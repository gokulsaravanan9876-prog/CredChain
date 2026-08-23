# ---------------------------------------------------------------------------
# Credential requests + student-controlled selective sharing.
#
# The authorization boundary this feeds is app/services/authorization_service.py
# (Phase 5) — that file is UNCHANGED by this phase. Once approve_request()
# below creates a real ShareGrant + ShareGrantCredential rows, Phase 5's
# is_verifier_authorized() (which already queries exactly those tables)
# starts returning True for real, with zero code changes on that side. This
# is the payoff of keeping that boundary clean in Phase 5.
# ---------------------------------------------------------------------------

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.activity_log import ActivityLog
from ..models.company import Company
from ..models.credential import Credential
from ..models.credential_request import CredentialRequest
from ..models.enums import CredentialRequestStatus, SharePermission
from ..models.share_grant import ShareGrant, ShareGrantCredential
from ..models.student import Student
from ..schemas.sharing import ALLOWED_EXPIRY_DAYS, CredentialRequestResponse, ShareCredentialPreview, ShareGrantResponse
from ..security.tokens import generate_raw_token, hash_token


class StudentNotFoundError(Exception):
    pass


class RequestNotFoundError(Exception):
    pass


class RequestNotOwnedError(Exception):
    pass


class RequestAlreadyProcessedError(Exception):
    pass


class InvalidExpiryError(Exception):
    pass


class CredentialSelectionError(Exception):
    pass


class CompanyNotFoundError(Exception):
    pass


class ShareNotFoundError(Exception):
    pass


class ShareNotOwnedError(Exception):
    pass


class ShareAlreadyRevokedError(Exception):
    pass


class InvalidShareTokenError(Exception):
    pass


class ShareRevokedError(Exception):
    pass


class ShareExpiredError(Exception):
    pass


# ---- credential requests ---------------------------------------------------


def create_credential_request(
    db: Session,
    company: Company,
    *,
    student_id: uuid.UUID | None,
    student_identifier: str | None,
    purpose: str,
    requested_credentials: list[str],
) -> CredentialRequest:
    """
    Creating a request never grants access — it only records "company is
    asking". No ShareGrant is created here.

    Resolves the student by whichever reference was given — internal UUID
    (the original, legacy path) or the human-readable student_identifier a
    company would actually be given by a candidate. Exactly one is present
    by the time this is called (enforced by CreateCredentialRequestBody).
    """
    student = db.get(Student, student_id) if student_id else None
    if student is None and student_identifier:
        normalized = student_identifier.strip()
        student = (
            db.query(Student)
            .filter(func.lower(Student.student_identifier) == normalized.lower())
            .first()
        )
    if student is None:
        raise StudentNotFoundError()

    request = CredentialRequest(
        company_id=company.id,
        student_id=student.id,
        purpose=purpose,
        status=CredentialRequestStatus.PENDING,
        requested_credentials=requested_credentials,
    )
    db.add(request)
    db.flush()

    db.add(
        ActivityLog(
            actor_user_id=company.user_id,
            action="CREDENTIAL_REQUEST_CREATED",
            entity_type="credential_request",
            entity_id=request.id,
            metadata_={"student_id": str(student.id), "purpose": purpose},
        )
    )
    db.commit()
    db.refresh(request)
    return request


def list_requests_for_company(db: Session, company: Company) -> list[CredentialRequest]:
    return (
        db.query(CredentialRequest)
        .filter(CredentialRequest.company_id == company.id)
        .order_by(CredentialRequest.created_at.desc())
        .all()
    )


def list_requests_for_student(db: Session, student: Student) -> list[CredentialRequest]:
    return (
        db.query(CredentialRequest)
        .filter(CredentialRequest.student_id == student.id)
        .order_by(CredentialRequest.created_at.desc())
        .all()
    )


def _get_owned_pending_request(db: Session, student: Student, request_id: uuid.UUID) -> CredentialRequest:
    request = db.get(CredentialRequest, request_id)
    if request is None:
        raise RequestNotFoundError()
    if request.student_id != student.id:
        raise RequestNotOwnedError()
    if request.status != CredentialRequestStatus.PENDING:
        raise RequestAlreadyProcessedError()
    return request


def decline_request(db: Session, student: Student, request_id: uuid.UUID) -> CredentialRequest:
    request = _get_owned_pending_request(db, student, request_id)
    request.status = CredentialRequestStatus.DECLINED
    request.responded_at = datetime.now(timezone.utc)
    db.add(request)

    db.add(
        ActivityLog(
            actor_user_id=student.user_id,
            action="CREDENTIAL_REQUEST_DECLINED",
            entity_type="credential_request",
            entity_id=request.id,
            metadata_={"company_id": str(request.company_id)},
        )
    )
    db.commit()
    db.refresh(request)
    return request


def _resolve_and_validate_credentials(db: Session, student: Student, credential_ids: list[uuid.UUID]) -> list[Credential]:
    unique_ids = set(credential_ids)
    credentials = db.query(Credential).filter(Credential.id.in_(unique_ids)).all()
    if len(credentials) != len(unique_ids):
        raise CredentialSelectionError("One or more selected credentials do not exist")
    for credential in credentials:
        # Never trust that a credential_id belongs to this student just
        # because the frontend sent it — verify every one.
        if credential.student_id != student.id:
            raise CredentialSelectionError("One or more selected credentials do not belong to you")
    return credentials


def _create_share_grant(
    db: Session,
    student: Student,
    *,
    company_id: uuid.UUID,
    credentials: list[Credential],
    expires_in_days: int,
    permission: SharePermission,
    credential_request_id: uuid.UUID | None,
) -> tuple[ShareGrant, str]:
    """
    The ONE place a ShareGrant + ShareGrantCredential rows + secure token are
    ever created — used by both approve_request (credential_request_id set)
    and create_direct_share (credential_request_id null). Returns (grant,
    raw_token); the raw token is NOT persisted anywhere, the caller (the
    route) must hand it to the client and then let it go.
    """
    raw_token = generate_raw_token()
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    grant = ShareGrant(
        student_id=student.id,
        company_id=company_id,
        credential_request_id=credential_request_id,
        share_token_hash=token_hash,
        expires_at=expires_at,
        permission=permission,
    )
    db.add(grant)
    db.flush()

    for credential in credentials:
        db.add(ShareGrantCredential(share_grant_id=grant.id, credential_id=credential.id))

    db.add(
        ActivityLog(
            actor_user_id=student.user_id,
            action="CREDENTIAL_SHARED",
            entity_type="share_grant",
            entity_id=grant.id,
            metadata_={"company_id": str(company_id), "credential_count": len(credentials)},
        )
    )
    return grant, raw_token


def approve_request(
    db: Session,
    student: Student,
    request_id: uuid.UUID,
    *,
    credential_ids: list[uuid.UUID],
    expires_in_days: int,
    permission: SharePermission = SharePermission.VIEW_ONLY,
) -> tuple[ShareGrant, str]:
    """
    Creates the ShareGrant + ShareGrantCredential rows AND the secure token
    in one transaction. Only the credential_ids explicitly passed in are
    included — a credential the company originally asked for but the
    student didn't select here never becomes part of the grant, regardless
    of what request.requested_credentials says (that field is just the
    company's original ask; _create_share_grant is the only place a
    ShareGrant is actually created, and it only ever grants what's in
    credential_ids).
    """
    if expires_in_days not in ALLOWED_EXPIRY_DAYS:
        raise InvalidExpiryError(f"expires_in_days must be one of {ALLOWED_EXPIRY_DAYS}")
    if not credential_ids:
        raise CredentialSelectionError("Select at least one credential to share")

    request = _get_owned_pending_request(db, student, request_id)
    credentials = _resolve_and_validate_credentials(db, student, credential_ids)

    grant, raw_token = _create_share_grant(
        db,
        student,
        company_id=request.company_id,
        credentials=credentials,
        expires_in_days=expires_in_days,
        permission=permission,
        credential_request_id=request.id,
    )

    request.status = CredentialRequestStatus.APPROVED
    request.responded_at = datetime.now(timezone.utc)
    db.add(request)

    db.add(
        ActivityLog(
            actor_user_id=student.user_id,
            action="CREDENTIAL_REQUEST_APPROVED",
            entity_type="credential_request",
            entity_id=request.id,
            metadata_={"company_id": str(request.company_id), "credential_count": len(credentials)},
        )
    )

    db.commit()
    db.refresh(grant)
    return grant, raw_token


def create_direct_share(
    db: Session,
    student: Student,
    *,
    company_id: uuid.UUID,
    credential_ids: list[uuid.UUID],
    expires_in_days: int,
    permission: SharePermission = SharePermission.VIEW_ONLY,
) -> tuple[ShareGrant, str]:
    """
    Student-initiated share directly to a real company — no prior
    CredentialRequest exists. Reuses the exact same ShareGrant creation path
    as approve_request; credential_request_id is simply null, which the
    schema already supports (see ShareGrant's docstring). The company must
    be a real, existing Company row — this is not a free-text recipient.
    """
    if expires_in_days not in ALLOWED_EXPIRY_DAYS:
        raise InvalidExpiryError(f"expires_in_days must be one of {ALLOWED_EXPIRY_DAYS}")
    if not credential_ids:
        raise CredentialSelectionError("Select at least one credential to share")

    company = db.get(Company, company_id)
    if company is None:
        raise CompanyNotFoundError()

    credentials = _resolve_and_validate_credentials(db, student, credential_ids)

    grant, raw_token = _create_share_grant(
        db,
        student,
        company_id=company.id,
        credentials=credentials,
        expires_in_days=expires_in_days,
        permission=permission,
        credential_request_id=None,
    )

    db.commit()
    db.refresh(grant)
    return grant, raw_token


# ---- shares -----------------------------------------------------------------


def list_shares_for_student(db: Session, student: Student) -> list[ShareGrant]:
    return db.query(ShareGrant).filter(ShareGrant.student_id == student.id).order_by(ShareGrant.created_at.desc()).all()


def list_shares_for_company(db: Session, company: Company) -> list[ShareGrant]:
    return db.query(ShareGrant).filter(ShareGrant.company_id == company.id).order_by(ShareGrant.created_at.desc()).all()


def revoke_share(db: Session, student: Student, share_id: uuid.UUID) -> ShareGrant:
    grant = db.get(ShareGrant, share_id)
    if grant is None:
        raise ShareNotFoundError()
    if grant.student_id != student.id:
        raise ShareNotOwnedError()
    if grant.revoked_at is not None:
        raise ShareAlreadyRevokedError()

    grant.revoked_at = datetime.now(timezone.utc)
    db.add(grant)

    db.add(
        ActivityLog(
            actor_user_id=student.user_id,
            action="SHARE_REVOKED",
            entity_type="share_grant",
            entity_id=grant.id,
            metadata_={"company_id": str(grant.company_id)},
        )
    )
    db.commit()
    db.refresh(grant)
    return grant


def access_share_by_token(db: Session, raw_token: str) -> ShareGrant:
    """
    Looks up a ShareGrant by the SHA-256 hash of the supplied raw token —
    never by storing or comparing the raw token itself. Raises a distinct
    typed error for "no such token" vs. "revoked" vs. "expired" so the route
    can return the right status code (401 vs. 410) without ever echoing the
    token or hash back.
    """
    token_hash = hash_token(raw_token)
    grant = db.query(ShareGrant).filter(ShareGrant.share_token_hash == token_hash).first()
    if grant is None:
        raise InvalidShareTokenError()
    if grant.revoked_at is not None:
        raise ShareRevokedError()
    if grant.expires_at <= datetime.now(timezone.utc):
        raise ShareExpiredError()

    db.add(
        ActivityLog(
            actor_user_id=None,  # accessed via link/QR, not an authenticated session — no actor to attribute this to
            action="SHARE_ACCESSED",
            entity_type="share_grant",
            entity_id=grant.id,
            metadata_={"company_id": str(grant.company_id)},
        )
    )
    db.commit()
    return grant


# ---- response builders --------------------------------------------------------


def to_credential_request_response(db: Session, request: CredentialRequest) -> CredentialRequestResponse:
    # The ShareGrant (if any) created when this specific request was
    # approved — see approve_request, which sets credential_request_id.
    grant = db.query(ShareGrant).filter(ShareGrant.credential_request_id == request.id).first()
    shared = [_credential_preview(link.credential) for link in grant.credential_links] if grant else []

    return CredentialRequestResponse(
        id=request.id,
        company_id=request.company_id,
        company_name=request.company.name,
        student_id=request.student_id,
        student_name=request.student.user.full_name,
        purpose=request.purpose,
        requested_credentials=request.requested_credentials,
        status=request.status,
        created_at=request.created_at,
        updated_at=request.updated_at,
        responded_at=request.responded_at,
        shared_credentials=shared,
    )


def _share_status(grant: ShareGrant) -> str:
    if grant.revoked_at is not None:
        return "revoked"
    if grant.expires_at <= datetime.now(timezone.utc):
        return "expired"
    return "active"


def _credential_preview(credential: Credential) -> ShareCredentialPreview:
    return ShareCredentialPreview(
        id=credential.id,
        credential_type=credential.credential_type,
        title=credential.title,
        degree=credential.degree,
        graduation_year=credential.graduation_year,
        cgpa=float(credential.cgpa) if credential.cgpa is not None else None,
        institution_name=credential.institution.name,
    )


def to_share_grant_response(grant: ShareGrant) -> ShareGrantResponse:
    return ShareGrantResponse(
        id=grant.id,
        company_id=grant.company_id,
        company_name=grant.company.name,
        credentials=[_credential_preview(link.credential) for link in grant.credential_links],
        permission=grant.permission.value,
        created_at=grant.created_at,
        expires_at=grant.expires_at,
        revoked_at=grant.revoked_at,
        status=_share_status(grant),
    )

# ---------------------------------------------------------------------------
# Phase 8B: read-only activity feeds built purely on top of the existing
# ActivityLog table (see app/models/activity_log.py) and the existing writes
# to it in credential_service, sharing_service, verification_service, and
# ai routes. Nothing here writes to ActivityLog or changes any of those
# write paths — this module only queries and renders.
#
# ActivityLog.actor_user_id identifies who performed an action, but most
# events matter to *someone else* too (a student cares that an institution
# issued them a credential, even though the institution is the actor). So
# "this role's activity" is resolved via entity ownership, not just actor
# identity: for each entity_type an event can reference, we first collect
# the ids of that role's own rows (their credentials / requests / grants),
# then match ActivityLog rows either by being the actor or by pointing at
# one of those owned entities.
# ---------------------------------------------------------------------------

import uuid

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..models.activity_log import ActivityLog
from ..models.company import Company
from ..models.credential import Credential
from ..models.credential_request import CredentialRequest
from ..models.institution import Institution
from ..models.share_grant import ShareGrant
from ..models.student import Student

DEFAULT_LIMIT = 50
MAX_LIMIT = 50


def _clamp_limit(limit: int) -> int:
    return max(1, min(limit, MAX_LIMIT))


def get_student_activity(db: Session, student: Student, limit: int = DEFAULT_LIMIT) -> list[ActivityLog]:
    credential_ids = [row[0] for row in db.query(Credential.id).filter(Credential.student_id == student.id).all()]
    request_ids = [row[0] for row in db.query(CredentialRequest.id).filter(CredentialRequest.student_id == student.id).all()]
    grant_ids = [row[0] for row in db.query(ShareGrant.id).filter(ShareGrant.student_id == student.id).all()]

    condition = or_(
        ActivityLog.actor_user_id == student.user_id,
        and_(ActivityLog.entity_type == "credential", ActivityLog.entity_id.in_(credential_ids)) if credential_ids else False,
        and_(ActivityLog.entity_type == "credential_request", ActivityLog.entity_id.in_(request_ids)) if request_ids else False,
        and_(ActivityLog.entity_type == "share_grant", ActivityLog.entity_id.in_(grant_ids)) if grant_ids else False,
    )
    return (
        db.query(ActivityLog)
        .filter(condition)
        .order_by(ActivityLog.created_at.desc())
        .limit(_clamp_limit(limit))
        .all()
    )


def get_institution_activity(db: Session, institution: Institution, limit: int = DEFAULT_LIMIT) -> list[ActivityLog]:
    credential_ids = [row[0] for row in db.query(Credential.id).filter(Credential.institution_id == institution.id).all()]

    condition = or_(
        ActivityLog.actor_user_id == institution.user_id,
        and_(ActivityLog.entity_type == "credential", ActivityLog.entity_id.in_(credential_ids)) if credential_ids else False,
    )
    return (
        db.query(ActivityLog)
        .filter(condition)
        .order_by(ActivityLog.created_at.desc())
        .limit(_clamp_limit(limit))
        .all()
    )


def get_company_activity(db: Session, company: Company, limit: int = DEFAULT_LIMIT) -> list[ActivityLog]:
    request_ids = [row[0] for row in db.query(CredentialRequest.id).filter(CredentialRequest.company_id == company.id).all()]
    grant_ids = [row[0] for row in db.query(ShareGrant.id).filter(ShareGrant.company_id == company.id).all()]

    condition = or_(
        ActivityLog.actor_user_id == company.user_id,
        and_(ActivityLog.entity_type == "credential_request", ActivityLog.entity_id.in_(request_ids)) if request_ids else False,
        and_(ActivityLog.entity_type == "share_grant", ActivityLog.entity_id.in_(grant_ids)) if grant_ids else False,
    )
    return (
        db.query(ActivityLog)
        .filter(condition)
        .order_by(ActivityLog.created_at.desc())
        .limit(_clamp_limit(limit))
        .all()
    )


# --- human-readable message rendering ---------------------------------------

_GENERIC_MESSAGES = {
    "CREDENTIAL_ISSUED": "A credential was issued",
    "CREDENTIAL_REVOKED": "A credential was revoked",
    "CREDENTIAL_VERIFIED": "A credential was verified",
    "CREDENTIAL_REQUEST_CREATED": "A credential request was made",
    "CREDENTIAL_REQUEST_APPROVED": "A credential request was approved",
    "CREDENTIAL_REQUEST_DECLINED": "A credential request was declined",
    "CREDENTIAL_SHARED": "Credentials were shared",
    "SHARE_REVOKED": "Share link revoked",
    "SHARE_ACCESSED": "A shared link was accessed",
    "AI_DOCUMENT_ANALYSIS": "AI document analysis completed",
    "AI_COMPANY_ANALYSIS": "AI company analysis completed",
    "AI_JOB_ANALYSIS": "AI job analysis completed",
    "AI_JOB_MATCH": "AI job match analysis completed",
}


def _credential_for(db: Session, entity_id: uuid.UUID | None) -> Credential | None:
    if entity_id is None:
        return None
    return db.get(Credential, entity_id)


def _request_for(db: Session, entity_id: uuid.UUID | None) -> CredentialRequest | None:
    if entity_id is None:
        return None
    return db.get(CredentialRequest, entity_id)


def _grant_for(db: Session, entity_id: uuid.UUID | None) -> ShareGrant | None:
    if entity_id is None:
        return None
    return db.get(ShareGrant, entity_id)


def render_message(db: Session, log: ActivityLog, *, viewer_role: str) -> str:
    """
    Builds a clean, human-readable message for one ActivityLog row from
    real data already reachable from the row (its resolved entity, or the
    actor's own profile name) — never from fabricated details. Falls back
    to a safe generic message if the referenced entity can no longer be
    resolved (e.g. it was later deleted) or the action isn't recognized.
    """
    action = log.action
    meta = log.metadata_ or {}

    try:
        if action == "CREDENTIAL_ISSUED":
            credential = _credential_for(db, log.entity_id)
            if credential is None:
                return _GENERIC_MESSAGES[action]
            student_name = credential.student.user.full_name
            if viewer_role == "student":
                return f"{credential.institution.name} issued you a credential: {credential.title}"
            return f"Credential issued to {student_name}"

        if action == "CREDENTIAL_REVOKED":
            credential = _credential_for(db, log.entity_id)
            if credential is None:
                return _GENERIC_MESSAGES[action]
            if viewer_role == "student":
                return f"{credential.institution.name} revoked your credential: {credential.title}"
            return f"Revoked credential: {credential.title}"

        if action == "CREDENTIAL_VERIFIED":
            credential = _credential_for(db, log.entity_id)
            company_name = log.actor_user.company.name if log.actor_user and log.actor_user.company else "A company"
            if credential is None:
                return f"{company_name} attempted to verify a credential"
            if viewer_role == "student":
                return f"{company_name} verified your credential: {credential.title}"
            if viewer_role == "institution":
                return f"{company_name} verified a credential you issued: {credential.title}"
            return f"You verified {credential.title} ({credential.student.user.full_name})"

        if action == "CREDENTIAL_REQUEST_CREATED":
            request = _request_for(db, log.entity_id)
            if request is None:
                return _GENERIC_MESSAGES[action]
            if viewer_role == "student":
                return f"{request.company.name} requested your credentials"
            return f"You requested credentials from {request.student.user.full_name}"

        if action == "CREDENTIAL_REQUEST_APPROVED":
            request = _request_for(db, log.entity_id)
            if request is None:
                return _GENERIC_MESSAGES[action]
            if viewer_role == "student":
                return f"You approved {request.company.name}'s credential request"
            return f"{request.student.user.full_name} approved your credential request"

        if action == "CREDENTIAL_REQUEST_DECLINED":
            request = _request_for(db, log.entity_id)
            if request is None:
                return _GENERIC_MESSAGES[action]
            if viewer_role == "student":
                return f"You declined {request.company.name}'s credential request"
            return f"{request.student.user.full_name} declined your credential request"

        if action == "CREDENTIAL_SHARED":
            grant = _grant_for(db, log.entity_id)
            if grant is None:
                return _GENERIC_MESSAGES[action]
            credentials = grant.credentials
            label = credentials[0].title if len(credentials) == 1 else f"{len(credentials)} credentials"
            if viewer_role == "student":
                return f"You shared {label} with {grant.company.name}"
            return f"{grant.student.user.full_name} shared {label} with you"

        if action == "SHARE_REVOKED":
            grant = _grant_for(db, log.entity_id)
            if grant is None:
                return _GENERIC_MESSAGES[action]
            if viewer_role == "student":
                return f"You revoked {grant.company.name}'s access to your credentials"
            return f"{grant.student.user.full_name} revoked your access to their credentials"

        if action == "SHARE_ACCESSED":
            grant = _grant_for(db, log.entity_id)
            if grant is None:
                return _GENERIC_MESSAGES[action]
            if viewer_role == "student":
                return f"{grant.company.name} accessed your shared credentials"
            return f"Your shared link for {grant.student.user.full_name} was accessed"

        if action.startswith("AI_"):
            job_title = meta.get("job_title")
            base = _GENERIC_MESSAGES.get(action, "AI analysis completed")
            return f"{base} for \"{job_title}\"" if job_title else base

        return _GENERIC_MESSAGES.get(action, "Activity recorded")
    except Exception:
        # A resolvable-looking entity that turned out to be in an
        # unexpected state should never break the whole feed — fall back
        # to a safe generic label for this one row instead.
        return _GENERIC_MESSAGES.get(action, "Activity recorded")

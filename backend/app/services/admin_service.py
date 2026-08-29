# ---------------------------------------------------------------------------
# Phase A: minimal admin business logic — institution/company verification
# review only. Deliberately narrow (see the Phase A spec): no user deletion,
# no database administration, no impersonation, nothing beyond
# approve/reject a REGISTERED institution/company account.
#
# Reuses the existing ActivityLog table for the audit trail (no second audit
# system) — see _log below.
# ---------------------------------------------------------------------------

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models.activity_log import ActivityLog
from ..models.company import Company
from ..models.enums import VerificationStatus
from ..models.institution import Institution
from ..models.user import User
from ..schemas.admin import PendingCompanyResponse, PendingInstitutionResponse


class InstitutionNotFoundError(Exception):
    pass


class CompanyNotFoundError(Exception):
    pass


class NotARegisteredAccountError(Exception):
    """Raised if an admin action targets a directory-only row (user_id IS NULL) — there is no account to verify."""


class AlreadyDecidedError(Exception):
    """Raised on approve/reject of an institution/company whose verification_status is not currently PENDING — prevents re-deciding an already-verified or already-rejected account."""


def _log(db: Session, *, actor: User, action: str, entity_type: str, entity_id: uuid.UUID, metadata: dict | None = None) -> None:
    db.add(ActivityLog(actor_user_id=actor.id, action=action, entity_type=entity_type, entity_id=entity_id, metadata_=metadata))


# --- Institutions -----------------------------------------------------------


def list_pending_institutions(db: Session) -> list[Institution]:
    return (
        db.query(Institution)
        .filter(Institution.user_id.isnot(None), Institution.verification_status == VerificationStatus.PENDING)
        .order_by(Institution.created_at)
        .all()
    )


def _get_registered_institution(db: Session, institution_id: uuid.UUID) -> Institution:
    institution = db.get(Institution, institution_id)
    if institution is None:
        raise InstitutionNotFoundError()
    if institution.user_id is None:
        raise NotARegisteredAccountError()
    return institution


def approve_institution(db: Session, admin: User, institution_id: uuid.UUID) -> Institution:
    institution = _get_registered_institution(db, institution_id)
    if institution.verification_status != VerificationStatus.PENDING:
        raise AlreadyDecidedError()
    institution.verification_status = VerificationStatus.VERIFIED
    institution.verified_at = datetime.now(timezone.utc)
    institution.verified_by = admin.id
    institution.rejection_reason = None
    db.add(institution)
    _log(db, actor=admin, action="ADMIN_APPROVED_INSTITUTION", entity_type="institution", entity_id=institution.id)
    db.commit()
    db.refresh(institution)
    return institution


def reject_institution(db: Session, admin: User, institution_id: uuid.UUID, reason: str) -> Institution:
    institution = _get_registered_institution(db, institution_id)
    if institution.verification_status != VerificationStatus.PENDING:
        raise AlreadyDecidedError()
    institution.verification_status = VerificationStatus.REJECTED
    institution.verified_at = datetime.now(timezone.utc)
    institution.verified_by = admin.id
    institution.rejection_reason = reason
    db.add(institution)
    _log(db, actor=admin, action="ADMIN_REJECTED_INSTITUTION", entity_type="institution", entity_id=institution.id, metadata={"reason": reason})
    db.commit()
    db.refresh(institution)
    return institution


def to_pending_institution_response(institution: Institution) -> PendingInstitutionResponse:
    user = institution.user
    return PendingInstitutionResponse(
        id=institution.id,
        name=institution.name,
        location=institution.location,
        website=institution.website,
        registration_number=institution.registration_number,
        verification_status=institution.verification_status.value,
        created_at=institution.created_at,
        contact_email=user.email if user else None,
        contact_full_name=user.full_name if user else None,
    )


# --- Companies ---------------------------------------------------------------


def list_pending_companies(db: Session) -> list[Company]:
    return (
        db.query(Company)
        .filter(Company.user_id.isnot(None), Company.verification_status == VerificationStatus.PENDING)
        .order_by(Company.created_at)
        .all()
    )


def _get_registered_company(db: Session, company_id: uuid.UUID) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise CompanyNotFoundError()
    if company.user_id is None:
        raise NotARegisteredAccountError()
    return company


def approve_company(db: Session, admin: User, company_id: uuid.UUID) -> Company:
    company = _get_registered_company(db, company_id)
    if company.verification_status != VerificationStatus.PENDING:
        raise AlreadyDecidedError()
    company.verification_status = VerificationStatus.VERIFIED
    company.verified_at = datetime.now(timezone.utc)
    company.verified_by = admin.id
    company.rejection_reason = None
    db.add(company)
    _log(db, actor=admin, action="ADMIN_APPROVED_COMPANY", entity_type="company", entity_id=company.id)
    db.commit()
    db.refresh(company)
    return company


def reject_company(db: Session, admin: User, company_id: uuid.UUID, reason: str) -> Company:
    company = _get_registered_company(db, company_id)
    if company.verification_status != VerificationStatus.PENDING:
        raise AlreadyDecidedError()
    company.verification_status = VerificationStatus.REJECTED
    company.verified_at = datetime.now(timezone.utc)
    company.verified_by = admin.id
    company.rejection_reason = reason
    db.add(company)
    _log(db, actor=admin, action="ADMIN_REJECTED_COMPANY", entity_type="company", entity_id=company.id, metadata={"reason": reason})
    db.commit()
    db.refresh(company)
    return company


def to_pending_company_response(company: Company) -> PendingCompanyResponse:
    user = company.user
    return PendingCompanyResponse(
        id=company.id,
        name=company.name,
        location=company.location,
        website=company.website,
        industry=company.industry,
        verification_status=company.verification_status.value,
        created_at=company.created_at,
        contact_email=user.email if user else None,
        contact_full_name=user.full_name if user else None,
    )

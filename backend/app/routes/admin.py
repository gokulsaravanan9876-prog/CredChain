# ---------------------------------------------------------------------------
# Phase A: minimal admin API — institution/company verification review only.
# Every endpoint requires require_admin (backend-enforced; see
# security/permissions.py) — a student/institution/verifier token gets a
# real 403 here regardless of anything the frontend does or doesn't render.
# ---------------------------------------------------------------------------

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.admin import PendingCompanyResponse, PendingInstitutionResponse, RejectVerificationBody
from ..security.permissions import require_admin
from ..services import admin_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get(
    "/institutions/pending",
    response_model=list[PendingInstitutionResponse],
    summary="List registered institution accounts awaiting verification",
)
def list_pending_institutions(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> list[PendingInstitutionResponse]:
    institutions = admin_service.list_pending_institutions(db)
    return [admin_service.to_pending_institution_response(i) for i in institutions]


@router.post(
    "/institutions/{institution_id}/approve",
    response_model=PendingInstitutionResponse,
    summary="Approve a registered institution — it can now issue credentials",
)
def approve_institution(
    institution_id: uuid.UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> PendingInstitutionResponse:
    try:
        institution = admin_service.approve_institution(db, current_user, institution_id)
    except admin_service.InstitutionNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    except admin_service.NotARegisteredAccountError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This is a directory listing, not a registered account")
    except admin_service.AlreadyDecidedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This institution's verification has already been decided")
    return admin_service.to_pending_institution_response(institution)


@router.post(
    "/institutions/{institution_id}/reject",
    response_model=PendingInstitutionResponse,
    summary="Reject a registered institution — it cannot issue credentials",
)
def reject_institution(
    institution_id: uuid.UUID,
    payload: RejectVerificationBody,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PendingInstitutionResponse:
    try:
        institution = admin_service.reject_institution(db, current_user, institution_id, payload.reason)
    except admin_service.InstitutionNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    except admin_service.NotARegisteredAccountError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This is a directory listing, not a registered account")
    except admin_service.AlreadyDecidedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This institution's verification has already been decided")
    return admin_service.to_pending_institution_response(institution)


@router.get(
    "/companies/pending",
    response_model=list[PendingCompanyResponse],
    summary="List registered company accounts awaiting verification",
)
def list_pending_companies(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> list[PendingCompanyResponse]:
    companies = admin_service.list_pending_companies(db)
    return [admin_service.to_pending_company_response(c) for c in companies]


@router.post(
    "/companies/{company_id}/approve",
    response_model=PendingCompanyResponse,
    summary="Approve a registered company — it can now publish jobs",
)
def approve_company(
    company_id: uuid.UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> PendingCompanyResponse:
    try:
        company = admin_service.approve_company(db, current_user, company_id)
    except admin_service.CompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    except admin_service.NotARegisteredAccountError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This is a directory listing, not a registered account")
    except admin_service.AlreadyDecidedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This company's verification has already been decided")
    return admin_service.to_pending_company_response(company)


@router.post(
    "/companies/{company_id}/reject",
    response_model=PendingCompanyResponse,
    summary="Reject a registered company — it cannot publish jobs",
)
def reject_company(
    company_id: uuid.UUID,
    payload: RejectVerificationBody,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PendingCompanyResponse:
    try:
        company = admin_service.reject_company(db, current_user, company_id, payload.reason)
    except admin_service.CompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    except admin_service.NotARegisteredAccountError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This is a directory listing, not a registered account")
    except admin_service.AlreadyDecidedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This company's verification has already been decided")
    return admin_service.to_pending_company_response(company)

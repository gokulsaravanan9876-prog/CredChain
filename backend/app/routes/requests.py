import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models.user import User
from ..schemas.sharing import (
    ApproveCredentialRequestBody,
    CreateCredentialRequestBody,
    CredentialRequestResponse,
    ShareCreatedResponse,
)
from ..security.permissions import require_student, require_verifier
from ..services import sharing_service

router = APIRouter(tags=["credential-requests"])


@router.post(
    "/api/credential-requests",
    response_model=CredentialRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Company asks a student for specific credentials — does NOT grant access",
)
def create_request(
    payload: CreateCredentialRequestBody,
    current_user: User = Depends(require_verifier),
    db: Session = Depends(get_db),
) -> CredentialRequestResponse:
    if current_user.company is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No company profile for this account")
    try:
        request = sharing_service.create_credential_request(
            db,
            current_user.company,
            student_id=payload.student_id,
            student_identifier=payload.student_identifier,
            purpose=payload.purpose,
            requested_credentials=payload.requested_credentials,
        )
    except sharing_service.StudentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return sharing_service.to_credential_request_response(db, request)


@router.get("/api/companies/me/requests", response_model=list[CredentialRequestResponse])
def list_company_requests(
    current_user: User = Depends(require_verifier), db: Session = Depends(get_db)
) -> list[CredentialRequestResponse]:
    if current_user.company is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No company profile for this account")
    requests = sharing_service.list_requests_for_company(db, current_user.company)
    return [sharing_service.to_credential_request_response(db, r) for r in requests]


@router.get("/api/students/me/requests", response_model=list[CredentialRequestResponse])
def list_student_requests(
    current_user: User = Depends(require_student), db: Session = Depends(get_db)
) -> list[CredentialRequestResponse]:
    if current_user.student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No student profile for this account")
    requests = sharing_service.list_requests_for_student(db, current_user.student)
    return [sharing_service.to_credential_request_response(db, r) for r in requests]


@router.post("/api/credential-requests/{request_id}/decline", response_model=CredentialRequestResponse)
def decline_request(
    request_id: uuid.UUID, current_user: User = Depends(require_student), db: Session = Depends(get_db)
) -> CredentialRequestResponse:
    if current_user.student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No student profile for this account")
    try:
        request = sharing_service.decline_request(db, current_user.student, request_id)
    except sharing_service.RequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except sharing_service.RequestNotOwnedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This request does not belong to you")
    except sharing_service.RequestAlreadyProcessedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This request has already been processed")
    return sharing_service.to_credential_request_response(db, request)


@router.post(
    "/api/credential-requests/{request_id}/approve",
    response_model=ShareCreatedResponse,
    summary="Student approves a request, selecting exactly which credentials to share — creates the ShareGrant and a one-time-visible secure share token",
)
def approve_request(
    request_id: uuid.UUID,
    payload: ApproveCredentialRequestBody,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> ShareCreatedResponse:
    if current_user.student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No student profile for this account")
    try:
        grant, raw_token = sharing_service.approve_request(
            db,
            current_user.student,
            request_id,
            credential_ids=payload.credential_ids,
            expires_in_days=payload.expires_in_days,
            permission=payload.permission,
        )
    except sharing_service.RequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except sharing_service.RequestNotOwnedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This request does not belong to you")
    except sharing_service.RequestAlreadyProcessedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This request has already been processed")
    except sharing_service.InvalidExpiryError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except sharing_service.CredentialSelectionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    share_response = sharing_service.to_share_grant_response(grant)
    share_url = f"{settings.frontend_base_url}/share/verify/{raw_token}"
    return ShareCreatedResponse(share=share_response, share_token=raw_token, share_url=share_url)

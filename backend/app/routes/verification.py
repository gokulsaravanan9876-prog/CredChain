import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.credential import Credential
from ..models.user import User
from ..schemas.verification import VerifyRequest, VerifyResponse
from ..security.permissions import require_verifier
from ..services import authorization_service, verification_service

router = APIRouter(prefix="/api/verification", tags=["verification"])


def _get_credential_or_404(db: Session, credential_id: uuid.UUID) -> Credential:
    credential = db.get(Credential, credential_id)
    if credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
    return credential


@router.post(
    "/verify",
    response_model=VerifyResponse,
    summary="Verify a credential's authenticity — signature, document integrity, status, and access are all computed server-side, never trusted from the request",
)
def verify(
    payload: VerifyRequest,
    current_user: User = Depends(require_verifier),
    db: Session = Depends(get_db),
) -> VerifyResponse:
    if current_user.company is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No company profile for this account")

    result = verification_service.verify_credential(
        db,
        current_user.company,
        payload.credential_id,
        demo_cgpa_override=payload.demo_cgpa_override,
    )
    return VerifyResponse(**result)


@router.get(
    "/credentials/{credential_id}/view",
    summary="Inline view of a shared credential's document — any active (non-revoked, non-expired) share grant, regardless of permission level",
)
def view_shared_document(
    credential_id: uuid.UUID,
    current_user: User = Depends(require_verifier),
    db: Session = Depends(get_db),
) -> FileResponse:
    if current_user.company is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No company profile for this account")

    credential = _get_credential_or_404(db, credential_id)
    grant = authorization_service.get_active_share_grant(db, current_user.company, credential)
    if grant is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This credential has not been shared with you")
    if credential.document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No document on file for this credential")

    path = Path(credential.document.storage_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing on this server")
    # No filename passed -> Starlette emits no Content-Disposition header at all, so the browser renders it inline by default.
    return FileResponse(path, media_type=credential.document.mime_type)


@router.get(
    "/credentials/{credential_id}/download",
    summary="Attachment download of a shared credential's document — requires an active share grant WITH view_download permission, 403 otherwise",
)
def download_shared_document(
    credential_id: uuid.UUID,
    current_user: User = Depends(require_verifier),
    db: Session = Depends(get_db),
) -> FileResponse:
    if current_user.company is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No company profile for this account")

    credential = _get_credential_or_404(db, credential_id)
    if not authorization_service.is_verifier_authorized(db, current_user.company, credential):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This credential has not been shared with you")
    if not authorization_service.has_download_permission(db, current_user.company, credential):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This share only grants view access, not download")
    if credential.document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No document on file for this credential")

    path = Path(credential.document.storage_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing on this server")
    return FileResponse(
        path,
        media_type=credential.document.mime_type,
        filename=f"{credential.credential_identifier}.pdf",
    )

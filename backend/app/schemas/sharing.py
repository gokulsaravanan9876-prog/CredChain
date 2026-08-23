import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from ..models.enums import CredentialRequestStatus, CredentialType, SharePermission

# Whitelisted expiry choices — never accept an arbitrary caller-supplied
# date. Matches the existing frontend's expiry dropdown (1/7/30 days).
ALLOWED_EXPIRY_DAYS = (1, 7, 30)


class CreateCredentialRequestBody(BaseModel):
    # student_id (internal UUID) is kept for backward compatibility with any
    # existing caller; student_identifier (the human-readable id a company
    # would actually be given, e.g. "XYZ-2026-CS-014") is the field the
    # current frontend uses — a company has no legitimate way to know a
    # student's internal UUID. Exactly one must be provided.
    student_id: uuid.UUID | None = None
    student_identifier: str | None = None
    purpose: str = Field(min_length=1, max_length=255)
    requested_credentials: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def _exactly_one_student_reference(self) -> "CreateCredentialRequestBody":
        if not self.student_id and not self.student_identifier:
            raise ValueError("Either student_id or student_identifier is required")
        return self


class ShareCredentialPreview(BaseModel):
    id: uuid.UUID
    credential_type: CredentialType
    title: str
    degree: str | None
    graduation_year: int | None
    cgpa: float | None
    institution_name: str


class CredentialRequestResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    student_id: uuid.UUID
    student_name: str
    purpose: str
    requested_credentials: list[str]
    status: CredentialRequestStatus
    created_at: datetime
    updated_at: datetime
    responded_at: datetime | None
    # PS3 Phase F: what the student actually shared in response to this
    # request (via the ShareGrant this request's approval created), so the
    # company can see "requested X, received Y" before ever clicking
    # Verify. Empty until the student approves.
    shared_credentials: list[ShareCredentialPreview] = []

    model_config = {"from_attributes": True}


class ApproveCredentialRequestBody(BaseModel):
    credential_ids: list[uuid.UUID] = Field(min_length=1)
    expires_in_days: int
    # Defaults to VIEW_ONLY — preserves every existing caller's behavior.
    permission: SharePermission = SharePermission.VIEW_ONLY


class CreateDirectShareBody(BaseModel):
    """Student-initiated share directly to a real company, with no prior CredentialRequest. Same ShareGrant/token architecture as approving a request — credential_request_id is simply left null."""

    company_id: uuid.UUID
    credential_ids: list[uuid.UUID] = Field(min_length=1)
    expires_in_days: int
    permission: SharePermission = SharePermission.VIEW_ONLY


class ShareGrantResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    credentials: list[ShareCredentialPreview]
    permission: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    status: str  # active | expired | revoked — derived, not a stored column


class ShareCreatedResponse(BaseModel):
    share: ShareGrantResponse
    # The RAW token — present in this ONE response, at creation time only.
    # It is not recoverable afterward (only its hash is stored).
    share_token: str
    share_url: str


class ShareTokenAccessResponse(BaseModel):
    """What GET /api/shares/verify/{token} returns — a minimal preview, not a verification result. See routes/sharing.py."""

    company_name: str
    expires_at: datetime
    credentials: list[ShareCredentialPreview]
    permission: str

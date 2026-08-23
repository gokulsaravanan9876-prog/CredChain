import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from ..models.enums import CredentialType, StudentDocumentStatus


class RejectStudentDocumentBody(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class ApproveStudentDocumentBody(BaseModel):
    """
    Optional academic metadata the institution confirms while approving a
    student-uploaded document — e.g. the CGPA/degree/graduation year printed
    on the PDF the reviewer is looking at. A StudentDocument row has no
    structured fields of its own to copy from (it's just an uploaded file),
    so without this, every document-approval credential was permanently
    metadata-empty even when the institution reviewer could see the real
    values. All fields stay optional: a certification or other document type
    genuinely has nothing to enter here.
    """

    degree: str | None = Field(default=None, max_length=255)
    graduation_year: int | None = None
    cgpa: float | None = None


class StudentDocumentResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    student_identifier: str
    institution_id: uuid.UUID
    institution_name: str
    credential_type: CredentialType
    custom_credential_name: str | None
    original_filename: str
    status: StudentDocumentStatus
    rejection_reason: str | None
    resulting_credential_id: uuid.UUID | None
    created_at: datetime
    reviewed_at: datetime | None

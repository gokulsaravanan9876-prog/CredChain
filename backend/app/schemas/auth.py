# ---------------------------------------------------------------------------
# Pydantic request/response schemas for auth. Routes return these, never raw
# SQLAlchemy model instances — that's how password_hash etc. stay out of
# every API response by construction, not by remembering to exclude a field.
# ---------------------------------------------------------------------------

import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from ..models.enums import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole

    # Role-specific fields needed to create the matching profile row.
    # Exactly one group is required, depending on `role` — validated in
    # auth_service.register_user, not here, since it's cross-field logic.
    student_identifier: str | None = Field(default=None, max_length=100)
    # Optional at registration — a student can also link (or change) their
    # institution afterward via POST /api/students/me/institution. Either
    # way, the id is validated server-side against real institution rows
    # (see auth_service.register_user / student_service.link_student_to_institution);
    # never trusted as-is.
    institution_id: uuid.UUID | None = Field(default=None)

    institution_name: str | None = Field(default=None, max_length=255)
    institution_registration_number: str | None = Field(default=None, max_length=100)

    company_name: str | None = Field(default=None, max_length=255)
    company_industry: str | None = Field(default=None, max_length=255)
    company_website: str | None = Field(default=None, max_length=255)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        if not any(ch.isalpha() for ch in value) or not any(ch.isdigit() for ch in value):
            raise ValueError("Password must contain at least one letter and one number")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    role: UserRole
    is_active: bool

    # Populated depending on role so the frontend can address the
    # role-specific profile without a second request.
    student_id: uuid.UUID | None = None
    institution_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    # Institution/company display name — the existing Sidebar UI shows this
    # under the CredChain logo for those two roles.
    org_name: str | None = None
    # Populated only for students: the institution THEY are affiliated
    # with (distinct from institution_id above, which is only ever an
    # institution-role user's own institution). Both null when unlinked.
    student_institution_id: uuid.UUID | None = None
    student_institution_name: str | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

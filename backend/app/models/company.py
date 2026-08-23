from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .common import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .credential_request import CredentialRequest
    from .job import Job
    from .job_application import JobApplication
    from .share_grant import ShareGrant
    from .user import User
    from .verification_event import VerificationEvent


class Company(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The "verifier" role's profile — named Company to match the DB entity list; the frontend/API role value stays 'verifier'."""

    __tablename__ = "companies"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # PS3 job-marketplace phase: real company profile fields, all optional —
    # a company that hasn't filled these in yet is still a real company row,
    # never replaced with fabricated placeholder text anywhere in the UI.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user: Mapped[User] = relationship(back_populates="company")
    credential_requests: Mapped[list[CredentialRequest]] = relationship(back_populates="company")
    share_grants: Mapped[list[ShareGrant]] = relationship(back_populates="company")
    verification_events: Mapped[list[VerificationEvent]] = relationship(back_populates="company")
    jobs: Mapped[list[Job]] = relationship(back_populates="company")
    job_applications: Mapped[list[JobApplication]] = relationship(back_populates="company")

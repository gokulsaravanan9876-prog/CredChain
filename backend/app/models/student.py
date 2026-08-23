from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .common import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .credential import Credential
    from .credential_request import CredentialRequest
    from .institution import Institution
    from .institution_certificate_request import InstitutionCertificateRequest
    from .share_grant import ShareGrant
    from .student_document import StudentDocument
    from .user import User


class Student(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "students"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    student_identifier: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    # A student can exist before being linked to an institution (e.g. self-registers),
    # and an institution could theoretically be deleted without deleting its alumni —
    # SET NULL rather than cascading a delete onto the student record.
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Self-reported by the student, used only by the deterministic job-
    # eligibility check (app/services/eligibility_service.py) as an
    # advisory (non-blocking) signal — never written to by AI, never a
    # hard gate on its own.
    skills: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped[User] = relationship(back_populates="student")
    institution: Mapped[Institution | None] = relationship(back_populates="students")
    credentials: Mapped[list[Credential]] = relationship(back_populates="student")
    credential_requests: Mapped[list[CredentialRequest]] = relationship(back_populates="student")
    share_grants: Mapped[list[ShareGrant]] = relationship(back_populates="student")
    institution_certificate_requests: Mapped[list[InstitutionCertificateRequest]] = relationship(back_populates="student")
    student_documents: Mapped[list[StudentDocument]] = relationship(back_populates="student")

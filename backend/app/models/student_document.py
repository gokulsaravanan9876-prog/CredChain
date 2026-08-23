from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .common import TimestampMixin, UUIDPrimaryKeyMixin
from .enums import CredentialType, StudentDocumentStatus

if TYPE_CHECKING:
    from .credential import Credential
    from .institution import Institution
    from .student import Student


class StudentDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A document a student already possesses and uploads for institution
    review — deliberately NOT a Credential row (a Credential requires an
    institution's real Ed25519 signature to exist at all; this table is
    what an unsigned, unverified claim looks like before that happens).
    Starts UNVERIFIED and can only become a real Credential through
    student_document_service.approve_document, which reuses the exact same
    signing pipeline as any other issuance — never a boolean flip.
    """

    __tablename__ = "student_documents"
    __table_args__ = (
        Index("ix_student_documents_student_status", "student_id", "status"),
        Index("ix_student_documents_institution_status", "institution_id", "status"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    credential_type: Mapped[CredentialType] = mapped_column(
        SAEnum(CredentialType, values_callable=lambda e: [m.value for m in e], name="credential_type"),
        nullable=False,
    )
    custom_credential_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    status: Mapped[StudentDocumentStatus] = mapped_column(
        SAEnum(StudentDocumentStatus, values_callable=lambda e: [m.value for m in e], name="student_document_status"),
        nullable=False,
        default=StudentDocumentStatus.UNVERIFIED,
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Set only on APPROVED — the real, signed credential this upload became.
    resulting_credential_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("credentials.id", ondelete="SET NULL"), nullable=True
    )

    student: Mapped[Student] = relationship(back_populates="student_documents")
    institution: Mapped[Institution] = relationship(back_populates="student_documents")
    resulting_credential: Mapped[Credential | None] = relationship()

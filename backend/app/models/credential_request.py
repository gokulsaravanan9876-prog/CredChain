from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .common import TimestampMixin, UUIDPrimaryKeyMixin
from .enums import CredentialRequestStatus

if TYPE_CHECKING:
    from .company import Company
    from .student import Student


class CredentialRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    requested_credentials is a JSON list of credential type/title labels
    (e.g. ["B.Tech Degree", "Final Transcript"]) rather than a FK to actual
    Credential rows: at request time the company is asking for a *kind* of
    credential, not naming a specific row it doesn't know exists. The
    specific credentials actually shared happen at approval time, via a
    ShareGrant.
    """

    __tablename__ = "credential_requests"
    __table_args__ = (Index("ix_credential_requests_student_status", "student_id", "status"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )

    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[CredentialRequestStatus] = mapped_column(
        SAEnum(
            CredentialRequestStatus,
            values_callable=lambda e: [m.value for m in e],
            name="credential_request_status",
        ),
        nullable=False,
        default=CredentialRequestStatus.PENDING,
        index=True,
    )
    requested_credentials: Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    company: Mapped[Company] = relationship(back_populates="credential_requests")
    student: Mapped[Student] = relationship(back_populates="credential_requests")

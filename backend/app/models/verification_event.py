from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .common import UUIDPrimaryKeyMixin
from .enums import VerificationResultStatus

if TYPE_CHECKING:
    from .company import Company
    from .credential import Credential


class VerificationEvent(UUIDPrimaryKeyMixin, Base):
    """
    A record of one verification check the backend performed, with each
    sub-check broken out individually so a UI can show which specific check
    failed (matches the checks[] pattern in the existing frontend). These
    booleans are written only by verification_service.py (Phase 5) — they
    are never accepted as input from a client request.
    """

    __tablename__ = "verification_events"
    __table_args__ = (Index("ix_verification_events_credential_company", "credential_id", "company_id"),)

    credential_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("credentials.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    result: Mapped[VerificationResultStatus] = mapped_column(
        SAEnum(
            VerificationResultStatus,
            values_callable=lambda e: [m.value for m in e],
            name="verification_result_status",
        ),
        nullable=False,
        index=True,
    )

    issuer_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    integrity_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    access_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)

    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    credential: Mapped[Credential] = relationship(back_populates="verification_events")
    company: Mapped[Company] = relationship(back_populates="verification_events")

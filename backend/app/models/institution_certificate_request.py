from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .common import TimestampMixin, UUIDPrimaryKeyMixin
from .enums import CredentialType, InstitutionRequestStatus

if TYPE_CHECKING:
    from .credential import Credential
    from .institution import Institution
    from .student import Student


class InstitutionCertificateRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Student -> institution certificate request — the reverse direction of
    CredentialRequest (which is company -> student and has a different
    shape: free-text label lists, no typed credential_type, no approval
    lifecycle). Kept as its own table rather than overloading that model,
    since conflating the two directions would corrupt both.

    Only ever created for institution_id == student.institution_id (the
    real, already-validated university<->student relationship) — enforced
    in institution_request_service.create_request, not here.
    """

    __tablename__ = "institution_certificate_requests"
    __table_args__ = (
        Index("ix_institution_certificate_requests_student_status", "student_id", "status"),
        Index("ix_institution_certificate_requests_institution_status", "institution_id", "status"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Groups multiple InstitutionCertificateRequest rows created together in
    # one student submission (e.g. Transcript + Degree + Migration in a
    # single "Request from Institution" action) so they can be displayed as
    # one request with several items — while each row keeps its own
    # independent PENDING/APPROVED/REJECTED/FULFILLED lifecycle, unchanged.
    # NULL for requests created before this existed, and that's fine: a
    # lone item with no batch_id just renders as a request with one item.
    batch_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    credential_type: Mapped[CredentialType] = mapped_column(
        SAEnum(CredentialType, values_callable=lambda e: [m.value for m in e], name="credential_type"),
        nullable=False,
    )
    # Only meaningful (and only shown by the frontend) when credential_type == OTHER.
    custom_credential_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[InstitutionRequestStatus] = mapped_column(
        SAEnum(InstitutionRequestStatus, values_callable=lambda e: [m.value for m in e], name="institution_request_status"),
        nullable=False,
        default=InstitutionRequestStatus.PENDING,
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Set only when an institution actually issues the credential that
    # fulfills this request — never on approval alone. SET NULL so a later
    # credential revocation/deletion (revocation never deletes, but this is
    # defensive) never breaks this row's integrity.
    fulfilled_credential_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("credentials.id", ondelete="SET NULL"), nullable=True
    )

    student: Mapped[Student] = relationship(back_populates="institution_certificate_requests")
    institution: Mapped[Institution] = relationship(back_populates="institution_certificate_requests")
    fulfilled_credential: Mapped[Credential | None] = relationship()

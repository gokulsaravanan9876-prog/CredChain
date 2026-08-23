from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .common import TimestampMixin, UUIDPrimaryKeyMixin
from .enums import BlockchainAnchorStatus, CredentialStatus, CredentialType

if TYPE_CHECKING:
    from .credential_document import CredentialDocument
    from .institution import Institution
    from .share_grant import ShareGrant, ShareGrantCredential
    from .student import Student
    from .verification_event import VerificationEvent


class Credential(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    document_hash and signature are populated by the issuance service
    (Phase 4) — SHA-256 of the uploaded document and the institution's
    cryptographic signature over the canonical credential payload,
    respectively. Both are nullable here because a credential can exist
    (e.g. mid-issuance) before those steps complete; the issuance service
    is responsible for only marking a credential fully issued once both
    are set.
    """

    __tablename__ = "credentials"
    __table_args__ = (Index("ix_credentials_student_status", "student_id", "status"),)

    # Short, unique, human-shareable identifier (distinct from the UUID PK) —
    # e.g. what you'd print on a certificate or put in a QR-adjacent label.
    credential_identifier: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    student_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    credential_type: Mapped[CredentialType] = mapped_column(
        SAEnum(CredentialType, values_callable=lambda e: [m.value for m in e], name="credential_type"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cgpa: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)

    status: Mapped[CredentialStatus] = mapped_column(
        SAEnum(CredentialStatus, values_callable=lambda e: [m.value for m in e], name="credential_status"),
        nullable=False,
        default=CredentialStatus.ACTIVE,
        index=True,
    )

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # SHA-256 hex digest of the credential document's bytes.
    document_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Base64-encoded signature over the canonical credential payload, produced
    # with the issuing institution's private key (Phase 4/5).
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Phase 9A/9B: blockchain hash-anchoring metadata --------------------
    # All nullable — an existing (or newly issued) credential is valid and
    # fully usable through the existing Ed25519 verification path whether or
    # not it has ever been anchored. Anchoring is an additional, optional
    # trust anchor, never a prerequisite for a credential being real.
    #
    # blockchain_credential_hash is NOT a duplicate of document_hash: it is
    # sha256(canonicalize_credential_payload(...)) — the hash of the full
    # canonical credential payload (identifiers, names, dates, and
    # document_hash all together) that Ed25519 already signs, not the hash
    # of the PDF bytes alone. document_hash is one input INTO that payload;
    # this is the hash of the payload itself, so it is what's meaningful to
    # anchor (it changes if ANY signed field would differ, not just the
    # document). Storing it explicitly (rather than recomputing on demand)
    # means the exact bytes that were anchored on-chain are preserved even if
    # reconstruct_canonical_payload's inputs could ever drift.
    blockchain_tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    blockchain_network: Mapped[str | None] = mapped_column(String(50), nullable=True)
    blockchain_contract_address: Mapped[str | None] = mapped_column(String(42), nullable=True)
    blockchain_credential_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    blockchain_anchored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    blockchain_status: Mapped[BlockchainAnchorStatus | None] = mapped_column(
        SAEnum(BlockchainAnchorStatus, values_callable=lambda e: [m.value for m in e], name="blockchain_anchor_status"),
        nullable=True,
    )

    student: Mapped[Student] = relationship(back_populates="credentials")
    institution: Mapped[Institution] = relationship(back_populates="credentials")
    document: Mapped[CredentialDocument | None] = relationship(
        back_populates="credential", uselist=False, cascade="all, delete-orphan"
    )
    verification_events: Mapped[list[VerificationEvent]] = relationship(back_populates="credential")
    share_grant_links: Mapped[list[ShareGrantCredential]] = relationship(back_populates="credential")
    share_grants: Mapped[list[ShareGrant]] = relationship(
        secondary="share_grant_credentials", back_populates="credentials", viewonly=True
    )

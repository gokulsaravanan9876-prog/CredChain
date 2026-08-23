from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .common import UUIDPrimaryKeyMixin
from .enums import SharePermission

if TYPE_CHECKING:
    from .company import Company
    from .credential import Credential
    from .credential_request import CredentialRequest
    from .student import Student


class ShareGrant(UUIDPrimaryKeyMixin, Base):
    """
    A student-issued grant letting one company view a specific set of
    credentials. The set is modeled as a real many-to-many relationship via
    the share_grant_credentials join table (see ShareGrantCredential below)
    rather than a raw array-of-UUIDs column, so each referenced credential is
    a real foreign key the database enforces — the spec's field list called
    this "credential_ids"; that name now lives on the join table instead of
    on this row directly (accessible here via the `credentials` relationship).

    share_token_hash, not the raw token, is what's persisted — the raw token
    is generated and returned to the client exactly once at creation time
    (Phase 6) and is never recoverable from the database afterward.

    No updated_at: a grant's only two allowed transitions are being created
    and being revoked (revoked_at), both are point-in-time facts, not a
    general-purpose "last edited" timestamp.
    """

    __tablename__ = "share_grants"
    __table_args__ = (Index("ix_share_grants_student_company", "student_id", "company_id"),)

    student_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Which company CredentialRequest (if any) this grant was created to
    # fulfill — null for a share not created via approve_request (none
    # exist today, but never assume). Lets verification compare what was
    # requested against what's actually being verified (see
    # verification_service.py's type-mismatch check). SET NULL, not
    # CASCADE: a request being removed should never destroy the grant/share
    # history that already happened.
    credential_request_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("credential_requests.id", ondelete="SET NULL"), nullable=True, index=True
    )

    permission: Mapped[SharePermission] = mapped_column(
        SAEnum(SharePermission, values_callable=lambda e: [m.value for m in e], name="share_permission"),
        nullable=False,
        default=SharePermission.VIEW_ONLY,
    )

    # SHA-256 (or similarly strong) hash of a cryptographically random token;
    # never the raw token. Unique + indexed since this is the lookup path for
    # GET /shares/verify/{token} (Phase 6).
    share_token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student: Mapped[Student] = relationship(back_populates="share_grants")
    company: Mapped[Company] = relationship(back_populates="share_grants")
    credential_request: Mapped[CredentialRequest | None] = relationship()
    credential_links: Mapped[list[ShareGrantCredential]] = relationship(
        back_populates="share_grant", cascade="all, delete-orphan"
    )
    credentials: Mapped[list[Credential]] = relationship(
        secondary="share_grant_credentials", back_populates="share_grants", viewonly=True
    )


class ShareGrantCredential(Base):
    """Join table: which credentials a given ShareGrant covers. Composite PK — a credential can only appear once per grant."""

    __tablename__ = "share_grant_credentials"

    share_grant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("share_grants.id", ondelete="CASCADE"), primary_key=True
    )
    credential_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("credentials.id", ondelete="CASCADE"), primary_key=True, index=True
    )

    share_grant: Mapped[ShareGrant] = relationship(back_populates="credential_links")
    credential: Mapped[Credential] = relationship(back_populates="share_grant_links")

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .common import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .credential import Credential
    from .institution_certificate_request import InstitutionCertificateRequest
    from .student import Student
    from .student_document import StudentDocument
    from .user import User


class Institution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    public_key is the institution's signing public key (PEM, populated once
    Phase 4/5 generates the keypair). It's safe to expose via the API; the
    matching private key never lives in this table or anywhere the ORM
    touches — see app/security/signatures.py (added Phase 4).

    user_id is nullable: a row with user_id=None is a directory-only listing
    (seeded from a curated public dataset, see scripts/seed_directory.py) —
    discoverable and linkable by a student, but with no CredChain login and
    therefore never able to issue credentials itself. A real institution
    that registers keeps (or gains) a non-null user_id exactly as before;
    nothing about the existing login-linked path changes.
    """

    __tablename__ = "institutions"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    registration_number: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    public_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Public directory fields — all optional, populated either by the seed
    # script (backend/scripts/seed_directory.py) or left blank for a real
    # institution that hasn't filled them in, never fabricated in the UI.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    institution_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Structured location (Phase 2) — lets search/filter use real indexed
    # equality/prefix predicates instead of substring-matching `location`.
    # NULL on every Phase 1 row; populated going forward by real imports.
    country: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Where this record came from (e.g. "manual_curated", "hipolabs_world_universities") and that
    # source's own stable id for it (e.g. a domain) — see scripts/import_institutions.py. Both NULL
    # for Phase 1's manually curated rows and for any institution that registered directly.
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped[User | None] = relationship(back_populates="institution")
    students: Mapped[list[Student]] = relationship(back_populates="institution")
    credentials: Mapped[list[Credential]] = relationship(back_populates="institution")
    institution_certificate_requests: Mapped[list[InstitutionCertificateRequest]] = relationship(back_populates="institution")
    student_documents: Mapped[list[StudentDocument]] = relationship(back_populates="institution")

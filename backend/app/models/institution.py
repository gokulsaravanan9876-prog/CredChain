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
    """

    __tablename__ = "institutions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    registration_number: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    public_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="institution")
    students: Mapped[list[Student]] = relationship(back_populates="institution")
    credentials: Mapped[list[Credential]] = relationship(back_populates="institution")
    institution_certificate_requests: Mapped[list[InstitutionCertificateRequest]] = relationship(back_populates="institution")
    student_documents: Mapped[list[StudentDocument]] = relationship(back_populates="institution")

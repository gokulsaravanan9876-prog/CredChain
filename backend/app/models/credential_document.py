from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .common import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .credential import Credential


class CredentialDocument(UUIDPrimaryKeyMixin, Base):
    """
    Metadata + a reference to the actual file, which lives in private
    filesystem/object storage (see app/services/document_service.py, added
    Phase 4) — never in this table. One document per credential; storage_path
    is an internal reference only and must never be returned directly to a
    client (see app/security/permissions.py, added Phase 4).

    No updated_at: a document upload is treated as an immutable fact about a
    credential — replacing a document means issuing a new credential, not
    mutating this row.
    """

    __tablename__ = "credential_documents"

    credential_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("credentials.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    # SHA-256 hex digest of the file bytes at upload time — the trusted value
    # future integrity checks compare a presented document against.
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    credential: Mapped[Credential] = relationship(back_populates="document")

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .common import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .user import User


class ActivityLog(UUIDPrimaryKeyMixin, Base):
    """
    Append-only audit trail. `action` is a free-text code (e.g.
    CREDENTIAL_ISSUED, LOGIN_FAILED — see the examples in the product spec)
    rather than a hard Postgres enum, since the action vocabulary is expected
    to grow across later phases without needing a migration each time.

    `entity_type` + `entity_id` is a generic, non-FK-constrained reference
    (a log entry can point at a credential, a share grant, a request, etc.)
    — deliberately not a real foreign key, since a single column can't
    reference multiple tables, and this table must never lose rows just
    because the entity it references was later deleted.

    actor_user_id is nullable with ON DELETE SET NULL: some events genuinely
    have no resolvable user (e.g. LOGIN_FAILED against an email that doesn't
    exist), and a log row must survive even if the acting user is later
    deleted — audit trail durability outranks referential strictness here.

    No update/delete path is exposed anywhere in the API by design (routes
    only ever INSERT into this table) — enforced at the application layer
    for now; a stricter DB-level guarantee (e.g. REVOKE UPDATE, DELETE) is a
    reasonable hardening step for later, not required for the hackathon MVP.
    """

    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_activity_logs_entity", "entity_type", "entity_id"),
        Index("ix_activity_logs_created_at", "created_at"),
    )

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    # Mapped Python attribute is `metadata_` because `metadata` is reserved by
    # SQLAlchemy's declarative Base; the actual DB column is still "metadata".
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    actor_user: Mapped[User | None] = relationship(back_populates="activity_logs")

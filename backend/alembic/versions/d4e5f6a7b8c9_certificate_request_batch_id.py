"""add batch_id to institution_certificate_requests for multi-document requests

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "institution_certificate_requests",
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_institution_certificate_requests_batch_id",
        "institution_certificate_requests",
        ["batch_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_institution_certificate_requests_batch_id", table_name="institution_certificate_requests")
    op.drop_column("institution_certificate_requests", "batch_id")

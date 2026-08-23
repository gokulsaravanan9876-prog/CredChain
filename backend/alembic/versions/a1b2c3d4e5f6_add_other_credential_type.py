"""add OTHER value to credential_type enum

Revision ID: a1b2c3d4e5f6
Revises: fc9bbe8065cb
Create Date: 2026-08-22 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fc9bbe8065cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE credential_type ADD VALUE IF NOT EXISTS 'other'")


def downgrade() -> None:
    # Postgres has no ALTER TYPE ... DROP VALUE — removing an enum value
    # requires rebuilding the type, which is unsafe to do blindly in a
    # downgrade (would fail if any row already uses 'other'). Left as a
    # no-op, consistent with this being an additive, backward-compatible
    # change.
    pass

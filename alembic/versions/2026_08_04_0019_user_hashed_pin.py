"""Add hashed_pin to users for account-level app PIN

Revision ID: k1f2a3b4c5d6
Revises: j0e1f2a3b4c5
Create Date: 2026-08-04 14:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "k1f2a3b4c5d6"
down_revision: str | Sequence[str] | None = "j0e1f2a3b4c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("hashed_pin", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "hashed_pin")

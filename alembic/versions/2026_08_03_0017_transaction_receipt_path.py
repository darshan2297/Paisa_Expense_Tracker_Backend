"""Add receipt_path to transactions

Revision ID: i9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2026-08-03 01:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "i9d0e1f2a3b4"
down_revision: str | Sequence[str] | None = "h8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("receipt_path", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transactions", "receipt_path")

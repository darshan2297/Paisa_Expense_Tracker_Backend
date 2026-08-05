"""Add payment_method to transactions

Revision ID: n4i5d6e7f8g9
Revises: m3h4c5d6e7f8
Create Date: 2026-08-05 21:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "n4i5d6e7f8g9"
down_revision: str | Sequence[str] | None = "m3h4c5d6e7f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("payment_method", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("transactions", "payment_method")

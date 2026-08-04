"""Add optional monthly EMI amount on credit cards

Revision ID: l2g3b4c5d6e7
Revises: k1f2a3b4c5d6
Create Date: 2026-08-05 00:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "l2g3b4c5d6e7"
down_revision: str | Sequence[str] | None = "k1f2a3b4c5d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "credit_cards",
        sa.Column("emi_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("credit_cards", "emi_amount")

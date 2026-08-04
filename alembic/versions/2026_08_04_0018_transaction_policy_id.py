"""Add policy_id to transactions

Revision ID: j0e1f2a3b4c5
Revises: i9d0e1f2a3b4
Create Date: 2026-08-04 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "j0e1f2a3b4c5"
down_revision: str | Sequence[str] | None = "i9d0e1f2a3b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("policy_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_transactions_policy_id"), "transactions", "policies", ["policy_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_transactions_policy_id"), "transactions", type_="foreignkey")
    op.drop_column("transactions", "policy_id")

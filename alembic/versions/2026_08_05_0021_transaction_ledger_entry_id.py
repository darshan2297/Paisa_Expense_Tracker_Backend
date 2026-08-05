"""Add ledger_entry_id to transactions

Revision ID: m3h4c5d6e7f8
Revises: l2g3b4c5d6e7
Create Date: 2026-08-05 20:55:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "m3h4c5d6e7f8"
down_revision: str | Sequence[str] | None = "l2g3b4c5d6e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("ledger_entry_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_transactions_ledger_entry_id"),
        "transactions",
        "ledger_entries",
        ["ledger_entry_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_transactions_ledger_entry_id"),
        "transactions",
        ["ledger_entry_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_ledger_entry_id"), table_name="transactions")
    op.drop_constraint(op.f("fk_transactions_ledger_entry_id"), "transactions", type_="foreignkey")
    op.drop_column("transactions", "ledger_entry_id")

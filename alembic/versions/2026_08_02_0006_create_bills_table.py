"""create bills table and link transactions

Revision ID: d8a1b2c3e4f5
Revises: c7f9e1b3d5a4
Create Date: 2026-08-02 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d8a1b2c3e4f5"
down_revision: str | Sequence[str] | None = "c7f9e1b3d5a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bills",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("frequency", sa.String(length=16), server_default="monthly", nullable=False),
        sa.Column("auto_pay", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("lead_days", sa.Integer(), server_default="3", nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("paid_on", sa.Date(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_bills_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bills")),
    )
    op.create_index(op.f("ix_bills_user_id"), "bills", ["user_id"], unique=False)
    op.create_index(op.f("ix_bills_due_date"), "bills", ["due_date"], unique=False)

    op.add_column("transactions", sa.Column("bill_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_transactions_bill_id"), "transactions", "bills", ["bill_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_transactions_bill_id"), "transactions", type_="foreignkey")
    op.drop_column("transactions", "bill_id")
    op.drop_table("bills")

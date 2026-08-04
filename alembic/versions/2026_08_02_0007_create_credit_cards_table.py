"""create credit_cards table and link transactions

Revision ID: e9b2c3d4f5a6
Revises: d8a1b2c3e4f5
Create Date: 2026-08-02 18:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e9b2c3d4f5a6"
down_revision: str | Sequence[str] | None = "d8a1b2c3e4f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "credit_cards",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("bank", sa.String(length=255), nullable=False),
        sa.Column("network", sa.String(length=64), server_default="Visa", nullable=False),
        sa.Column("last4", sa.String(length=4), nullable=False),
        sa.Column("credit_limit", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("outstanding", sa.Numeric(precision=14, scale=2), server_default="0", nullable=False),
        sa.Column("statement_day", sa.Integer(), nullable=False),
        sa.Column("due_day", sa.Integer(), nullable=False),
        sa.Column("opened_on", sa.Date(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_credit_cards_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_credit_cards")),
    )
    op.create_index(op.f("ix_credit_cards_user_id"), "credit_cards", ["user_id"], unique=False)

    op.add_column("transactions", sa.Column("card_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_transactions_card_id"), "transactions", "credit_cards", ["card_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_transactions_card_id"), "transactions", type_="foreignkey")
    op.drop_column("transactions", "card_id")
    op.drop_table("credit_cards")

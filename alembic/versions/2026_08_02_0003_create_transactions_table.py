"""create transactions table

Revision ID: 9d3b5f7a1c2e
Revises: 6f2a1c8e4b7d
Create Date: 2026-08-02 09:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9d3b5f7a1c2e"
down_revision: str | Sequence[str] | None = "6f2a1c8e4b7d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "transactions",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_transactions_user_id")),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name=op.f("fk_transactions_account_id")
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], name=op.f("fk_transactions_category_id")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
    )
    # Composite index backing every month-scoped query (list/summary) - see
    # docs/DATABASE_STANDARDS.md's indexing guidance for this exact table.
    op.create_index(
        "ix_transactions_user_id_date", "transactions", ["user_id", "date"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_transactions_user_id_date", table_name="transactions")
    op.drop_table("transactions")

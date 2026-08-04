"""create fixed_commitments table and link transactions to it

Revision ID: c7f9e1b3d5a4
Revises: b4e6d8f2a3c1
Create Date: 2026-08-02 10:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7f9e1b3d5a4"
down_revision: str | Sequence[str] | None = "b4e6d8f2a3c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "fixed_commitments",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("due_day", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=24), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_fixed_commitments_user_id")
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], name=op.f("fk_fixed_commitments_category_id")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fixed_commitments")),
    )

    # Append-only: `transactions` already exists (F3) - add the nullable
    # link column now that `fixed_commitments` exists for it to reference.
    op.add_column("transactions", sa.Column("fixed_commitment_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_transactions_fixed_commitment_id"),
        "transactions",
        "fixed_commitments",
        ["fixed_commitment_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f("fk_transactions_fixed_commitment_id"), "transactions", type_="foreignkey"
    )
    op.drop_column("transactions", "fixed_commitment_id")
    op.drop_table("fixed_commitments")

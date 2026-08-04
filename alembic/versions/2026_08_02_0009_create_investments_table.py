"""create investments table

Revision ID: a1b2c3d4e5f6
Revises: f0a1b2c3d4e5
Create Date: 2026-08-02 20:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f0a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investments",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("invested_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("current_value", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column(
            "monthly_sip", sa.Numeric(precision=14, scale=2), server_default="0", nullable=False
        ),
        sa.Column("opened_on", sa.Date(), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_investments_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_investments")),
    )
    op.create_index(op.f("ix_investments_user_id"), "investments", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("investments")

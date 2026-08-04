"""create goals table

Revision ID: f0a1b2c3d4e5
Revises: e9b2c3d4f5a6
Create Date: 2026-08-02 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f0a1b2c3d4e5"
down_revision: str | Sequence[str] | None = "e9b2c3d4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("target_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column(
            "saved_amount", sa.Numeric(precision=14, scale=2), server_default="0", nullable=False
        ),
        sa.Column(
            "monthly_contribution",
            sa.Numeric(precision=14, scale=2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("is_emergency", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("due_day", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_goals_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_goals")),
    )
    op.create_index(op.f("ix_goals_user_id"), "goals", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("goals")

"""create budget_settings table

Revision ID: b4e6d8f2a3c1
Revises: 9d3b5f7a1c2e
Create Date: 2026-08-02 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4e6d8f2a3c1"
down_revision: str | Sequence[str] | None = "9d3b5f7a1c2e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "budget_settings",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("monthly_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("alert_pct", sa.Integer(), server_default="20", nullable=False),
        sa.Column("reminder_lead_days", sa.Integer(), server_default="15", nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_budget_settings_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_budget_settings")),
        sa.UniqueConstraint("user_id", name=op.f("uq_budget_settings_user_id")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("budget_settings")

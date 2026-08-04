"""create assets and net_worth_snapshots tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-02 20:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("purchase_value", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("current_value", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("acquired_on", sa.Date(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_assets_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assets")),
    )
    op.create_index(op.f("ix_assets_user_id"), "assets", ["user_id"], unique=False)

    op.create_table(
        "net_worth_snapshots",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_assets", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("total_liabilities", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("net_worth", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("breakdown_json", sa.String(), server_default="{}", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_net_worth_snapshots_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_net_worth_snapshots")),
    )
    op.create_index(op.f("ix_net_worth_snapshots_user_id"), "net_worth_snapshots", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("net_worth_snapshots")
    op.drop_table("assets")

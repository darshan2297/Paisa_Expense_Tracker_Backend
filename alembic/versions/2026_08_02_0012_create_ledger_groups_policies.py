"""create ledger_entries, expense_groups, group_expenses, group_settlements, policies

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-02 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ledger_entries",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("person_name", sa.String(length=255), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=512), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_ledger_entries_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ledger_entries")),
    )
    op.create_index(op.f("ix_ledger_entries_user_id"), "ledger_entries", ["user_id"], unique=False)

    op.create_table(
        "expense_groups",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("members", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_expense_groups_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expense_groups")),
    )
    op.create_index(op.f("ix_expense_groups_user_id"), "expense_groups", ["user_id"], unique=False)

    op.create_table(
        "group_expenses",
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("payer", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("split_type", sa.String(length=16), server_default="equal", nullable=False),
        sa.Column("splits", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["expense_groups.id"], name=op.f("fk_group_expenses_group_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_group_expenses")),
    )

    op.create_table(
        "group_settlements",
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("from_member", sa.String(length=255), nullable=False),
        sa.Column("to_member", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["expense_groups.id"], name=op.f("fk_group_settlements_group_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_group_settlements")),
    )

    op.create_table(
        "policies",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("cover_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("premium", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("frequency", sa.String(length=16), nullable=False),
        sa.Column("renewal_date", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=512), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_policies_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_policies")),
    )
    op.create_index(op.f("ix_policies_user_id"), "policies", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("policies")
    op.drop_table("group_settlements")
    op.drop_table("group_expenses")
    op.drop_table("expense_groups")
    op.drop_table("ledger_entries")

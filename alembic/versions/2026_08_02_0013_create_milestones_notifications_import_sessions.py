"""create milestones, notifications, import, sessions tables

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-02 21:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "milestones",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("note", sa.String(length=512), nullable=True),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), server_default="0", nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_milestones_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_milestones")),
    )

    op.create_table(
        "notifications",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.String(length=1024), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", sa.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_notifications_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )

    op.create_table(
        "push_tokens",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("expo_push_token", sa.String(length=512), nullable=False),
        sa.Column("device_label", sa.String(length=255), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_push_tokens_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_push_tokens")),
        sa.UniqueConstraint("expo_push_token", name=op.f("uq_push_tokens_expo_push_token")),
    )

    op.create_table(
        "import_jobs",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="uploaded", nullable=False),
        sa.Column("row_count", sa.Integer(), server_default="0", nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_import_jobs_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_jobs")),
    )

    op.create_table(
        "import_rows",
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("merchant", sa.String(length=512), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("suggested_category_id", sa.UUID(), nullable=True),
        sa.Column("state", sa.String(length=16), server_default="ready", nullable=False),
        sa.Column("duplicate_of_txn_id", sa.UUID(), nullable=True),
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
        sa.ForeignKeyConstraint(["job_id"], ["import_jobs.id"], name=op.f("fk_import_rows_job_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_rows")),
    )

    op.create_table(
        "sessions",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("device_label", sa.String(length=255), nullable=False),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_sessions_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
    )

    op.create_table(
        "backups",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_backups_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_backups")),
    )


def downgrade() -> None:
    op.drop_table("backups")
    op.drop_table("sessions")
    op.drop_table("import_rows")
    op.drop_table("import_jobs")
    op.drop_table("push_tokens")
    op.drop_table("notifications")
    op.drop_table("milestones")

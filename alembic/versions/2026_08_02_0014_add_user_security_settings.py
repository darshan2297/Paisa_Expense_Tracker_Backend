"""add user security settings and security_events

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-02 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: str | Sequence[str] | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("pin_lock_enabled", sa.Boolean(), server_default="true", nullable=False))
    op.add_column(
        "users", sa.Column("fingerprint_login_enabled", sa.Boolean(), server_default="true", nullable=False)
    )
    op.add_column("users", sa.Column("face_id_enabled", sa.Boolean(), server_default="false", nullable=False))
    op.add_column(
        "users", sa.Column("password_protection_enabled", sa.Boolean(), server_default="true", nullable=False)
    )
    op.add_column(
        "users", sa.Column("hide_sensitive_amounts", sa.Boolean(), server_default="false", nullable=False)
    )
    op.add_column(
        "users", sa.Column("privacy_mode_enabled", sa.Boolean(), server_default="false", nullable=False)
    )
    op.add_column("users", sa.Column("auto_lock_enabled", sa.Boolean(), server_default="true", nullable=False))
    op.add_column(
        "users", sa.Column("cloud_backup_enabled", sa.Boolean(), server_default="true", nullable=False)
    )
    op.add_column(
        "users", sa.Column("local_backup_enabled", sa.Boolean(), server_default="false", nullable=False)
    )
    op.add_column(
        "users", sa.Column("e2e_encryption_enabled", sa.Boolean(), server_default="true", nullable=False)
    )
    op.add_column("users", sa.Column("two_factor_enabled", sa.Boolean(), server_default="true", nullable=False))
    op.add_column("users", sa.Column("auto_logout_minutes", sa.Integer(), server_default="5", nullable=False))
    op.add_column("users", sa.Column("vault_locked", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("users", sa.Column("last_backup_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_backup_size_bytes", sa.Integer(), nullable=True))

    op.add_column("sessions", sa.Column("location", sa.String(length=255), nullable=True))
    op.add_column("sessions", sa.Column("is_current", sa.Boolean(), server_default="false", nullable=False))

    op.create_table(
        "security_events",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("device_label", sa.String(length=255), nullable=False),
        sa.Column("detail", sa.String(length=512), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_security_events_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_security_events")),
    )
    op.create_index(op.f("ix_security_events_user_id"), "security_events", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_security_events_user_id"), table_name="security_events")
    op.drop_table("security_events")
    op.drop_column("sessions", "is_current")
    op.drop_column("sessions", "location")
    op.drop_column("users", "last_backup_size_bytes")
    op.drop_column("users", "last_backup_at")
    op.drop_column("users", "vault_locked")
    op.drop_column("users", "auto_logout_minutes")
    op.drop_column("users", "two_factor_enabled")
    op.drop_column("users", "e2e_encryption_enabled")
    op.drop_column("users", "local_backup_enabled")
    op.drop_column("users", "cloud_backup_enabled")
    op.drop_column("users", "auto_lock_enabled")
    op.drop_column("users", "privacy_mode_enabled")
    op.drop_column("users", "hide_sensitive_amounts")
    op.drop_column("users", "password_protection_enabled")
    op.drop_column("users", "face_id_enabled")
    op.drop_column("users", "fingerprint_login_enabled")
    op.drop_column("users", "pin_lock_enabled")

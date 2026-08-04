"""add user_configurations table and move settings off users

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-02 23:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "g7b8c9d0e1f2"
down_revision: str | Sequence[str] | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_configurations",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("month_start_day", sa.Integer(), server_default="1", nullable=False),
        sa.Column("dark_mode", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("week_start_monday", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("round_up_savings", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("digest_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("sound_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("pin_lock_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("fingerprint_login_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("face_id_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "password_protection_enabled", sa.Boolean(), server_default="true", nullable=False
        ),
        sa.Column("hide_sensitive_amounts", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("privacy_mode_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("auto_lock_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("cloud_backup_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("local_backup_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("e2e_encryption_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("two_factor_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("auto_logout_minutes", sa.Integer(), server_default="5", nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_user_configurations_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_configurations")),
        sa.UniqueConstraint("user_id", name=op.f("uq_user_configurations_user_id")),
    )
    op.create_index(
        op.f("ix_user_configurations_user_id"), "user_configurations", ["user_id"], unique=False
    )

    op.execute(
        sa.text(
            """
            INSERT INTO user_configurations (
                id, user_id, currency, month_start_day,
                dark_mode, week_start_monday, round_up_savings, digest_enabled, sound_enabled,
                pin_lock_enabled, fingerprint_login_enabled, face_id_enabled,
                password_protection_enabled, hide_sensitive_amounts, privacy_mode_enabled,
                auto_lock_enabled, cloud_backup_enabled, local_backup_enabled,
                e2e_encryption_enabled, two_factor_enabled, auto_logout_minutes,
                created_at, updated_at
            )
            SELECT
                gen_random_uuid(), id, currency, month_start_day,
                dark_mode, week_start_monday, round_up_savings, digest_enabled, sound_enabled,
                pin_lock_enabled, fingerprint_login_enabled, face_id_enabled,
                password_protection_enabled, hide_sensitive_amounts, privacy_mode_enabled,
                auto_lock_enabled, cloud_backup_enabled, local_backup_enabled,
                e2e_encryption_enabled, two_factor_enabled, auto_logout_minutes,
                now(), now()
            FROM users
            """
        )
    )

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
    op.drop_column("users", "sound_enabled")
    op.drop_column("users", "digest_enabled")
    op.drop_column("users", "round_up_savings")
    op.drop_column("users", "week_start_monday")
    op.drop_column("users", "dark_mode")
    op.drop_column("users", "month_start_day")
    op.drop_column("users", "currency")


def downgrade() -> None:
    op.add_column("users", sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False))
    op.add_column("users", sa.Column("month_start_day", sa.Integer(), server_default="1", nullable=False))
    op.add_column("users", sa.Column("dark_mode", sa.Boolean(), server_default="false", nullable=False))
    op.add_column(
        "users", sa.Column("week_start_monday", sa.Boolean(), server_default="true", nullable=False)
    )
    op.add_column(
        "users", sa.Column("round_up_savings", sa.Boolean(), server_default="false", nullable=False)
    )
    op.add_column("users", sa.Column("digest_enabled", sa.Boolean(), server_default="true", nullable=False))
    op.add_column("users", sa.Column("sound_enabled", sa.Boolean(), server_default="true", nullable=False))
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

    op.execute(
        sa.text(
            """
            UPDATE users u SET
                currency = c.currency,
                month_start_day = c.month_start_day,
                dark_mode = c.dark_mode,
                week_start_monday = c.week_start_monday,
                round_up_savings = c.round_up_savings,
                digest_enabled = c.digest_enabled,
                sound_enabled = c.sound_enabled,
                pin_lock_enabled = c.pin_lock_enabled,
                fingerprint_login_enabled = c.fingerprint_login_enabled,
                face_id_enabled = c.face_id_enabled,
                password_protection_enabled = c.password_protection_enabled,
                hide_sensitive_amounts = c.hide_sensitive_amounts,
                privacy_mode_enabled = c.privacy_mode_enabled,
                auto_lock_enabled = c.auto_lock_enabled,
                cloud_backup_enabled = c.cloud_backup_enabled,
                local_backup_enabled = c.local_backup_enabled,
                e2e_encryption_enabled = c.e2e_encryption_enabled,
                two_factor_enabled = c.two_factor_enabled,
                auto_logout_minutes = c.auto_logout_minutes
            FROM user_configurations c
            WHERE c.user_id = u.id
            """
        )
    )

    op.drop_index(op.f("ix_user_configurations_user_id"), table_name="user_configurations")
    op.drop_table("user_configurations")

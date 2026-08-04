"""configurations catalog + user_configurations key-value rows

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-08-02 23:30:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "h8c9d0e1f2a3"
down_revision: str | Sequence[str] | None = "g7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CATALOG_ROWS = [
    ("currency", "preferences", "string", "INR", "Currency", "ISO 4217 currency code", '["INR"]'),
    (
        "month_start_day",
        "preferences",
        "integer",
        "1",
        "Month start day",
        "Budget month start day (1-28)",
        None,
    ),
    ("dark_mode", "preferences", "boolean", "false", "Dark mode", "Use dark theme", None),
    (
        "week_start_monday",
        "preferences",
        "boolean",
        "true",
        "Week starts Monday",
        "Calendar weeks begin on Monday",
        None,
    ),
    (
        "round_up_savings",
        "preferences",
        "boolean",
        "false",
        "Round-up savings",
        "Round expenses and save spare change",
        None,
    ),
    (
        "digest_enabled",
        "preferences",
        "boolean",
        "true",
        "Weekly digest",
        "Weekly spending summary",
        None,
    ),
    (
        "sound_enabled",
        "preferences",
        "boolean",
        "true",
        "Sound effects",
        "Play sounds for actions",
        None,
    ),
    ("pin_lock_enabled", "security", "boolean", "true", "PIN lock", "6-digit PIN on launch", None),
    (
        "fingerprint_login_enabled",
        "security",
        "boolean",
        "true",
        "Fingerprint login",
        "Unlock with fingerprint",
        None,
    ),
    ("face_id_enabled", "security", "boolean", "false", "Face ID", "Unlock with face", None),
    (
        "password_protection_enabled",
        "security",
        "boolean",
        "true",
        "Password protection",
        "Fallback password for new devices",
        None,
    ),
    (
        "hide_sensitive_amounts",
        "security",
        "boolean",
        "false",
        "Hide sensitive amounts",
        "Blur balances until tapped",
        None,
    ),
    (
        "privacy_mode_enabled",
        "security",
        "boolean",
        "false",
        "Privacy mode",
        "Hide values when app loses focus",
        None,
    ),
    (
        "auto_lock_enabled",
        "security",
        "boolean",
        "true",
        "Auto lock",
        "Lock after session timeout",
        None,
    ),
    (
        "cloud_backup_enabled",
        "security",
        "boolean",
        "true",
        "Cloud backup",
        "Encrypted nightly cloud backup",
        None,
    ),
    (
        "local_backup_enabled",
        "security",
        "boolean",
        "false",
        "Local backup",
        "Keep a copy on device",
        None,
    ),
    (
        "e2e_encryption_enabled",
        "security",
        "boolean",
        "true",
        "End-to-end encryption",
        "User-held decryption key",
        None,
    ),
    (
        "two_factor_enabled",
        "security",
        "boolean",
        "true",
        "Two-factor authentication",
        "OTP on new sign-ins",
        None,
    ),
    (
        "auto_logout_minutes",
        "security",
        "integer",
        "5",
        "Auto-logout after",
        "Inactivity timeout in minutes",
        "[1,5,15,30]",
    ),
]

FLAT_COLUMN_MAP = [
    ("currency", "currency"),
    ("month_start_day", "month_start_day::text"),
    ("dark_mode", "CASE WHEN dark_mode THEN 'true' ELSE 'false' END"),
    ("week_start_monday", "CASE WHEN week_start_monday THEN 'true' ELSE 'false' END"),
    ("round_up_savings", "CASE WHEN round_up_savings THEN 'true' ELSE 'false' END"),
    ("digest_enabled", "CASE WHEN digest_enabled THEN 'true' ELSE 'false' END"),
    ("sound_enabled", "CASE WHEN sound_enabled THEN 'true' ELSE 'false' END"),
    ("pin_lock_enabled", "CASE WHEN pin_lock_enabled THEN 'true' ELSE 'false' END"),
    (
        "fingerprint_login_enabled",
        "CASE WHEN fingerprint_login_enabled THEN 'true' ELSE 'false' END",
    ),
    ("face_id_enabled", "CASE WHEN face_id_enabled THEN 'true' ELSE 'false' END"),
    (
        "password_protection_enabled",
        "CASE WHEN password_protection_enabled THEN 'true' ELSE 'false' END",
    ),
    ("hide_sensitive_amounts", "CASE WHEN hide_sensitive_amounts THEN 'true' ELSE 'false' END"),
    ("privacy_mode_enabled", "CASE WHEN privacy_mode_enabled THEN 'true' ELSE 'false' END"),
    ("auto_lock_enabled", "CASE WHEN auto_lock_enabled THEN 'true' ELSE 'false' END"),
    ("cloud_backup_enabled", "CASE WHEN cloud_backup_enabled THEN 'true' ELSE 'false' END"),
    ("local_backup_enabled", "CASE WHEN local_backup_enabled THEN 'true' ELSE 'false' END"),
    ("e2e_encryption_enabled", "CASE WHEN e2e_encryption_enabled THEN 'true' ELSE 'false' END"),
    ("two_factor_enabled", "CASE WHEN two_factor_enabled THEN 'true' ELSE 'false' END"),
    ("auto_logout_minutes", "auto_logout_minutes::text"),
]


def upgrade() -> None:
    bind = op.get_bind()

    def table_names() -> set[str]:
        return set(sa.inspect(bind).get_table_names())

    if "configurations" not in table_names():
        op.create_table(
            "configurations",
            sa.Column("key", sa.String(length=64), nullable=False),
            sa.Column("category", sa.String(length=32), nullable=False),
            sa.Column("value_type", sa.String(length=16), nullable=False),
            sa.Column("default_value", sa.String(length=255), nullable=False),
            sa.Column("label", sa.String(length=255), nullable=True),
            sa.Column("description", sa.String(length=512), nullable=True),
            sa.Column("allowed_values", sa.String(length=512), nullable=True),
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
            sa.PrimaryKeyConstraint("id", name=op.f("pk_configurations")),
            sa.UniqueConstraint("key", name=op.f("uq_configurations_key")),
        )
        op.create_index(
            op.f("ix_configurations_category"), "configurations", ["category"], unique=False
        )
        op.create_index(op.f("ix_configurations_key"), "configurations", ["key"], unique=False)

        configurations = sa.table(
            "configurations",
            sa.column("id", sa.UUID()),
            sa.column("key", sa.String()),
            sa.column("category", sa.String()),
            sa.column("value_type", sa.String()),
            sa.column("default_value", sa.String()),
            sa.column("label", sa.String()),
            sa.column("description", sa.String()),
            sa.column("allowed_values", sa.String()),
        )
        op.bulk_insert(
            configurations,
            [
                {
                    "id": str(uuid.uuid4()),
                    "key": key,
                    "category": category,
                    "value_type": value_type,
                    "default_value": default_value,
                    "label": label,
                    "description": description,
                    "allowed_values": allowed_values,
                }
                for key, category, value_type, default_value, label, description, allowed_values in CATALOG_ROWS
            ],
        )

    if "user_configuration_values" not in table_names():
        op.create_table(
            "user_configuration_values",
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("configuration_id", sa.UUID(), nullable=False),
            sa.Column("value", sa.String(length=255), nullable=False),
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
            sa.ForeignKeyConstraint(
                ["configuration_id"],
                ["configurations.id"],
                name=op.f("fk_user_configuration_values_configuration_id"),
            ),
            sa.ForeignKeyConstraint(
                ["user_id"], ["users.id"], name=op.f("fk_user_configuration_values_user_id")
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_user_configuration_values")),
            sa.UniqueConstraint(
                "user_id", "configuration_id", name=op.f("uq_user_configuration_values_user_option")
            ),
        )
        op.create_index(
            op.f("ix_user_configuration_values_configuration_id"),
            "user_configuration_values",
            ["configuration_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_user_configuration_values_user_id"),
            "user_configuration_values",
            ["user_id"],
            unique=False,
        )

        flat_source = (
            "user_configurations_flat"
            if "user_configurations_flat" in table_names()
            else "user_configurations"
        )

        for config_key, value_expr in FLAT_COLUMN_MAP:
            op.execute(
                sa.text(
                    f"""
                    INSERT INTO user_configuration_values (id, user_id, configuration_id, value, created_at, updated_at)
                    SELECT gen_random_uuid(), l.user_id, c.id, {value_expr}, now(), now()
                    FROM {flat_source} l
                    JOIN configurations c ON c.key = :config_key
                    """
                ).bindparams(config_key=config_key)
            )

    tables = table_names()
    if "user_configurations_flat" in tables:
        op.drop_table("user_configurations_flat")
    elif "user_configurations" in tables and "user_configuration_values" in tables:
        op.drop_index(op.f("ix_user_configurations_user_id"), table_name="user_configurations")
        op.drop_table("user_configurations")

    if "user_configuration_values" in table_names():
        op.rename_table("user_configuration_values", "user_configurations")


def downgrade() -> None:
    raise NotImplementedError("Downgrade not supported for catalog migration")

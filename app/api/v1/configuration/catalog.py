"""Seed definitions for the `configurations` catalog table.

Single source of truth for default configuration options. New options are
added here, then picked up automatically by `scripts/seed_reference_data`
(on container start) and app startup — same lifecycle as category taxonomy.
"""

from typing import TypedDict


class ConfigurationDefinition(TypedDict):
    key: str
    category: str
    value_type: str
    default_value: str
    label: str
    description: str
    allowed_values: str | None


CONFIGURATION_DEFINITIONS: list[ConfigurationDefinition] = [
    {
        "key": "currency",
        "category": "preferences",
        "value_type": "string",
        "default_value": "INR",
        "label": "Currency",
        "description": "ISO 4217 currency code for amounts and reports",
        "allowed_values": '["INR"]',
    },
    {
        "key": "month_start_day",
        "category": "preferences",
        "value_type": "integer",
        "default_value": "1",
        "label": "Month start day",
        "description": "Day of month (1-28) your budget month begins on",
        "allowed_values": None,
    },
    {
        "key": "dark_mode",
        "category": "preferences",
        "value_type": "boolean",
        "default_value": "false",
        "label": "Dark mode",
        "description": "Use dark theme across the app",
        "allowed_values": None,
    },
    {
        "key": "week_start_monday",
        "category": "preferences",
        "value_type": "boolean",
        "default_value": "true",
        "label": "Week starts Monday",
        "description": "Calendar weeks begin on Monday instead of Sunday",
        "allowed_values": None,
    },
    {
        "key": "round_up_savings",
        "category": "preferences",
        "value_type": "boolean",
        "default_value": "false",
        "label": "Round-up savings",
        "description": "Round expenses up and save the spare change",
        "allowed_values": None,
    },
    {
        "key": "digest_enabled",
        "category": "preferences",
        "value_type": "boolean",
        "default_value": "true",
        "label": "Weekly digest",
        "description": "Receive a weekly spending summary",
        "allowed_values": None,
    },
    {
        "key": "sound_enabled",
        "category": "preferences",
        "value_type": "boolean",
        "default_value": "true",
        "label": "Sound effects",
        "description": "Play sounds for actions and alerts",
        "allowed_values": None,
    },
    {
        "key": "pin_lock_enabled",
        "category": "security",
        "value_type": "boolean",
        "default_value": "true",
        "label": "PIN lock",
        "description": "6-digit PIN on every launch",
        "allowed_values": None,
    },
    {
        "key": "fingerprint_login_enabled",
        "category": "security",
        "value_type": "boolean",
        "default_value": "true",
        "label": "Fingerprint login",
        "description": "Unlock with your fingerprint",
        "allowed_values": None,
    },
    {
        "key": "face_id_enabled",
        "category": "security",
        "value_type": "boolean",
        "default_value": "false",
        "label": "Face ID",
        "description": "Unlock by looking at the screen",
        "allowed_values": None,
    },
    {
        "key": "password_protection_enabled",
        "category": "security",
        "value_type": "boolean",
        "default_value": "true",
        "label": "Password protection",
        "description": "Fallback password for new devices",
        "allowed_values": None,
    },
    {
        "key": "hide_sensitive_amounts",
        "category": "security",
        "value_type": "boolean",
        "default_value": "false",
        "label": "Hide sensitive amounts",
        "description": "Blur balances until you tap them",
        "allowed_values": None,
    },
    {
        "key": "privacy_mode_enabled",
        "category": "security",
        "value_type": "boolean",
        "default_value": "false",
        "label": "Privacy mode",
        "description": "Hide all values when the app loses focus",
        "allowed_values": None,
    },
    {
        "key": "auto_lock_enabled",
        "category": "security",
        "value_type": "boolean",
        "default_value": "true",
        "label": "Auto lock",
        "description": "Lock after the session timeout",
        "allowed_values": None,
    },
    {
        "key": "cloud_backup_enabled",
        "category": "security",
        "value_type": "boolean",
        "default_value": "true",
        "label": "Cloud backup",
        "description": "Encrypted nightly backup to your drive",
        "allowed_values": None,
    },
    {
        "key": "local_backup_enabled",
        "category": "security",
        "value_type": "boolean",
        "default_value": "false",
        "label": "Local backup",
        "description": "Keep a copy on this device",
        "allowed_values": None,
    },
    {
        "key": "e2e_encryption_enabled",
        "category": "security",
        "value_type": "boolean",
        "default_value": "true",
        "label": "End-to-end encryption",
        "description": "Only you hold the decryption key",
        "allowed_values": None,
    },
    {
        "key": "two_factor_enabled",
        "category": "security",
        "value_type": "boolean",
        "default_value": "true",
        "label": "Two-factor authentication",
        "description": "One-time code on new sign-ins",
        "allowed_values": None,
    },
    {
        "key": "auto_logout_minutes",
        "category": "security",
        "value_type": "integer",
        "default_value": "5",
        "label": "Auto-logout after",
        "description": "Minutes of inactivity before automatic sign-out",
        "allowed_values": "[1,5,15,30]",
    },
]

PROFILE_CONFIG_KEYS = frozenset(
    {
        "currency",
        "month_start_day",
        "dark_mode",
        "week_start_monday",
        "round_up_savings",
        "digest_enabled",
        "sound_enabled",
    }
)

SECURITY_CONFIG_KEYS = frozenset(
    {
        "pin_lock_enabled",
        "fingerprint_login_enabled",
        "face_id_enabled",
        "password_protection_enabled",
        "hide_sensitive_amounts",
        "privacy_mode_enabled",
        "auto_lock_enabled",
        "cloud_backup_enabled",
        "local_backup_enabled",
        "e2e_encryption_enabled",
        "two_factor_enabled",
        "auto_logout_minutes",
    }
)

ALL_CONFIG_KEYS = PROFILE_CONFIG_KEYS | SECURITY_CONFIG_KEYS

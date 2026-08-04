"""Pydantic schemas for security settings and overview."""

import datetime as dt
import uuid

from pydantic import BaseModel, Field

AUTO_LOGOUT_OPTIONS = (1, 5, 15, 30)


class SecuritySettingsResponse(BaseModel):
    """User security & privacy configuration — maps to Security screen toggles."""

    pin_lock_enabled: bool
    fingerprint_login_enabled: bool
    face_id_enabled: bool
    password_protection_enabled: bool
    hide_sensitive_amounts: bool
    privacy_mode_enabled: bool
    auto_lock_enabled: bool
    cloud_backup_enabled: bool
    local_backup_enabled: bool
    e2e_encryption_enabled: bool
    two_factor_enabled: bool
    auto_logout_minutes: int
    vault_locked: bool


class SecuritySettingsUpdateRequest(BaseModel):
    pin_lock_enabled: bool | None = None
    fingerprint_login_enabled: bool | None = None
    face_id_enabled: bool | None = None
    password_protection_enabled: bool | None = None
    hide_sensitive_amounts: bool | None = None
    privacy_mode_enabled: bool | None = None
    auto_lock_enabled: bool | None = None
    cloud_backup_enabled: bool | None = None
    local_backup_enabled: bool | None = None
    e2e_encryption_enabled: bool | None = None
    two_factor_enabled: bool | None = None
    auto_logout_minutes: int | None = Field(default=None, ge=1, le=60)
    vault_locked: bool | None = None


class BackupStatusResponse(BaseModel):
    last_backup_at: dt.datetime | None
    last_backup_size_bytes: int | None
    encrypted: bool = True


class SessionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    device_label: str
    location: str | None
    ip: str | None
    user_agent: str | None
    last_active_at: dt.datetime
    is_current: bool


class SecurityEventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    event_type: str
    device_label: str
    detail: str | None
    created_at: dt.datetime


class LoginHistoryListResponse(BaseModel):
    """Paginated login / security-event history with optional date filters."""

    data: list[SecurityEventResponse]
    total: int
    page: int
    size: int
    pages: int
    from_date: dt.date | None = None
    to_date: dt.date | None = None


class SecurityOverviewResponse(BaseModel):
    """Full Security & Privacy screen payload."""

    settings: SecuritySettingsResponse
    backup: BackupStatusResponse
    sessions: list[SessionResponse]
    login_history: list[SecurityEventResponse]


class BackupResponse(BaseModel):
    filename: str
    size_bytes: int
    created_at: dt.datetime
    # JSON document the client can download / re-import.
    content: str = ""


class BackupImportRequest(BaseModel):
    """Client-uploaded backup JSON (same shape as `BackupResponse.content`)."""

    content: str = Field(min_length=2)

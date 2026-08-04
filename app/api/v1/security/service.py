"""Security settings, sessions, backup, and audit log service."""

import json
import uuid
from datetime import UTC, date, datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.assets import repository as assets_repo
from app.api.v1.auth.models import User
from app.api.v1.bills import repository as bills_repo
from app.api.v1.cards import repository as cards_repo
from app.api.v1.configuration.catalog import PROFILE_CONFIG_KEYS, SECURITY_CONFIG_KEYS
from app.api.v1.configuration import service as config_service
from app.api.v1.goals import repository as goals_repo
from app.api.v1.investments import repository as investments_repo
from app.api.v1.ledger import repository as ledger_repo
from app.api.v1.loans import repository as loans_repo
from app.api.v1.policies import repository as policies_repo
from app.api.v1.security import repository
from app.api.v1.security.schemas import (
    BackupResponse,
    BackupStatusResponse,
    LoginHistoryListResponse,
    SecurityEventResponse,
    SecurityOverviewResponse,
    SecuritySettingsResponse,
    SecuritySettingsUpdateRequest,
    SessionResponse,
)
from app.core.pagination import PageParams
from app.core.exceptions import NotFoundError, ValidationError


def _settings_from(user: User, values: dict[str, Any]) -> SecuritySettingsResponse:
    return SecuritySettingsResponse(
        pin_lock_enabled=bool(values["pin_lock_enabled"]),
        fingerprint_login_enabled=bool(values["fingerprint_login_enabled"]),
        face_id_enabled=bool(values["face_id_enabled"]),
        password_protection_enabled=bool(values["password_protection_enabled"]),
        hide_sensitive_amounts=bool(values["hide_sensitive_amounts"]),
        privacy_mode_enabled=bool(values["privacy_mode_enabled"]),
        auto_lock_enabled=bool(values["auto_lock_enabled"]),
        cloud_backup_enabled=bool(values["cloud_backup_enabled"]),
        local_backup_enabled=bool(values["local_backup_enabled"]),
        e2e_encryption_enabled=bool(values["e2e_encryption_enabled"]),
        two_factor_enabled=bool(values["two_factor_enabled"]),
        auto_logout_minutes=int(values["auto_logout_minutes"]),  # type: ignore[arg-type]
        vault_locked=user.vault_locked,
    )


def _device_label_from_request(request: Request) -> str:
    ua = request.headers.get("user-agent", "Unknown device")
    if "Mobile" in ua or "iPhone" in ua or "Android" in ua:
        return "Mobile · Paisa app"
    if "Chrome" in ua:
        return "Desktop · Chrome"
    if "Safari" in ua:
        return "Desktop · Safari"
    if "Firefox" in ua:
        return "Desktop · Firefox"
    return ua[:255]


async def _security_values(session: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
    return await config_service.get_resolved_subset(session, user_id, SECURITY_CONFIG_KEYS)


async def get_settings(session: AsyncSession, user: User) -> SecuritySettingsResponse:
    values = await _security_values(session, user.id)
    return _settings_from(user, values)


async def update_settings(
    session: AsyncSession, user: User, payload: SecuritySettingsUpdateRequest
) -> SecuritySettingsResponse:
    data = payload.model_dump(exclude_unset=True)

    if "vault_locked" in data:
        user.vault_locked = data.pop("vault_locked")

    config_updates = {k: v for k, v in data.items() if k in SECURITY_CONFIG_KEYS}
    values = await config_service.set_values(session, user.id, config_updates)
    await session.flush()
    return _settings_from(user, {k: values[k] for k in SECURITY_CONFIG_KEYS})


async def get_overview(session: AsyncSession, user: User) -> SecurityOverviewResponse:
    values = await _security_values(session, user.id)
    # Collapse historical duplicates from older login behaviour so the
    # Security screen reflects real devices, not every past sign-in.
    await repository.revoke_duplicate_user_agents(session, user.id)
    sessions = await repository.list_sessions(session, user.id)
    # Overview keeps a short recent slice; the Security screen uses the
    # dedicated paginated /login-history endpoint for the full list + filters.
    events, _total = await repository.list_security_events(session, user.id, limit=5, offset=0)
    return SecurityOverviewResponse(
        settings=_settings_from(user, values),
        backup=BackupStatusResponse(
            last_backup_at=user.last_backup_at,
            last_backup_size_bytes=user.last_backup_size_bytes,
            encrypted=True,
        ),
        sessions=[SessionResponse.model_validate(s) for s in sessions],
        login_history=[SecurityEventResponse.model_validate(e) for e in events],
    )


async def list_login_history(
    session: AsyncSession,
    user: User,
    params: PageParams,
    from_date: date | None,
    to_date: date | None,
) -> LoginHistoryListResponse:
    if from_date and to_date and from_date > to_date:
        raise ValidationError("from_date must be on or before to_date")

    events, total = await repository.list_security_events(
        session,
        user.id,
        limit=params.size,
        offset=params.offset,
        from_date=from_date,
        to_date=to_date,
    )
    pages = (total + params.size - 1) // params.size if total else 0
    return LoginHistoryListResponse(
        data=[SecurityEventResponse.model_validate(e) for e in events],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
        from_date=from_date,
        to_date=to_date,
    )


async def lock_vault(session: AsyncSession, user: User) -> SecuritySettingsResponse:
    user.vault_locked = True
    await session.flush()
    await repository.create_security_event(
        session,
        user_id=user.id,
        event_type="vault_locked",
        device_label="This device",
        detail="Vault locked manually",
    )
    values = await _security_values(session, user.id)
    return _settings_from(user, values)


async def record_login(
    session: AsyncSession, user: User, request: Request, location: str | None = None
) -> None:
    """Upsert a device session for this browser, then log a sign-in event.

    Each successful password login used to insert a brand-new session row.
    Logging out only bumped JWT credential_version and left those rows
    active — so one Chrome tab looked like three "trusted devices".
    """
    device = _device_label_from_request(request)
    user_agent = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    now = datetime.now(UTC)

    await repository.clear_current_flags(session, user.id)

    existing = await repository.find_open_session_by_user_agent(session, user.id, user_agent)
    if existing is not None:
        existing.device_label = device
        existing.location = location  # None when unknown — UI omits it
        existing.ip = ip
        existing.user_agent = user_agent
        existing.last_active_at = now
        existing.is_current = True
        existing.revoked_at = None
        await session.flush()
        # Drop any older duplicates for the same browser fingerprint.
        await repository.revoke_duplicate_user_agents(session, user.id)
        # Re-assert current after dedupe (dedupe may have touched flags).
        existing.is_current = True
        await session.flush()
    else:
        await repository.create_session(
            session,
            user_id=user.id,
            device_label=device,
            location=location,
            ip=ip,
            user_agent=user_agent,
            last_active_at=now,
            is_current=True,
        )

    await repository.create_security_event(
        session,
        user_id=user.id,
        event_type="sign_in",
        device_label=device,
        detail="Successful sign-in",
    )


async def record_logout(session: AsyncSession, user: User) -> None:
    """Revoke every open device session.

    Auth logout already invalidates all JWTs via credential_version, so
    leaving session rows around only confuses the Trusted devices list.
    """
    await repository.revoke_all_except(session, user.id, None)


async def record_password_change(session: AsyncSession, user: User, request: Request | None = None) -> None:
    device = _device_label_from_request(request) if request else "This device"
    # Password change bumps credential_version (all tokens die); clear stale devices.
    await repository.revoke_all_except(session, user.id, None)
    await repository.create_security_event(
        session,
        user_id=user.id,
        event_type="password_changed",
        device_label=device,
        detail="Password updated",
    )


async def list_sessions(session: AsyncSession, user_id: uuid.UUID) -> list[SessionResponse]:
    await repository.revoke_duplicate_user_agents(session, user_id)
    rows = await repository.list_sessions(session, user_id)
    return [SessionResponse.model_validate(r) for r in rows]


async def revoke_session(session: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID) -> None:
    s = await repository.get_session_by_id(session, session_id, user_id)
    if s is None:
        raise NotFoundError("Session not found")
    await repository.revoke_session(session, session_id, user_id)


async def revoke_all_sessions(
    session: AsyncSession, user_id: uuid.UUID, current_session_id: uuid.UUID | None = None
) -> None:
    await repository.revoke_all_except(session, user_id, current_session_id)


async def export_backup(session: AsyncSession, user: User) -> BackupResponse:
    user_id = user.id
    profile_values = await config_service.get_resolved_subset(session, user_id, PROFILE_CONFIG_KEYS)
    security_values = await _security_values(session, user_id)
    data = {
        "profile": {
            "name": user.name,
            "email": user.email,
            "currency": profile_values["currency"],
        },
        "security_settings": _settings_from(user, security_values).model_dump(),
        "goals": [g.name for g in await goals_repo.list_by_user(session, user_id)],
        "investments": [i.name for i in await investments_repo.list_by_user(session, user_id)],
        "loans": [l.name for l in await loans_repo.list_by_user(session, user_id)],
        "assets": [a.name for a in await assets_repo.list_by_user(session, user_id)],
        "bills": [b.name for b in await bills_repo.list_by_user(session, user_id)],
        "cards": [c.name for c in await cards_repo.list_by_user(session, user_id)],
        "policies": [p.name for p in await policies_repo.list_by_user(session, user_id)],
        "ledger": [e.person_name for e in await ledger_repo.list_by_user(session, user_id)],
    }
    content = json.dumps(data, indent=2)
    size = len(content.encode())
    filename = f"paisa-backup-{datetime.now(UTC).strftime('%Y%m%d')}.json"
    await repository.create_backup_record(
        session,
        user_id=user_id,
        filename=filename,
        size_bytes=size,
        storage_key=f"backup/{user_id}/{filename}",
    )
    user.last_backup_at = datetime.now(UTC)
    user.last_backup_size_bytes = size
    await session.flush()
    await repository.create_security_event(
        session,
        user_id=user_id,
        event_type="backup_completed",
        device_label="Cloud",
        detail=f"Encrypted · {size / 1024 / 1024:.1f} MB",
    )
    return BackupResponse(
        filename=filename,
        size_bytes=size,
        created_at=datetime.now(UTC),
        content=content,
    )


async def import_backup(session: AsyncSession, user: User, content: str) -> dict[str, str]:
    """Accept a previously exported backup JSON and restore profile/security toggles."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValidationError("Backup file is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ValidationError("Backup file has an unexpected shape")

    profile = data.get("profile") or {}
    if isinstance(profile, dict) and profile.get("name"):
        user.name = str(profile["name"])[:255]

    security = data.get("security_settings") or {}
    if isinstance(security, dict):
        config_updates = {
            key: security[key]
            for key in SECURITY_CONFIG_KEYS
            if key in security and key != "vault_locked"
        }
        if config_updates:
            await config_service.set_values(session, user.id, config_updates)

    size = len(content.encode())
    user.last_backup_at = datetime.now(UTC)
    user.last_backup_size_bytes = size
    await session.flush()
    await repository.create_security_event(
        session,
        user_id=user.id,
        event_type="backup_completed",
        device_label="Restore",
        detail="Settings restored from backup file",
    )
    return {"message": "Backup restored — profile and security settings applied"}

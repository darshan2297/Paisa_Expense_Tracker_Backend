"""Resolve and update user configuration values from the catalog."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.configuration import repository
from app.api.v1.configuration.catalog import ALL_CONFIG_KEYS, CONFIGURATION_DEFINITIONS
from app.api.v1.configuration.models import Configuration
from app.api.v1.configuration.values import parse_value, serialize_value
from app.core.exceptions import NotFoundError, ValidationError


async def seed_catalog(session: AsyncSession) -> int:
    """Idempotent — inserts catalog rows that do not exist yet. Returns insert count."""
    inserted = 0
    for definition in CONFIGURATION_DEFINITIONS:
        existing = await repository.get_by_key(session, definition["key"])
        if existing is None:
            session.add(Configuration(**definition))
            inserted += 1
    if inserted:
        await session.flush()
    return inserted


async def get_resolved_map(session: AsyncSession, user_id: uuid.UUID | str) -> dict[str, Any]:
    """Return `{key: typed_value}` merging catalog defaults with user overrides."""
    catalog = await repository.list_catalog(session)
    overrides = {
        row.configuration.key: row.value
        for row in await repository.list_user_values(session, user_id)
        if row.configuration is not None
    }

    resolved: dict[str, Any] = {}
    for option in catalog:
        raw = overrides.get(option.key, option.default_value)
        resolved[option.key] = parse_value(raw, option.value_type)
    return resolved


async def get_resolved_subset(
    session: AsyncSession, user_id: uuid.UUID | str, keys: frozenset[str]
) -> dict[str, Any]:
    full = await get_resolved_map(session, user_id)
    return {key: full[key] for key in keys if key in full}


async def set_values(
    session: AsyncSession, user_id: uuid.UUID | str, updates: dict[str, Any]
) -> dict[str, Any]:
    """Validate and persist user overrides; return the full resolved map."""
    if not updates:
        return await get_resolved_map(session, user_id)

    unknown = set(updates) - ALL_CONFIG_KEYS
    if unknown:
        raise NotFoundError(f"Unknown configuration keys: {', '.join(sorted(unknown))}")

    for key, value in updates.items():
        option = await repository.get_by_key(session, key)
        if option is None:
            raise NotFoundError(f"Configuration option '{key}' is not in the catalog")

        if option.allowed_values is not None:
            allowed = repository.parse_allowed_values(option.allowed_values)
            if value not in allowed:
                raise ValidationError(f"{key} must be one of {allowed}")

        serialized = serialize_value(value, option.value_type)
        await repository.upsert_user_value(session, user_id, option, serialized)

    await session.flush()
    return await get_resolved_map(session, user_id)


async def initialize_user_defaults(session: AsyncSession, user_id: uuid.UUID | str) -> None:
    """Create explicit user rows for every catalog option (using defaults)."""
    catalog = await repository.list_catalog(session)
    for option in catalog:
        existing = await repository.get_user_value(session, user_id, option.id)
        if existing is None:
            await repository.upsert_user_value(session, user_id, option, option.default_value)


async def build_profile_config(session: AsyncSession) -> dict[str, object]:
    """UI metadata derived from the catalog — no hard-coded option lists."""
    catalog = await repository.list_catalog(session)
    auto_logout = next((c for c in catalog if c.key == "auto_logout_minutes"), None)
    currency_opt = next((c for c in catalog if c.key == "currency"), None)

    auto_logout_options = (
        repository.parse_allowed_values(auto_logout.allowed_values) if auto_logout else [1, 5, 15, 30]
    )
    currencies = (
        repository.parse_allowed_values(currency_opt.allowed_values) if currency_opt else ["INR"]
    )

    return {
        "auto_logout_minutes_options": auto_logout_options,
        "month_start_day_min": 1,
        "month_start_day_max": 28,
        "currencies": currencies,
        "options": [
            {
                "key": option.key,
                "category": option.category,
                "value_type": option.value_type,
                "default_value": parse_value(option.default_value, option.value_type),
                "label": option.label,
                "description": option.description,
                "allowed_values": repository.parse_allowed_values(option.allowed_values),
            }
            for option in catalog
        ],
    }

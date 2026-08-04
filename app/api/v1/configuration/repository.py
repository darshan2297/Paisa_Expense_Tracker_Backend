"""Data access for configuration catalog and per-user values."""

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.configuration.models import Configuration, UserConfiguration


async def list_catalog(session: AsyncSession) -> list[Configuration]:
    result = await session.execute(select(Configuration).order_by(Configuration.category, Configuration.key))
    return list(result.scalars().all())


async def get_by_key(session: AsyncSession, key: str) -> Configuration | None:
    result = await session.execute(select(Configuration).where(Configuration.key == key))
    return result.scalar_one_or_none()


async def list_user_values(session: AsyncSession, user_id: uuid.UUID | str) -> list[UserConfiguration]:
    result = await session.execute(
        select(UserConfiguration)
        .where(UserConfiguration.user_id == user_id)
        .options(selectinload(UserConfiguration.configuration))
    )
    return list(result.scalars().all())


async def get_user_value(
    session: AsyncSession, user_id: uuid.UUID | str, configuration_id: uuid.UUID
) -> UserConfiguration | None:
    result = await session.execute(
        select(UserConfiguration).where(
            UserConfiguration.user_id == user_id,
            UserConfiguration.configuration_id == configuration_id,
        )
    )
    return result.scalar_one_or_none()


async def upsert_user_value(
    session: AsyncSession,
    user_id: uuid.UUID | str,
    configuration: Configuration,
    value: str,
) -> UserConfiguration:
    existing = await get_user_value(session, user_id, configuration.id)
    if existing is not None:
        existing.value = value
        await session.flush()
        return existing

    row = UserConfiguration(
        user_id=user_id,  # type: ignore[arg-type]
        configuration_id=configuration.id,
        value=value,
    )
    session.add(row)
    await session.flush()
    return row


def parse_allowed_values(raw: str | None) -> list[object] | None:
    if raw is None:
        return None
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValidationError("allowed_values must be a JSON array")
    return parsed

"""Data access for assets."""

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.assets.models import Asset, NetWorthSnapshot


async def list_by_user(session: AsyncSession, user_id: uuid.UUID) -> list[Asset]:
    result = await session.execute(
        select(Asset)
        .where(Asset.user_id == user_id, Asset.deleted_at.is_(None))
        .order_by(Asset.name)
    )
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, asset_id: uuid.UUID, user_id: uuid.UUID) -> Asset | None:
    result = await session.execute(
        select(Asset).where(
            Asset.id == asset_id, Asset.user_id == user_id, Asset.deleted_at.is_(None)
        )
    )
    return result.scalar_one_or_none()


async def create(session: AsyncSession, user_id: uuid.UUID, **kwargs: object) -> Asset:
    asset = Asset(user_id=user_id, **kwargs)
    session.add(asset)
    await session.flush()
    return asset


async def soft_delete(session: AsyncSession, asset: Asset) -> None:
    asset.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()


async def list_snapshots(
    session: AsyncSession, user_id: uuid.UUID, months: int
) -> list[NetWorthSnapshot]:
    result = await session.execute(
        select(NetWorthSnapshot)
        .where(NetWorthSnapshot.user_id == user_id)
        .order_by(NetWorthSnapshot.snapshot_date.desc())
        .limit(months)
    )
    return list(reversed(result.scalars().all()))


async def create_snapshot(session: AsyncSession, **kwargs: object) -> NetWorthSnapshot:
    snap = NetWorthSnapshot(**kwargs)
    session.add(snap)
    await session.flush()
    return snap

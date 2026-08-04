"""Business logic for assets."""

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.assets import repository
from app.api.v1.assets.models import Asset
from app.api.v1.assets.schemas import (
    AllocationItem,
    AssetCreateRequest,
    AssetResponse,
    AssetsSummaryResponse,
    AssetUpdateRequest,
)
from app.core.exceptions import NotFoundError


def _to_response(asset: Asset) -> AssetResponse:
    return AssetResponse.model_validate(asset)


async def list_assets(session: AsyncSession, user_id: uuid.UUID) -> list[AssetResponse]:
    rows = await repository.list_by_user(session, user_id)
    return [_to_response(r) for r in rows]


async def get_summary(session: AsyncSession, user_id: uuid.UUID) -> AssetsSummaryResponse:
    assets = await list_assets(session, user_id)
    total = sum((a.current_value for a in assets), Decimal("0"))
    by_kind: dict[str, Decimal] = {}
    for a in assets:
        by_kind[a.kind] = by_kind.get(a.kind, Decimal("0")) + a.current_value
    allocation = [
        AllocationItem(
            kind=k,
            amount=v,
            pct=round(float(v / total * 100), 1) if total else 0.0,
        )
        for k, v in sorted(by_kind.items())
    ]
    return AssetsSummaryResponse(
        total_value=total, count=len(assets), allocation=allocation, assets=assets
    )


async def create_asset(
    session: AsyncSession, user_id: uuid.UUID, payload: AssetCreateRequest
) -> AssetResponse:
    asset = await repository.create(session, user_id, **payload.model_dump())
    return _to_response(asset)


async def update_asset(
    session: AsyncSession, user_id: uuid.UUID, asset_id: uuid.UUID, payload: AssetUpdateRequest
) -> AssetResponse:
    asset = await repository.get_by_id(session, asset_id, user_id)
    if asset is None:
        raise NotFoundError("Asset not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
    await session.flush()
    return _to_response(asset)


async def delete_asset(session: AsyncSession, user_id: uuid.UUID, asset_id: uuid.UUID) -> None:
    asset = await repository.get_by_id(session, asset_id, user_id)
    if asset is None:
        raise NotFoundError("Asset not found")
    await repository.soft_delete(session, asset)

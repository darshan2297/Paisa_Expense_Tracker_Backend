"""HTTP layer for assets."""

import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.assets import service
from app.api.v1.assets.schemas import (
    AssetCreateRequest,
    AssetResponse,
    AssetsSummaryResponse,
    AssetUpdateRequest,
)
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

assets_router = APIRouter(prefix="/assets")


@assets_router.get("", summary="List assets")
@default_limit()
async def list_assets(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[AssetResponse]:
    return await service.list_assets(session, current_user.id)


@assets_router.get("/summary", summary="Assets summary")
@default_limit()
async def assets_summary(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> AssetsSummaryResponse:
    return await service.get_summary(session, current_user.id)


@assets_router.post("", status_code=201, summary="Create asset")
@default_limit()
async def create_asset(
    request: Request,
    payload: AssetCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> AssetResponse:
    return await service.create_asset(session, current_user.id, payload)


@assets_router.patch("/{asset_id}", summary="Update asset")
@default_limit()
async def update_asset(
    request: Request,
    asset_id: uuid.UUID,
    payload: AssetUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> AssetResponse:
    return await service.update_asset(session, current_user.id, asset_id, payload)


@assets_router.delete("/{asset_id}", status_code=204, summary="Delete asset")
@default_limit()
async def delete_asset(
    request: Request,
    asset_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_asset(session, current_user.id, asset_id)
    return Response(status_code=204)

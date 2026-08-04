"""HTTP layer for life dashboard."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dashboard import service
from app.api.v1.dashboard.schemas import LifeDashboardResponse
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

dashboard_router = APIRouter(prefix="/dashboard")
_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@dashboard_router.get("/life", summary="Life dashboard aggregation")
@default_limit()
async def life_dashboard(
    request: Request,
    current_user: CurrentUser,
    month: str = Query(pattern=_MONTH_PATTERN),
    session: AsyncSession = Depends(get_session),
) -> LifeDashboardResponse:
    return await service.get_life_dashboard(session, current_user, month)

"""HTTP layer for calendar and heatmap."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.calendar import service
from app.api.v1.calendar.schemas import CalendarResponse, HeatmapResponse
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

calendar_router = APIRouter()
_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@calendar_router.get("/calendar", summary="Cash-flow calendar for a month")
@default_limit()
async def get_calendar(
    request: Request,
    current_user: CurrentUser,
    month: str = Query(pattern=_MONTH_PATTERN),
    session: AsyncSession = Depends(get_session),
) -> CalendarResponse:
    return await service.get_calendar(session, current_user.id, month)


@calendar_router.get("/heatmap", summary="Spending heatmap")
@default_limit()
async def get_heatmap(
    request: Request,
    current_user: CurrentUser,
    weeks: int = Query(default=26, ge=1, le=52),
    session: AsyncSession = Depends(get_session),
) -> HeatmapResponse:
    return await service.get_heatmap(session, current_user.id, weeks)

"""HTTP layer for insights."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.insights import service
from app.api.v1.insights.schemas import HealthResponse, ReviewResponse, TrendsResponse
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

insights_router = APIRouter(prefix="/insights")
_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@insights_router.get("/health", summary="Financial health score")
@default_limit()
async def health_score(
    request: Request,
    current_user: CurrentUser,
    month: str = Query(pattern=_MONTH_PATTERN),
    session: AsyncSession = Depends(get_session),
) -> HealthResponse:
    return await service.get_health(session, current_user.id, month)


@insights_router.get("/trends", summary="Income vs expense trends")
@default_limit()
async def spending_trends(
    request: Request,
    current_user: CurrentUser,
    months: int = Query(default=6, ge=1, le=24),
    session: AsyncSession = Depends(get_session),
) -> TrendsResponse:
    return await service.get_trends(session, current_user.id, months)


@insights_router.get("/review", summary="Monthly financial review")
@default_limit()
async def monthly_review(
    request: Request,
    current_user: CurrentUser,
    month: str = Query(pattern=_MONTH_PATTERN),
    session: AsyncSession = Depends(get_session),
) -> ReviewResponse:
    return await service.get_review(session, current_user.id, month)

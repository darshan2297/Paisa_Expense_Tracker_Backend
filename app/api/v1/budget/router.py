"""HTTP layer for the budget module. Thin adapter only - no business logic,
no direct DB access. See docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.budget import service
from app.api.v1.budget.schemas import (
    BudgetSettingResponse,
    BudgetSettingUpdateRequest,
    BudgetSummaryResponse,
)
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

budget_router = APIRouter(prefix="/budget")

_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@budget_router.get("", summary="Get the current user's budget settings")
@default_limit()
async def get_budget(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BudgetSettingResponse:
    return await service.get_settings(session, current_user.id)


@budget_router.put("", summary="Create or update the current user's budget settings")
@default_limit()
async def update_budget(
    request: Request,
    payload: BudgetSettingUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BudgetSettingResponse:
    return await service.update_settings(session, current_user.id, payload)


@budget_router.get("/summary", summary="Budget-remaining math for a month")
@default_limit()
async def get_budget_summary(
    request: Request,
    current_user: CurrentUser,
    month: str = Query(pattern=_MONTH_PATTERN, description='"YYYY-MM"'),
    session: AsyncSession = Depends(get_session),
) -> BudgetSummaryResponse:
    return await service.get_summary(session, current_user.id, month)

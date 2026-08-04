"""Business logic for savings goals and emergency fund."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.goals import repository
from app.api.v1.goals.models import Goal
from app.api.v1.goals.schemas import (
    EmergencyFundResponse,
    GoalContributeRequest,
    GoalCreateRequest,
    GoalResponse,
    GoalSummaryResponse,
    GoalUpdateRequest,
    UpcomingContribution,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.deps import get_month_totals

_EMERGENCY_MONTHS_TARGET = 6
_EXPENSE_AVG_MONTHS = 3


def _to_response(goal: Goal) -> GoalResponse:
    return GoalResponse.model_validate(goal)


def _month_offset(month: str, delta: int) -> str:
    year, mon = (int(part) for part in month.split("-"))
    mon += delta
    while mon <= 0:
        mon += 12
        year -= 1
    while mon > 12:
        mon -= 12
        year += 1
    return f"{year:04d}-{mon:02d}"


async def _avg_monthly_expenses(session: AsyncSession, user_id: uuid.UUID) -> Decimal:
    today = dt.date.today()
    month = f"{today.year:04d}-{today.month:02d}"
    totals: list[Decimal] = []
    for i in range(_EXPENSE_AVG_MONTHS):
        m = _month_offset(month, -i)
        _income, expense = await get_month_totals(session, user_id, m)
        totals.append(expense)
    if not totals:
        return Decimal("0")
    return sum(totals, Decimal("0")) / len(totals)


async def list_goals(session: AsyncSession, user_id: uuid.UUID) -> list[GoalResponse]:
    goals = await repository.list_by_user(session, user_id)
    return [_to_response(g) for g in goals]


async def create_goal(
    session: AsyncSession, user_id: uuid.UUID, payload: GoalCreateRequest
) -> GoalResponse:
    if payload.saved_amount > payload.target_amount:
        raise ValidationError("Saved amount cannot exceed target")
    if payload.is_emergency:
        await repository.clear_emergency_flag(session, user_id)
    goal = await repository.create(
        session,
        user_id,
        name=payload.name,
        target_amount=payload.target_amount,
        saved_amount=payload.saved_amount,
        monthly_contribution=payload.monthly_contribution,
        is_emergency=payload.is_emergency,
        due_day=payload.due_day,
    )
    return _to_response(goal)


async def update_goal(
    session: AsyncSession, user_id: uuid.UUID, goal_id: uuid.UUID, payload: GoalUpdateRequest
) -> GoalResponse:
    goal = await repository.get_by_id(session, goal_id, user_id)
    if goal is None:
        raise NotFoundError("Goal not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    if goal.saved_amount > goal.target_amount:
        raise ValidationError("Saved amount cannot exceed target")
    await session.flush()
    return _to_response(goal)


async def delete_goal(session: AsyncSession, user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
    goal = await repository.get_by_id(session, goal_id, user_id)
    if goal is None:
        raise NotFoundError("Goal not found")
    await repository.soft_delete(session, goal)


async def contribute(
    session: AsyncSession, user_id: uuid.UUID, goal_id: uuid.UUID, payload: GoalContributeRequest
) -> GoalResponse:
    goal = await repository.get_by_id(session, goal_id, user_id)
    if goal is None:
        raise NotFoundError("Goal not found")
    goal.saved_amount = min(goal.saved_amount + payload.amount, goal.target_amount)
    await session.flush()
    return _to_response(goal)


async def get_emergency_fund(session: AsyncSession, user_id: uuid.UUID) -> EmergencyFundResponse:
    goal = await repository.get_emergency(session, user_id)
    avg_expense = await _avg_monthly_expenses(session, user_id)
    target = (avg_expense * _EMERGENCY_MONTHS_TARGET).quantize(Decimal("0.01"))
    saved = goal.saved_amount if goal else Decimal("0")
    months_covered = float(saved / avg_expense) if avg_expense else 0.0
    pct = float(saved / target * 100) if target else 0.0
    return EmergencyFundResponse(
        goal_id=goal.id if goal else None,
        saved=saved,
        target=target if goal else target,
        monthly_expense_avg=avg_expense.quantize(Decimal("0.01")),
        months_of_expenses_covered=round(months_covered, 1),
        pct_complete=round(pct, 1),
    )


async def get_summary(session: AsyncSession, user_id: uuid.UUID) -> GoalSummaryResponse:
    goals = await repository.list_by_user(session, user_id)
    total_saved = sum((g.saved_amount for g in goals), Decimal("0"))
    emergency = next((g for g in goals if g.is_emergency), None)
    upcoming: list[UpcomingContribution] = []
    for g in goals:
        if g.monthly_contribution > 0:
            upcoming.append(
                UpcomingContribution(
                    goal_id=g.id,
                    goal_name=g.name,
                    amount=g.monthly_contribution,
                    due_day=g.due_day,
                )
            )
    return GoalSummaryResponse(
        total_saved=total_saved,
        active_count=len(goals),
        emergency_saved=emergency.saved_amount if emergency else Decimal("0"),
        next_contributions=upcoming,
    )

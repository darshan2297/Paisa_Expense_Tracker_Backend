"""Business logic for investments."""

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.investments import repository
from app.api.v1.investments.models import Investment
from app.api.v1.investments.schemas import (
    AllocationItem,
    InvestmentCreateRequest,
    InvestmentResponse,
    InvestmentUpdateRequest,
    InvestmentsSummaryResponse,
    UpdateValueRequest,
)
from app.core.exceptions import NotFoundError


def _to_response(inv: Investment) -> InvestmentResponse:
    return InvestmentResponse.model_validate(inv)


async def list_investments(session: AsyncSession, user_id: uuid.UUID) -> list[InvestmentResponse]:
    rows = await repository.list_by_user(session, user_id)
    return [_to_response(r) for r in rows]


async def get_summary(session: AsyncSession, user_id: uuid.UUID) -> InvestmentsSummaryResponse:
    investments = await list_investments(session, user_id)
    total_invested = sum((i.invested_amount for i in investments), Decimal("0"))
    portfolio_total = sum((i.current_value for i in investments), Decimal("0"))
    total_gain = portfolio_total - total_invested
    gain_pct = float(total_gain / total_invested * 100) if total_invested else 0.0
    monthly_sip = sum((i.monthly_sip for i in investments), Decimal("0"))

    by_kind: dict[str, Decimal] = {}
    for i in investments:
        by_kind[i.kind] = by_kind.get(i.kind, Decimal("0")) + i.current_value
    allocation = [
        AllocationItem(
            kind=k,
            amount=v,
            pct=round(float(v / portfolio_total * 100), 1) if portfolio_total else 0.0,
        )
        for k, v in sorted(by_kind.items())
    ]

    return InvestmentsSummaryResponse(
        portfolio_total=portfolio_total,
        total_invested=total_invested,
        total_gain=total_gain,
        gain_pct=round(gain_pct, 1),
        monthly_sip_total=monthly_sip,
        allocation=allocation,
        investments=investments,
    )


async def create_investment(
    session: AsyncSession, user_id: uuid.UUID, payload: InvestmentCreateRequest
) -> InvestmentResponse:
    inv = await repository.create(session, user_id, **payload.model_dump())
    return _to_response(inv)


async def update_investment(
    session: AsyncSession, user_id: uuid.UUID, investment_id: uuid.UUID, payload: InvestmentUpdateRequest
) -> InvestmentResponse:
    inv = await repository.get_by_id(session, investment_id, user_id)
    if inv is None:
        raise NotFoundError("Investment not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inv, field, value)
    await session.flush()
    return _to_response(inv)


async def update_value(
    session: AsyncSession, user_id: uuid.UUID, investment_id: uuid.UUID, payload: UpdateValueRequest
) -> InvestmentResponse:
    inv = await repository.get_by_id(session, investment_id, user_id)
    if inv is None:
        raise NotFoundError("Investment not found")
    inv.current_value = payload.current_value
    await session.flush()
    return _to_response(inv)


async def delete_investment(session: AsyncSession, user_id: uuid.UUID, investment_id: uuid.UUID) -> None:
    inv = await repository.get_by_id(session, investment_id, user_id)
    if inv is None:
        raise NotFoundError("Investment not found")
    await repository.soft_delete(session, inv)

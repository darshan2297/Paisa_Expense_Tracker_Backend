"""Net worth aggregation service."""

import datetime as dt
import json
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.assets import repository as assets_repo
from app.api.v1.assets import service as assets_service
from app.api.v1.cards import service as cards_service
from app.api.v1.goals import repository as goals_repo
from app.api.v1.investments import service as investments_service
from app.api.v1.ledger import service as ledger_service
from app.api.v1.loans import service as loans_service
from app.api.v1.net_worth.schemas import (
    NetWorthCurrentResponse,
    NetWorthHistoryPoint,
    NetWorthHistoryResponse,
    NetWorthPart,
)
from app.api.v1.transactions import service as transactions_service


async def _compute_totals(
    session: AsyncSession, user_id: uuid.UUID
) -> tuple[Decimal, Decimal, list[NetWorthPart]]:
    inv_summary = await investments_service.get_summary(session, user_id)
    assets_summary = await assets_service.get_summary(session, user_id)
    goals = await goals_repo.list_by_user(session, user_id)
    goals_saved = sum((g.saved_amount for g in goals), Decimal("0"))
    loans = await loans_service.list_loans(session, user_id)
    loan_outstanding = sum((loan.outstanding for loan in loans), Decimal("0"))
    cards_summary = await cards_service.get_summary(session, user_id)

    # Net worth previously counted everything the user OWES (loans, card
    # outstanding) but omitted the cash they actually HOLD - every account's
    # balance is derived from transactions, never stored (see
    # docs/DATABASE_STANDARDS.md's money-column convention), so it must be
    # summed here the same way `transactions.get_month_totals` sums a single
    # month, just across all time. Ledger receivables/payables (money lent
    # or borrowed via the People feature) were omitted entirely too - both
    # are real components of net worth, not optional extras.
    income_total, expense_total = await transactions_service.get_all_time_totals(session, user_id)
    net_cash = income_total - expense_total
    people_balances = await ledger_service.list_people_balances(session, user_id)
    net_receivables = sum((p.net_balance for p in people_balances), Decimal("0"))

    portfolio = inv_summary.portfolio_total
    physical_assets = assets_summary.total_value
    cash_goals = net_cash + goals_saved
    liabilities = loan_outstanding + cards_summary.total_outstanding

    total_assets = portfolio + physical_assets + cash_goals + net_receivables

    parts = [
        NetWorthPart(label="Portfolio", value=portfolio),
        NetWorthPart(label="Assets", value=physical_assets),
        NetWorthPart(label="Cash & goals", value=cash_goals),
        NetWorthPart(label="Receivables", value=net_receivables),
        NetWorthPart(label="Liabilities", value=liabilities),
    ]
    return total_assets, liabilities, parts


async def get_current(session: AsyncSession, user_id: uuid.UUID) -> NetWorthCurrentResponse:
    total_assets, liabilities, parts = await _compute_totals(session, user_id)
    net_worth = total_assets - liabilities

    snapshots = await assets_repo.list_snapshots(session, user_id, 2)
    delta_month = None
    if len(snapshots) >= 1:
        delta_month = net_worth - snapshots[-1].net_worth

    return NetWorthCurrentResponse(
        net_worth=net_worth,
        total_assets=total_assets,
        total_liabilities=liabilities,
        delta_month=delta_month,
        parts=parts,
    )


async def get_history(
    session: AsyncSession, user_id: uuid.UUID, months: int
) -> NetWorthHistoryResponse:
    snapshots = await assets_repo.list_snapshots(session, user_id, months)
    points = [
        NetWorthHistoryPoint(
            date=s.snapshot_date,
            net_worth=s.net_worth,
            total_assets=s.total_assets,
            total_liabilities=s.total_liabilities,
        )
        for s in snapshots
    ]
    return NetWorthHistoryResponse(points=points)


async def create_snapshot(session: AsyncSession, user_id: uuid.UUID) -> NetWorthCurrentResponse:
    total_assets, liabilities, parts = await _compute_totals(session, user_id)
    net_worth = total_assets - liabilities
    breakdown = {p.label: str(p.value) for p in parts}
    await assets_repo.create_snapshot(
        session,
        user_id=user_id,
        snapshot_date=dt.date.today(),
        total_assets=total_assets,
        total_liabilities=liabilities,
        net_worth=net_worth,
        breakdown_json=json.dumps(breakdown),
    )
    return NetWorthCurrentResponse(
        net_worth=net_worth,
        total_assets=total_assets,
        total_liabilities=liabilities,
        delta_month=None,
        parts=parts,
    )

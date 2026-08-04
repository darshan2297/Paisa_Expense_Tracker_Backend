"""Life dashboard aggregation service."""

import calendar
import datetime as dt
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.assets import service as assets_service
from app.api.v1.auth.models import User
from app.api.v1.bills import repository as bills_repo
from app.api.v1.budget import service as budget_service
from app.api.v1.dashboard.schemas import (
    ActivityItem,
    ForecastData,
    GoalProgress,
    LifeDashboardResponse,
    LifeMetric,
    NetWorthPart,
    UpcomingItem,
)
from app.api.v1.goals import repository as goals_repo
from app.api.v1.goals import service as goals_service
from app.api.v1.investments import service as investments_service
from app.api.v1.loans import service as loans_service
from app.api.v1.net_worth import service as net_worth_service
from app.api.v1.policies import repository as policies_repo
from app.api.v1.transactions import repository as txn_repo
from app.api.v1.transactions.service import get_month_totals
from app.deps import list_categories


async def get_life_dashboard(
    session: AsyncSession, user: User, month: str
) -> LifeDashboardResponse:
    user_id = user.id
    income, expense = await get_month_totals(session, user_id, month)
    budget_summary = await budget_service.get_summary(session, user_id, month)
    nw = await net_worth_service.get_current(session, user_id)
    inv = await investments_service.get_summary(session, user_id)
    assets = await assets_service.get_summary(session, user_id)
    loans = await loans_service.get_summary(session, user_id, month)
    emergency = await goals_service.get_emergency_fund(session, user_id)
    goals = await goals_repo.list_by_user(session, user_id)

    budget = budget_summary.monthly_amount
    budget_left = budget_summary.remaining
    budget_used_pct = 100 - budget_summary.pct_remaining if budget else 0
    budget_over = budget_left < 0

    year, mon = (int(part) for part in month.split("-"))
    days_in_month = calendar.monthrange(year, mon)[1]
    today = dt.date.today()
    if (today.year, today.month) == (year, mon):
        days_elapsed = max(1, today.day)
        days_remaining = days_in_month - today.day + 1
    else:
        days_elapsed = days_in_month
        days_remaining = 1
    daily_rate = expense / days_elapsed if days_elapsed else Decimal("0")
    predicted = daily_rate * days_in_month
    expected_savings = income - predicted
    safe_daily = budget_left / days_remaining if days_remaining and budget_left > 0 else Decimal("0")

    cats = await list_categories(session)
    cat_by_id = {c.id: c for c in cats}
    recent_txns = await txn_repo.list_recent(session, user_id, month, limit=4)
    recent = []
    for t in recent_txns:
        cat = cat_by_id.get(t.category_id)
        recent.append(
            ActivityItem(
                id=str(t.id),
                title=cat.name if cat else "Transaction",
                sub=f"{t.date.strftime('%b %d')} · {t.note or ''}".strip(),
                amount=f"{'+' if t.type == 'income' else '−'}₹{t.amount}",
                initial=(cat.name[0] if cat else "T").upper(),
            )
        )

    upcoming: list[UpcomingItem] = []
    for g in goals:
        if g.monthly_contribution > 0:
            upcoming.append(
                UpcomingItem(
                    id=str(g.id),
                    label=g.name,
                    sub="Goal · monthly",
                    amount=f"₹{g.monthly_contribution}",
                )
            )
    for bill in await bills_repo.list_by_user(session, user_id):
        if bill.paid_on is None:
            upcoming.append(
                UpcomingItem(
                    id=str(bill.id),
                    label=bill.name,
                    sub="Bill",
                    amount=f"₹{bill.amount}",
                )
            )
    for policy in await policies_repo.list_by_user(session, user_id):
        upcoming.append(
            UpcomingItem(
                id=str(policy.id),
                label=policy.name,
                sub="Insurance",
                amount=f"₹{policy.premium}",
            )
        )

    goal_progress = [
        GoalProgress(
            id=str(g.id),
            name=g.name,
            pct=round(float(g.saved_amount / g.target_amount * 100), 1) if g.target_amount else 0,
        )
        for g in goals[:4]
    ]

    savings_rate = ((income - expense) / income * 100) if income else 0
    cash_total = sum(
        (item.amount for item in assets.allocation if item.kind in ("BANK", "CASH")),
        Decimal("0"),
    )
    gain_sign = "+" if inv.total_gain >= 0 else "−"
    life_tiles = [
        LifeMetric(label="Monthly income", value=f"₹{income}", sub="credited this month"),
        LifeMetric(
            label="Monthly expenses",
            value=f"₹{expense}",
            sub=f"{budget_used_pct:.0f}% of budget",
        ),
        LifeMetric(label="Saved this month", value=f"₹{income - expense}", sub=f"{savings_rate:.0f}% savings rate"),
        LifeMetric(
            label="Portfolio value",
            value=f"₹{inv.portfolio_total}",
            sub=f"{gain_sign}₹{abs(inv.total_gain)} overall",
        ),
        LifeMetric(label="Bank & cash", value=f"₹{cash_total}", sub="liquid right now"),
        LifeMetric(label="Assets", value=f"₹{assets.total_value}", sub=f"{assets.count} tracked"),
        LifeMetric(label="Loan outstanding", value=f"₹{loans.total_outstanding}", sub=f"{loans.active_count} active loans"),
        LifeMetric(
            label="Emergency fund",
            value=f"{emergency.months_of_expenses_covered:.1f} mo",
            sub=f"₹{emergency.saved} set aside",
        ),
    ]

    alert_title = ""
    alert_body = ""
    if budget_over:
        over_by = abs(budget_left)
        alert_title = f"Budget exceeded by ₹{over_by}"
        alert_body = f"You have spent ₹{expense} against a ₹{budget} limit this month."

    return LifeDashboardResponse(
        user_name=user.name or "User",
        month=month,
        net_worth=nw.net_worth,
        net_worth_delta=nw.delta_month,
        nw_parts=[NetWorthPart(label=p.label, value=p.value) for p in nw.parts],
        budget=budget,
        budget_left=budget_left,
        budget_used_pct=round(budget_used_pct, 1),
        budget_over=budget_over,
        show_budget_alert=budget_over,
        alert_title=alert_title,
        alert_body=alert_body,
        forecast=ForecastData(
            predicted=predicted.quantize(Decimal("0.01")),
            spent=expense,
            budget=budget,
            over_budget=predicted > budget,
            safe_daily=safe_daily.quantize(Decimal("0.01")),
            expected_savings=expected_savings.quantize(Decimal("0.01")),
            note=f"At this pace you will finish ₹{max(predicted - budget, Decimal('0'))} over budget."
            if predicted > budget
            else "On track to stay within budget.",
        ),
        life_tiles=life_tiles,
        recent=recent,
        upcoming=upcoming[:4],
        goals=goal_progress,
        reminder_count=len(upcoming),
    )

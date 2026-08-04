"""Insights, health score, and monthly review service."""

import datetime as dt
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.budget import service as budget_service
from app.api.v1.goals import service as goals_service
from app.api.v1.insights.schemas import (
    CategoryBar,
    HealthMetric,
    HealthResponse,
    InsightCard,
    ReviewResponse,
    ReviewRow,
    TrendMonth,
    TrendsResponse,
)
from app.api.v1.investments import service as investments_service
from app.api.v1.loans import service as loans_service
from app.api.v1.net_worth import service as net_worth_service
from app.api.v1.transactions import repository as txn_repo
from app.api.v1.transactions.service import get_month_totals
from app.deps import list_categories


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


def _rupees(amount: Decimal | float | int) -> str:
    """Whole-rupee mockup `fmt` / `signed` style (no decimals)."""
    return f"₹{int(round(float(amount)))}"


def _signed(amount: Decimal | float | int) -> str:
    n = float(amount)
    return f"−{_rupees(abs(n))}" if n < 0 else _rupees(n)


def _status_ge(value: float, good: float, ok: float) -> tuple[str, int]:
    """Mockup `status(v, good, ok)` — higher is better."""
    if value >= good:
        return "Healthy", 85
    if value >= ok:
        return "Watch", 55
    return "Needs work", 25


def _status_le(value: float, good: float, ok: float) -> tuple[str, int]:
    """Mockup `statusInv(v, good, ok)` — lower is better."""
    if value <= good:
        return "Healthy", 85
    if value <= ok:
        return "Watch", 55
    return "Needs work", 25


async def get_health(session: AsyncSession, user_id, month: str) -> HealthResponse:
    """Eight health cards — labels/copy/thresholds match design HTML `healthCards`."""
    income, expense = await get_month_totals(session, user_id, month)
    budget_summary = await budget_service.get_summary(session, user_id, month)
    emergency = await goals_service.get_emergency_fund(session, user_id)
    goals = await goals_service.list_goals(session, user_id)
    inv_summary = await investments_service.get_summary(session, user_id)
    loans_summary = await loans_service.get_summary(session, user_id, month)
    nw = await net_worth_service.get_current(session, user_id)

    savings_rate = float((income - expense) / income * 100) if income else 0.0
    inv_rate = float(inv_summary.monthly_sip_total / income * 100) if income else 0.0
    budget_util = float(100 - budget_summary.pct_remaining) if budget_summary.monthly_amount else 0.0
    ef_months = float(emergency.months_of_expenses_covered)
    debt_ratio = float(loans_summary.debt_to_income_pct)
    cashflow = income - expense

    if goals:
        goal_progress = (
            sum(
                min(1.0, float(g.saved_amount / g.target_amount)) if g.target_amount > 0 else 0.0
                for g in goals
            )
            / len(goals)
            * 100
        )
    else:
        goal_progress = 0.0

    # Mockup: (nwNow - nwPrev) / |nwPrev| * 100 when a prior snapshot exists.
    if nw.delta_month is not None and nw.net_worth - nw.delta_month != 0:
        nw_prev = nw.net_worth - nw.delta_month
        nw_growth = float(nw.delta_month / abs(nw_prev) * 100)
    else:
        nw_growth = 0.0

    has_budget = bool(budget_summary.monthly_amount and budget_summary.monthly_amount > 0)
    has_income = bool(income and income > 0)
    has_debt_signal = has_income or debt_ratio > 0

    sav_status, sav_score = _status_ge(savings_rate, 20, 10)
    inv_status, inv_score = _status_ge(inv_rate, 15, 8)
    # Unset budget is not "perfect utilisation" — only score once a limit exists.
    if has_budget:
        bud_status, bud_score = _status_le(budget_util, 85, 100)
    else:
        bud_status, bud_score = "Needs work", 25
    ef_status, ef_score = _status_ge(ef_months, 6, 3)
    # No income and no EMIs → neutral/healthy card, but do not inflate composite.
    if has_debt_signal:
        debt_status, debt_score = _status_le(debt_ratio, 35, 45)
    else:
        debt_status, debt_score = "Healthy", 85
    cf_status, cf_score = _status_ge(float(cashflow), 1, 0)
    goal_status, goal_score = _status_ge(goal_progress, 60, 30)
    nw_status, nw_score = _status_ge(nw_growth, 1, 0)

    metrics = [
        HealthMetric(
            label="Savings rate",
            value=f"{round(savings_rate)}%",
            trend=f"{'Above' if savings_rate >= 20 else 'Below'} the 20% mark",
            status=sav_status,
            score=sav_score,
        ),
        HealthMetric(
            label="Investment rate",
            value=f"{inv_rate:.1f}%",
            trend=f"{_rupees(inv_summary.monthly_sip_total)} invested monthly",
            status=inv_status,
            score=inv_score,
        ),
        HealthMetric(
            label="Budget utilisation",
            value=f"{round(budget_util)}%",
            trend=(
                f"{_rupees(budget_summary.spent)} of {_rupees(budget_summary.monthly_amount)}"
                if has_budget
                else "No monthly budget set"
            ),
            status=bud_status,
            score=bud_score,
        ),
        HealthMetric(
            label="Emergency fund",
            value=f"{ef_months:.1f} mo",
            trend="Target 6 months of expenses",
            status=ef_status,
            score=ef_score,
        ),
        HealthMetric(
            label="Debt ratio",
            value=f"{round(debt_ratio)}%",
            trend="EMIs against monthly income",
            status=debt_status,
            score=debt_score,
        ),
        HealthMetric(
            label="Monthly cash flow",
            value=_signed(cashflow),
            trend="Income minus everything spent",
            status=cf_status,
            score=cf_score,
        ),
        HealthMetric(
            label="Goal progress",
            value=f"{round(goal_progress)}%",
            trend=f"{len(goals)} goals being funded",
            status=goal_status,
            score=goal_score,
        ),
        HealthMetric(
            label="Net worth growth",
            value=f"{nw_growth:+.1f}%",
            trend="Compared with last month",
            status=nw_status,
            score=nw_score,
        ),
    ]
    # Mockup `healthScore` — average of six core levers (not all eight cards).
    # Empty / unset levers contribute 0, not a free 100. Otherwise a brand-new
    # account (₹0 everywhere) scored 33 from "perfect" zero budget + zero debt.
    budget_component = max(0.0, 100.0 - budget_util) if has_budget else 0.0
    debt_component = max(0.0, 100.0 - debt_ratio * 2) if has_debt_signal else 0.0
    composite = int(
        round(
            (
                min(100.0, savings_rate * 2.5)
                + min(100.0, inv_rate * 5)
                + budget_component
                + min(100.0, ef_months / 6 * 100)
                + debt_component
                + goal_progress
            )
            / 6
        )
    )
    return HealthResponse(composite_score=composite, metrics=metrics)


async def get_trends(session: AsyncSession, user_id, months: int) -> TrendsResponse:
    today = dt.date.today()
    month = f"{today.year:04d}-{today.month:02d}"
    trend_months: list[TrendMonth] = []
    for i in range(months - 1, -1, -1):
        m = _month_offset(month, -i)
        income, expense = await get_month_totals(session, user_id, m)
        label = dt.date(int(m[:4]), int(m[5:7]), 1).strftime("%b")
        trend_months.append(TrendMonth(label=label, income=income, expense=expense))

    cur_income, cur_expense = await get_month_totals(session, user_id, month)
    prev_income, prev_expense = await get_month_totals(session, user_id, _month_offset(month, -1))
    mom = ((cur_expense - prev_expense) / prev_expense * 100) if prev_expense else 0

    insights = [
        InsightCard(label="Month over month", value=f"{mom:+.0f}%", sub="Spending vs last month"),
        InsightCard(
            label="Savings trend",
            value=f"{((cur_income - cur_expense) / cur_income * 100) if cur_income else 0:.0f}%",
            sub="This month",
        ),
    ]
    return TrendsResponse(months=trend_months, insights=insights)


async def get_review(session: AsyncSession, user_id, month: str) -> ReviewResponse:
    income, expense = await get_month_totals(session, user_id, month)
    prev_income, prev_expense = await get_month_totals(session, user_id, _month_offset(month, -1))
    budget_summary = await budget_service.get_summary(session, user_id, month)
    nw = await net_worth_service.get_current(session, user_id)
    loans_summary = await loans_service.get_summary(session, user_id, month)

    cats = await list_categories(session)
    cat_by_id = {c.id: c for c in cats}
    category_sums = await txn_repo.sum_expense_by_category(session, user_id, month)
    category_bars = []
    for cat_id, amount in category_sums:
        cat = cat_by_id.get(cat_id)
        pct = float(amount / expense * 100) if expense else 0
        category_bars.append(
            CategoryBar(name=cat.name if cat else "Unknown", amount=amount, pct=round(pct, 1))
        )

    income_delta = ((income - prev_income) / prev_income * 100) if prev_income else 0
    expense_delta = ((expense - prev_expense) / prev_expense * 100) if prev_expense else 0

    rows = [
        ReviewRow(label="Income", value=f"₹{income}", delta=f"{income_delta:+.0f}% vs last month"),
        ReviewRow(label="Expenses", value=f"₹{expense}", delta=f"{expense_delta:+.0f}% vs last month"),
        ReviewRow(label="Saved", value=f"+₹{income - expense}", delta=""),
        ReviewRow(
            label="Net worth change",
            value=f"+₹{nw.delta_month}" if nw.delta_month else "—",
            delta="",
        ),
        ReviewRow(label="Loan & EMI payments", value=f"₹{loans_summary.total_emi}", delta=""),
    ]

    narrative = (
        f"In {month}, you earned ₹{income} and spent ₹{expense}. "
        f"Your budget was {budget_summary.pct_remaining:.0f}% remaining."
    )

    highlights = [
        InsightCard(
            label="Budget performance",
            value=f"{100 - budget_summary.pct_remaining:.0f}% used",
            sub=f"₹{budget_summary.spent} spent",
        ),
    ]

    return ReviewResponse(
        month=month,
        narrative=narrative,
        rows=rows,
        highlights=highlights,
        category_bars=category_bars,
    )

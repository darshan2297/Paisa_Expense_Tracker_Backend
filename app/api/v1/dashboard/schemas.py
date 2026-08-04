"""Life dashboard aggregation schemas."""

from decimal import Decimal

from pydantic import BaseModel


class NetWorthPart(BaseModel):
    label: str
    value: Decimal


class LifeMetric(BaseModel):
    label: str
    value: str
    sub: str


class ActivityItem(BaseModel):
    id: str
    title: str
    sub: str
    amount: str
    initial: str


class UpcomingItem(BaseModel):
    id: str
    label: str
    sub: str
    amount: str


class GoalProgress(BaseModel):
    id: str
    name: str
    pct: float


class ForecastData(BaseModel):
    predicted: Decimal
    spent: Decimal
    budget: Decimal
    over_budget: bool
    safe_daily: Decimal
    expected_savings: Decimal
    note: str


class LifeDashboardResponse(BaseModel):
    user_name: str
    month: str
    net_worth: Decimal
    net_worth_delta: Decimal | None
    nw_parts: list[NetWorthPart]
    budget: Decimal
    budget_left: Decimal
    budget_used_pct: float
    budget_over: bool
    show_budget_alert: bool
    alert_title: str
    alert_body: str
    forecast: ForecastData
    life_tiles: list[LifeMetric]
    recent: list[ActivityItem]
    upcoming: list[UpcomingItem]
    goals: list[GoalProgress]
    reminder_count: int

"""Pydantic schemas for insights."""

from decimal import Decimal

from pydantic import BaseModel


class HealthMetric(BaseModel):
    label: str
    value: str
    trend: str
    status: str
    score: int


class HealthResponse(BaseModel):
    composite_score: int
    metrics: list[HealthMetric]


class TrendMonth(BaseModel):
    label: str
    income: Decimal
    expense: Decimal


class InsightCard(BaseModel):
    label: str
    value: str
    sub: str


class TrendsResponse(BaseModel):
    months: list[TrendMonth]
    insights: list[InsightCard]


class ReviewRow(BaseModel):
    label: str
    value: str
    delta: str


class CategoryBar(BaseModel):
    name: str
    amount: Decimal
    pct: float


class ReviewResponse(BaseModel):
    month: str
    narrative: str
    rows: list[ReviewRow]
    highlights: list[InsightCard]
    category_bars: list[CategoryBar]

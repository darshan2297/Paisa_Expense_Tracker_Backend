"""Pydantic v2 request/response schemas for the budget module."""

from decimal import Decimal

from pydantic import BaseModel, Field


class BudgetSettingResponse(BaseModel):
    model_config = {"from_attributes": True}

    monthly_amount: Decimal
    alert_pct: int
    reminder_lead_days: int


class BudgetSettingUpdateRequest(BaseModel):
    """Full-replacement PUT payload - matches the design's `budgetPresets`/
    `leadOptions` allowed ranges.
    """

    monthly_amount: Decimal = Field(ge=0)
    alert_pct: int = Field(ge=5, le=60)
    reminder_lead_days: int = Field(ge=1, le=45)


class BudgetSummaryResponse(BaseModel):
    monthly_amount: Decimal
    spent: Decimal
    remaining: Decimal
    pct_remaining: float
    per_day_left: Decimal
    days_remaining_in_month: int
    alert_triggered: bool
    over_by: Decimal

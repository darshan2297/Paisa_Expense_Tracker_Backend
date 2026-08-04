"""Pydantic schemas for the goals module."""

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field


class GoalResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    target_amount: Decimal
    saved_amount: Decimal
    monthly_contribution: Decimal
    is_emergency: bool
    due_day: int | None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def remaining(self) -> Decimal:
        return max(self.target_amount - self.saved_amount, Decimal("0"))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pct_complete(self) -> float:
        if self.target_amount <= 0:
            return 0.0
        return round(float(self.saved_amount / self.target_amount * 100), 1)


class GoalCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    target_amount: Decimal = Field(gt=0)
    saved_amount: Decimal = Field(ge=0, default=Decimal("0"))
    monthly_contribution: Decimal = Field(ge=0, default=Decimal("0"))
    is_emergency: bool = False
    due_day: int | None = Field(default=None, ge=1, le=28)


class GoalUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    target_amount: Decimal | None = Field(default=None, gt=0)
    monthly_contribution: Decimal | None = Field(default=None, ge=0)
    due_day: int | None = Field(default=None, ge=1, le=28)


class GoalContributeRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    note: str | None = None


class GoalSummaryResponse(BaseModel):
    total_saved: Decimal
    active_count: int
    emergency_saved: Decimal
    next_contributions: list["UpcomingContribution"]


class UpcomingContribution(BaseModel):
    goal_id: uuid.UUID
    goal_name: str
    amount: Decimal
    due_day: int | None


class EmergencyFundResponse(BaseModel):
    goal_id: uuid.UUID | None
    saved: Decimal
    target: Decimal
    monthly_expense_avg: Decimal
    months_of_expenses_covered: float
    pct_complete: float


GoalSummaryResponse.model_rebuild()

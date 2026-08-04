"""Pydantic schemas for investments."""

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field

INVESTMENT_KINDS = ("SIP", "PPF", "STK", "GOLD", "FD", "NPS")


class InvestmentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    kind: str
    invested_amount: Decimal
    current_value: Decimal
    monthly_sip: Decimal
    opened_on: dt.date | None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def gain(self) -> Decimal:
        return self.current_value - self.invested_amount

    @computed_field  # type: ignore[prop-decorator]
    @property
    def gain_pct(self) -> float:
        if self.invested_amount <= 0:
            return 0.0
        return round(
            float((self.current_value - self.invested_amount) / self.invested_amount * 100), 1
        )


class InvestmentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    kind: str = Field(pattern=r"^(SIP|PPF|STK|GOLD|FD|NPS)$")
    invested_amount: Decimal = Field(ge=0)
    current_value: Decimal = Field(ge=0)
    monthly_sip: Decimal = Field(ge=0, default=Decimal("0"))
    opened_on: dt.date | None = None


class InvestmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    kind: str | None = Field(default=None, pattern=r"^(SIP|PPF|STK|GOLD|FD|NPS)$")
    invested_amount: Decimal | None = Field(default=None, ge=0)
    current_value: Decimal | None = Field(default=None, ge=0)
    monthly_sip: Decimal | None = Field(default=None, ge=0)
    opened_on: dt.date | None = None


class UpdateValueRequest(BaseModel):
    current_value: Decimal = Field(ge=0)


class AllocationItem(BaseModel):
    kind: str
    amount: Decimal
    pct: float


class InvestmentsSummaryResponse(BaseModel):
    portfolio_total: Decimal
    total_invested: Decimal
    total_gain: Decimal
    gain_pct: float
    monthly_sip_total: Decimal
    allocation: list[AllocationItem]
    investments: list[InvestmentResponse]

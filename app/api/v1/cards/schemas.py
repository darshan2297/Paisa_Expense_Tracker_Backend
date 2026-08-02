"""Pydantic schemas for credit cards."""

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field


class CreditCardCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    bank: str = Field(min_length=1, max_length=255)
    network: str = Field(default="Visa", max_length=64)
    last4: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")
    credit_limit: Decimal = Field(gt=0)
    outstanding: Decimal = Field(default=Decimal("0"), ge=0)
    statement_day: int = Field(ge=1, le=28)
    due_day: int = Field(ge=1, le=28)
    opened_on: dt.date | None = None


class CreditCardUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    bank: str | None = Field(default=None, min_length=1, max_length=255)
    network: str | None = Field(default=None, max_length=64)
    last4: str | None = Field(default=None, min_length=4, max_length=4, pattern=r"^\d{4}$")
    credit_limit: Decimal | None = Field(default=None, gt=0)
    statement_day: int | None = Field(default=None, ge=1, le=28)
    due_day: int | None = Field(default=None, ge=1, le=28)
    opened_on: dt.date | None = None


class CreditCardResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    bank: str
    network: str
    last4: str
    credit_limit: Decimal
    outstanding: Decimal
    statement_day: int
    due_day: int
    opened_on: dt.date | None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def minimum_due(self) -> Decimal:
        return (self.outstanding * Decimal("0.1")).quantize(Decimal("0.01"))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def utilization_pct(self) -> float:
        if self.credit_limit <= 0:
            return 0.0
        return float((self.outstanding / self.credit_limit * 100).quantize(Decimal("0.1")))


class CardAmountRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    note: str | None = None
    category_id: uuid.UUID | None = None


class CardsSummaryResponse(BaseModel):
    total_limit: Decimal
    total_outstanding: Decimal
    utilization_pct: float
    cards: list[CreditCardResponse]

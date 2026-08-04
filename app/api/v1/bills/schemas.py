"""Pydantic schemas for bills."""

import datetime as dt
import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

BillFrequencyLiteral = Literal["weekly", "monthly", "quarterly", "yearly"]
BillKindLiteral = Literal["electricity", "internet", "mobile", "credit_card", "gas", "other"]


class BillCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    kind: BillKindLiteral
    amount: Decimal = Field(gt=0)
    due_date: dt.date
    frequency: BillFrequencyLiteral = "monthly"
    auto_pay: bool = True
    lead_days: int = Field(default=3, ge=0, le=30)
    note: str | None = None


class BillUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    kind: BillKindLiteral | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    due_date: dt.date | None = None
    frequency: BillFrequencyLiteral | None = None
    auto_pay: bool | None = None
    lead_days: int | None = Field(default=None, ge=0, le=30)
    note: str | None = None


class BillResponse(BaseModel):
    id: uuid.UUID
    name: str
    kind: str
    amount: Decimal
    due_date: dt.date
    frequency: str
    auto_pay: bool
    lead_days: int
    note: str | None
    paid_on: dt.date | None
    days_until_due: int
    status_label: str
    linked_transaction_id: uuid.UUID | None

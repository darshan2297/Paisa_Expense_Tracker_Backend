"""Pydantic schemas for insurance policies."""

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class PolicyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    provider: str
    kind: str
    cover_amount: Decimal
    premium: Decimal
    frequency: str
    renewal_date: dt.date
    note: str | None
    premium_paid: bool
    linked_transaction_id: uuid.UUID | None


class PolicyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    provider: str = Field(min_length=1, max_length=255)
    kind: str = Field(pattern=r"^(TERM|HLTH|MOTOR|ACC|HOME)$")
    cover_amount: Decimal = Field(gt=0)
    premium: Decimal = Field(gt=0)
    frequency: str = Field(pattern=r"^(monthly|quarterly|yearly)$")
    renewal_date: dt.date
    note: str | None = None


class PolicyUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    provider: str | None = Field(default=None, min_length=1, max_length=255)
    cover_amount: Decimal | None = Field(default=None, gt=0)
    premium: Decimal | None = Field(default=None, gt=0)
    frequency: str | None = Field(default=None, pattern=r"^(monthly|quarterly|yearly)$")
    renewal_date: dt.date | None = None
    note: str | None = None


class PoliciesSummaryResponse(BaseModel):
    total_cover: Decimal
    annual_premium: Decimal
    policy_count: int
    next_renewal: PolicyResponse | None
    policies: list[PolicyResponse]

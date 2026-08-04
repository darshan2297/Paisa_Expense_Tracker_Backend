"""Pydantic schemas for assets."""

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class AssetResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    kind: str
    purchase_value: Decimal
    current_value: Decimal
    acquired_on: dt.date | None


class AssetCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    kind: str = Field(pattern=r"^(HOUSE|CAR|BIKE|GOLD|JEWEL|TECH|BANK|CASH)$")
    purchase_value: Decimal = Field(ge=0)
    current_value: Decimal = Field(ge=0)
    acquired_on: dt.date | None = None


class AssetUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    current_value: Decimal | None = Field(default=None, ge=0)
    acquired_on: dt.date | None = None


class AllocationItem(BaseModel):
    kind: str
    amount: Decimal
    pct: float


class AssetsSummaryResponse(BaseModel):
    total_value: Decimal
    count: int
    allocation: list[AllocationItem]
    assets: list[AssetResponse]

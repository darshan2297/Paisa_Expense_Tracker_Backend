"""Pydantic schemas for milestones."""

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class MilestoneResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    date: dt.date
    title: str
    note: str | None
    amount: Decimal


class MilestoneCreateRequest(BaseModel):
    date: dt.date
    title: str = Field(min_length=1, max_length=255)
    note: str | None = None
    amount: Decimal = Field(default=Decimal("0"), ge=0)


class MilestoneUpdateRequest(BaseModel):
    date: dt.date | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    note: str | None = None
    amount: Decimal | None = Field(default=None, ge=0)

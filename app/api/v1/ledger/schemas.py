"""Pydantic schemas for people ledger."""

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field

LEDGER_DIRECTIONS = ("lent", "received", "borrowed", "repaid")


class LedgerEntryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    person_name: str
    direction: str
    amount: Decimal
    date: dt.date
    note: str | None


class LedgerEntryCreateRequest(BaseModel):
    person_name: str = Field(min_length=1, max_length=255)
    direction: str = Field(pattern=r"^(lent|received|borrowed|repaid)$")
    amount: Decimal = Field(gt=0)
    date: dt.date
    note: str | None = None


class LedgerEntryUpdateRequest(BaseModel):
    person_name: str | None = Field(default=None, min_length=1, max_length=255)
    direction: str | None = Field(default=None, pattern=r"^(lent|received|borrowed|repaid)$")
    amount: Decimal | None = Field(default=None, gt=0)
    date: dt.date | None = None
    note: str | None = None


class PersonBalance(BaseModel):
    person_name: str
    net_balance: Decimal

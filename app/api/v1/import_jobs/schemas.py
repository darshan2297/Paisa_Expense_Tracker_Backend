"""Pydantic schemas for bank import."""

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class ImportRowResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    date: dt.date
    merchant: str
    amount: Decimal
    suggested_category_id: uuid.UUID | None
    state: str
    duplicate_of_txn_id: uuid.UUID | None


class ImportPreviewResponse(BaseModel):
    job_id: uuid.UUID
    filename: str
    status: str
    rows: list[ImportRowResponse]


class ImportRowUpdateRequest(BaseModel):
    suggested_category_id: uuid.UUID | None = None
    state: str | None = Field(default=None, pattern=r"^(ready|duplicate|ignored)$")


class ImportConfirmResponse(BaseModel):
    created_count: int
    skipped_count: int

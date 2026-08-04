"""Receipt scanner schemas."""

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class ScanLineItem(BaseModel):
    left: str
    right: str


class ScanResponse(BaseModel):
    merchant: str
    date: dt.date
    amount: Decimal
    gst: Decimal | None
    payment_method: str | None
    note: str | None
    line_items: list[ScanLineItem]
    suggested_category_id: uuid.UUID | None


class ScanConfirmRequest(BaseModel):
    merchant: str
    date: dt.date
    amount: Decimal = Field(gt=0)
    category_id: uuid.UUID
    note: str | None = None

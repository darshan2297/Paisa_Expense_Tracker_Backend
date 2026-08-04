"""Pydantic v2 request/response schemas for transactions.

`TransactionResponse.category` embeds `categories.schemas.CategoryResponse`
directly - schemas (plain DTOs) are outside the module-isolation rule in
docs/DEVELOPER_PHILOSOPHY.md §2.2, which targets `service`/`repository`/
`models`, not response-shape composition.
"""

import datetime as dt
import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.api.v1.categories.schemas import CategoryResponse

TransactionKind = Literal["expense", "income"]


class TransactionCreateRequest(BaseModel):
    type: TransactionKind
    category_id: uuid.UUID
    amount: Decimal = Field(gt=0)
    date: dt.date
    note: str | None = Field(default=None, max_length=500)


class TransactionUpdateRequest(BaseModel):
    category_id: uuid.UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    date: dt.date | None = None
    note: str | None = Field(default=None, max_length=500)


class TransactionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    account_id: uuid.UUID
    type: str
    amount: Decimal
    currency: str
    date: dt.date
    note: str | None
    category: CategoryResponse
    created_at: dt.datetime
    has_receipt: bool = False
    receipt_url: str | None = None


class TransactionListResponse(BaseModel):
    data: list[TransactionResponse]
    total: int
    page: int
    size: int
    pages: int


class CategoryBreakdownItem(BaseModel):
    category_id: uuid.UUID
    name: str
    color: str
    amount: Decimal
    pct: float


class TransactionsSummaryResponse(BaseModel):
    income_total: Decimal
    expense_total: Decimal
    net_balance: Decimal
    category_breakdown: list[CategoryBreakdownItem]
    recent: list[TransactionResponse]

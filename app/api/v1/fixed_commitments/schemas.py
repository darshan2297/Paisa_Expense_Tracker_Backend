"""Pydantic v2 request/response schemas for fixed commitments.

`FixedCommitmentResponse.category` embeds `categories.schemas.CategoryResponse`
directly - schemas (plain DTOs) are outside the module-isolation rule in
docs/DEVELOPER_PHILOSOPHY.md §2.2, same reasoning as `transactions.schemas`.
"""

import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.api.v1.categories.schemas import CategoryResponse

FixedCommitmentKindLiteral = Literal["emi", "home_loan", "personal_loan", "subscription", "bill"]


class FixedCommitmentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category_id: uuid.UUID
    amount: Decimal = Field(gt=0)
    due_day: int = Field(ge=1, le=28)
    kind: FixedCommitmentKindLiteral


class FixedCommitmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category_id: uuid.UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    due_day: int | None = Field(default=None, ge=1, le=28)
    kind: FixedCommitmentKindLiteral | None = None


class FixedCommitmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: CategoryResponse
    amount: Decimal
    due_day: int
    kind: str
    paid_this_month: bool
    linked_transaction_id: uuid.UUID | None

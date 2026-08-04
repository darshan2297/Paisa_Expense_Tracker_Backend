"""Pydantic schemas for shared expense groups."""

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class GroupExpenseItem(BaseModel):
    id: uuid.UUID
    label: str
    payer: str
    amount: Decimal
    date: dt.date
    split_type: str
    splits: list[dict[str, object]]


class GroupSettlementItem(BaseModel):
    id: uuid.UUID
    from_member: str
    to_member: str
    amount: Decimal
    date: dt.date


class GroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    kind: str
    members: list[str]
    expenses: list[GroupExpenseItem]
    settlements: list[GroupSettlementItem]


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    kind: str = Field(pattern=r"^(FLAT|TRIP|OTHER)$")
    members: list[str] = Field(min_length=1)


class GroupUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    members: list[str] | None = None


class GroupExpenseCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    payer: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0)
    date: dt.date
    split_type: str = Field(default="equal", pattern=r"^(equal|percent|custom)$")
    # For "equal", the service computes and overwrites this with a canonical,
    # remainder-safe allocation - whatever the client sends here is ignored.
    # For "custom"/"percent", the client must supply per-member shares that
    # sum exactly to `amount` (validated below) - there is no server-side
    # derivation for those modes.
    splits: list[dict[str, object]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_non_equal_splits(self) -> "GroupExpenseCreateRequest":
        if self.split_type == "equal":
            return self
        if not self.splits:
            raise ValueError(f"splits is required when split_type is '{self.split_type}'")
        total = sum((Decimal(str(s.get("amount", 0))) for s in self.splits), Decimal("0"))
        if total != self.amount:
            raise ValueError(f"splits must sum to the expense amount ({self.amount}), got {total}")
        return self


class GroupSettlementCreateRequest(BaseModel):
    from_member: str = Field(min_length=1, max_length=255)
    to_member: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0)
    date: dt.date


class MemberBalance(BaseModel):
    member: str
    balance: Decimal

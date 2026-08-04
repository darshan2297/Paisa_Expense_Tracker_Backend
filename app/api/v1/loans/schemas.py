"""Pydantic schemas for loans."""

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field


class LoanResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    kind: str
    principal: Decimal
    rate_pct: Decimal
    tenure_months: int
    start_date: dt.date
    outstanding: Decimal

    @computed_field  # type: ignore[prop-decorator]
    @property
    def paid_months(self) -> int:
        return paid_months_count(self.start_date, self.tenure_months)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def remaining_months(self) -> int:
        return max(0, self.tenure_months - self.paid_months)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emi(self) -> Decimal:
        """Current EMI from outstanding + remaining term + current rate.

        After rate changes, banks recompute installment on the *remaining*
        balance and term — not the original principal and full tenure.
        Example: ₹4,32,906 @ 7.85% for 97 months → ₹6,042 (not ₹5,786
        from ₹4,80,000 / 120 months).
        """
        remaining = self.remaining_months
        if remaining <= 0:
            return Decimal("0.00")
        balance = self.outstanding if self.outstanding > 0 else self.principal
        return compute_emi(balance, self.rate_pct, remaining)


class LoanCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    kind: str = Field(pattern=r"^(HL|VL|PL|OTHER)$")
    principal: Decimal = Field(gt=0)
    rate_pct: Decimal = Field(ge=0, le=100)
    tenure_months: int = Field(ge=1, le=600)
    start_date: dt.date
    outstanding: Decimal | None = None


class LoanUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    kind: str | None = Field(default=None, pattern=r"^(HL|VL|PL|OTHER)$")
    principal: Decimal | None = Field(default=None, gt=0)
    rate_pct: Decimal | None = Field(default=None, ge=0, le=100)
    tenure_months: int | None = Field(default=None, ge=1, le=600)
    start_date: dt.date | None = None
    outstanding: Decimal | None = Field(default=None, ge=0)


class ScheduleRow(BaseModel):
    month: int
    emi: Decimal
    interest: Decimal
    principal: Decimal
    balance: Decimal


class PrepayRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class PrepayResponse(BaseModel):
    loan: LoanResponse
    interest_saved: Decimal
    new_outstanding: Decimal
    schedule: list[ScheduleRow]


class LoansSummaryResponse(BaseModel):
    total_outstanding: Decimal
    total_emi: Decimal
    active_count: int
    debt_to_income_pct: float
    loans: list[LoanResponse]


def compute_emi(principal: Decimal, rate_pct: Decimal, tenure_months: int) -> Decimal:
    if tenure_months <= 0:
        return Decimal("0")
    r = rate_pct / Decimal("1200")
    if r == 0:
        return (principal / tenure_months).quantize(Decimal("0.01"))
    one_plus_r_n = (Decimal("1") + r) ** tenure_months
    emi = principal * r * one_plus_r_n / (one_plus_r_n - Decimal("1"))
    return emi.quantize(Decimal("0.01"))


def paid_months_count(start_date: dt.date, tenure_months: int) -> int:
    today = dt.date.today()
    months = (today.year - start_date.year) * 12 + (today.month - start_date.month)
    return min(tenure_months, max(0, months))


def build_schedule(
    principal: Decimal,
    rate_pct: Decimal,
    tenure_months: int,
    outstanding: Decimal | None = None,
    *,
    remaining_months: int | None = None,
) -> list[ScheduleRow]:
    """Amortization for the *remaining* balance at the current rate.

    `remaining_months` defaults to `tenure_months` when not provided (new loan).
    """
    balance = outstanding if outstanding is not None else principal
    months = remaining_months if remaining_months is not None else tenure_months
    if months <= 0 or balance <= 0:
        return []
    emi = compute_emi(balance, rate_pct, months)
    r = rate_pct / Decimal("1200")
    rows: list[ScheduleRow] = []
    for month in range(1, months + 1):
        if balance <= 0:
            break
        interest = (balance * r).quantize(Decimal("0.01"))
        principal_part = min(balance, (emi - interest).quantize(Decimal("0.01")))
        if principal_part < 0:
            principal_part = balance
        balance = (balance - principal_part).quantize(Decimal("0.01"))
        rows.append(
            ScheduleRow(
                month=month,
                emi=emi,
                interest=interest,
                principal=principal_part,
                balance=max(balance, Decimal("0")),
            )
        )
    return rows

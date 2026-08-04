"""Business logic for loans."""

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.loans import repository
from app.api.v1.loans.models import Loan
from app.api.v1.loans.schemas import (
    LoanCreateRequest,
    LoanResponse,
    LoansSummaryResponse,
    LoanUpdateRequest,
    PrepayRequest,
    PrepayResponse,
    ScheduleRow,
    build_schedule,
    compute_emi,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.deps import get_month_totals


def _to_response(loan: Loan) -> LoanResponse:
    return LoanResponse.model_validate(loan)


async def list_loans(session: AsyncSession, user_id: uuid.UUID) -> list[LoanResponse]:
    rows = await repository.list_by_user(session, user_id)
    return [_to_response(r) for r in rows]


async def get_summary(session: AsyncSession, user_id: uuid.UUID, month: str) -> LoansSummaryResponse:
    loans = await list_loans(session, user_id)
    total_outstanding = sum((l.outstanding for l in loans), Decimal("0"))
    total_emi = sum((l.emi for l in loans), Decimal("0"))
    income, _expense = await get_month_totals(session, user_id, month)
    dti = float(total_emi / income * 100) if income else 0.0
    return LoansSummaryResponse(
        total_outstanding=total_outstanding,
        total_emi=total_emi,
        active_count=len(loans),
        debt_to_income_pct=round(dti, 1),
        loans=loans,
    )


async def create_loan(
    session: AsyncSession, user_id: uuid.UUID, payload: LoanCreateRequest
) -> LoanResponse:
    outstanding = payload.outstanding if payload.outstanding is not None else payload.principal
    loan = await repository.create(
        session,
        user_id,
        name=payload.name,
        kind=payload.kind,
        principal=payload.principal,
        rate_pct=payload.rate_pct,
        tenure_months=payload.tenure_months,
        start_date=payload.start_date,
        outstanding=outstanding,
    )
    return _to_response(loan)


async def update_loan(
    session: AsyncSession, user_id: uuid.UUID, loan_id: uuid.UUID, payload: LoanUpdateRequest
) -> LoanResponse:
    loan = await repository.get_by_id(session, loan_id, user_id)
    if loan is None:
        raise NotFoundError("Loan not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(loan, field, value)
    await session.flush()
    return _to_response(loan)


async def delete_loan(session: AsyncSession, user_id: uuid.UUID, loan_id: uuid.UUID) -> None:
    loan = await repository.get_by_id(session, loan_id, user_id)
    if loan is None:
        raise NotFoundError("Loan not found")
    await repository.soft_delete(session, loan)


async def get_schedule(
    session: AsyncSession, user_id: uuid.UUID, loan_id: uuid.UUID
) -> list[ScheduleRow]:
    loan = await repository.get_by_id(session, loan_id, user_id)
    if loan is None:
        raise NotFoundError("Loan not found")
    return build_schedule(loan.principal, loan.rate_pct, loan.tenure_months, loan.outstanding)


async def prepay(
    session: AsyncSession, user_id: uuid.UUID, loan_id: uuid.UUID, payload: PrepayRequest
) -> PrepayResponse:
    loan = await repository.get_by_id(session, loan_id, user_id)
    if loan is None:
        raise NotFoundError("Loan not found")
    if payload.amount > loan.outstanding:
        raise ValidationError("Prepayment exceeds outstanding balance")

    old_schedule = build_schedule(loan.principal, loan.rate_pct, loan.tenure_months, loan.outstanding)
    old_interest = sum((r.interest for r in old_schedule), Decimal("0"))

    loan.outstanding = (loan.outstanding - payload.amount).quantize(Decimal("0.01"))
    await session.flush()

    new_schedule = build_schedule(loan.principal, loan.rate_pct, loan.tenure_months, loan.outstanding)
    new_interest = sum((r.interest for r in new_schedule), Decimal("0"))
    interest_saved = max(old_interest - new_interest, Decimal("0"))

    return PrepayResponse(
        loan=_to_response(loan),
        interest_saved=interest_saved.quantize(Decimal("0.01")),
        new_outstanding=loan.outstanding,
        schedule=new_schedule,
    )

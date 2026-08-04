"""Business logic for shared expense groups."""

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.groups import repository
from app.api.v1.groups.models import ExpenseGroup
from app.api.v1.groups.schemas import (
    GroupCreateRequest,
    GroupExpenseCreateRequest,
    GroupExpenseItem,
    GroupResponse,
    GroupSettlementCreateRequest,
    GroupSettlementItem,
    GroupUpdateRequest,
    MemberBalance,
)
from app.core.exceptions import NotFoundError


def _to_response(group: ExpenseGroup) -> GroupResponse:
    expenses = [
        GroupExpenseItem(
            id=e.id,
            label=e.label,
            payer=e.payer,
            amount=e.amount,
            date=e.date,
            split_type=e.split_type,
            splits=e.splits or [],
        )
        for e in group.expenses
        if e.deleted_at is None
    ]
    settlements = [
        GroupSettlementItem(
            id=s.id,
            from_member=s.from_member,
            to_member=s.to_member,
            amount=s.amount,
            date=s.date,
        )
        for s in group.settlements
        if s.deleted_at is None
    ]
    return GroupResponse(
        id=group.id,
        name=group.name,
        kind=group.kind,
        members=group.members or [],
        expenses=expenses,
        settlements=settlements,
    )


def _equal_shares(amount: Decimal, members: list[str]) -> list[dict[str, object]]:
    """Split `amount` across `members` so the shares sum EXACTLY to `amount`.

    Naive `amount / len(members)` drops a remainder whenever the amount isn't
    evenly divisible (₹100 / 3 = ₹33.33... -> ₹33+₹33+₹33 = ₹99, ₹1 vanishes).
    Working in integer cents and handing the leftover cents to the first N
    members (in group-member order) guarantees an exact, deterministic split.
    """
    n = len(members)
    total_cents = int((amount * 100).to_integral_value())
    base_cents, remainder_cents = divmod(total_cents, n)
    shares: list[dict[str, object]] = []
    for i, member in enumerate(members):
        cents = base_cents + (1 if i < remainder_cents else 0)
        shares.append({"member": member, "amount": str(Decimal(cents) / 100)})
    return shares


def _compute_balances(group: ExpenseGroup) -> list[MemberBalance]:
    balances: dict[str, Decimal] = {m: Decimal("0") for m in (group.members or [])}
    members = group.members or []
    for expense in group.expenses:
        if expense.deleted_at is not None:
            continue
        balances[expense.payer] = balances.get(expense.payer, Decimal("0")) + expense.amount
        splits = expense.splits or []
        if not splits and expense.split_type == "equal" and members:
            # Legacy rows created before splits were stored at write time -
            # recompute the same canonical, remainder-safe allocation.
            splits = _equal_shares(expense.amount, members)
        for split in splits:
            member = str(split.get("member", ""))
            amt = Decimal(str(split.get("amount", 0)))
            balances[member] = balances.get(member, Decimal("0")) - amt
    for settlement in group.settlements:
        if settlement.deleted_at is not None:
            continue
        balances[settlement.from_member] = (
            balances.get(settlement.from_member, Decimal("0")) + settlement.amount
        )
        balances[settlement.to_member] = (
            balances.get(settlement.to_member, Decimal("0")) - settlement.amount
        )
    return [MemberBalance(member=m, balance=bal) for m, bal in balances.items()]


async def list_groups(session: AsyncSession, user_id: uuid.UUID) -> list[GroupResponse]:
    groups = await repository.list_by_user(session, user_id)
    return [_to_response(g) for g in groups]


async def create_group(
    session: AsyncSession, user_id: uuid.UUID, payload: GroupCreateRequest
) -> GroupResponse:
    group = await repository.create_group(
        session, user_id, name=payload.name, kind=payload.kind, members=payload.members
    )
    await session.refresh(group, ["expenses", "settlements"])
    return _to_response(group)


async def update_group(
    session: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID, payload: GroupUpdateRequest
) -> GroupResponse:
    group = await repository.get_by_id(session, group_id, user_id)
    if group is None:
        raise NotFoundError("Group not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(group, field, value)
    await session.flush()
    return _to_response(group)


async def delete_group(session: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID) -> None:
    group = await repository.get_by_id(session, group_id, user_id)
    if group is None:
        raise NotFoundError("Group not found")
    await repository.soft_delete_group(session, group)


async def add_expense(
    session: AsyncSession,
    user_id: uuid.UUID,
    group_id: uuid.UUID,
    payload: GroupExpenseCreateRequest,
) -> GroupResponse:
    group = await repository.get_by_id(session, group_id, user_id)
    if group is None:
        raise NotFoundError("Group not found")
    data = payload.model_dump()
    if payload.split_type == "equal" and group.members:
        # Always the canonical, remainder-safe allocation - never trust a
        # client-computed equal split (that's exactly how the ₹100/3 bug
        # happened: rounding done independently, per-screen, per-render).
        data["splits"] = _equal_shares(payload.amount, group.members)
    await repository.create_expense(session, group_id, **data)
    group = await repository.get_by_id(session, group_id, user_id)
    assert group is not None
    return _to_response(group)


async def delete_expense(
    session: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID, expense_id: uuid.UUID
) -> GroupResponse:
    group = await repository.get_by_id(session, group_id, user_id)
    if group is None:
        raise NotFoundError("Group not found")
    expense = await repository.get_expense(session, expense_id, group_id)
    if expense is None:
        raise NotFoundError("Expense not found")
    await repository.soft_delete_expense(session, expense)
    group = await repository.get_by_id(session, group_id, user_id)
    assert group is not None
    return _to_response(group)


async def add_settlement(
    session: AsyncSession,
    user_id: uuid.UUID,
    group_id: uuid.UUID,
    payload: GroupSettlementCreateRequest,
) -> GroupResponse:
    group = await repository.get_by_id(session, group_id, user_id)
    if group is None:
        raise NotFoundError("Group not found")
    await repository.create_settlement(session, group_id, **payload.model_dump())
    group = await repository.get_by_id(session, group_id, user_id)
    assert group is not None
    return _to_response(group)


async def delete_settlement(
    session: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID, settlement_id: uuid.UUID
) -> GroupResponse:
    group = await repository.get_by_id(session, group_id, user_id)
    if group is None:
        raise NotFoundError("Group not found")
    settlement = await repository.get_settlement(session, settlement_id, group_id)
    if settlement is None:
        raise NotFoundError("Settlement not found")
    await repository.soft_delete_settlement(session, settlement)
    group = await repository.get_by_id(session, group_id, user_id)
    assert group is not None
    return _to_response(group)


async def get_balances(
    session: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID
) -> list[MemberBalance]:
    group = await repository.get_by_id(session, group_id, user_id)
    if group is None:
        raise NotFoundError("Group not found")
    return _compute_balances(group)

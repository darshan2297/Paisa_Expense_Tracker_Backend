"""Data access for sessions, backups, and security events."""

import datetime as dt
import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.models import User
from app.api.v1.security.models import Backup, SecurityEvent, UserSession


async def list_sessions(session: AsyncSession, user_id: uuid.UUID) -> list[UserSession]:
    result = await session.execute(
        select(UserSession)
        .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .order_by(UserSession.last_active_at.desc())
    )
    return list(result.scalars().all())


async def find_open_session_by_user_agent(
    session: AsyncSession, user_id: uuid.UUID, user_agent: str | None
) -> UserSession | None:
    """Newest open session matching this browser fingerprint (raw User-Agent)."""
    if not user_agent:
        return None
    result = await session.execute(
        select(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            UserSession.user_agent == user_agent,
        )
        .order_by(UserSession.last_active_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_session_by_id(
    session: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
) -> UserSession | None:
    result = await session.execute(
        select(UserSession).where(UserSession.id == session_id, UserSession.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def revoke_session(session: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
    await session.execute(
        update(UserSession)
        .where(UserSession.id == session_id, UserSession.user_id == user_id)
        .values(revoked_at=dt.datetime.now(dt.UTC))
    )


async def revoke_all_except(
    session: AsyncSession, user_id: uuid.UUID, except_id: uuid.UUID | None
) -> None:
    stmt = (
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .values(revoked_at=dt.datetime.now(dt.UTC))
    )
    if except_id:
        stmt = stmt.where(UserSession.id != except_id)
    await session.execute(stmt)


async def revoke_duplicate_user_agents(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Keep the newest open session per User-Agent; revoke older duplicates.

    Repeated logins used to insert a new row every time without revoking the
    previous one, so one browser could show as several identical devices.
    """
    rows = await list_sessions(session, user_id)
    seen: set[str] = set()
    revoked = 0
    now = dt.datetime.now(dt.UTC)
    for row in rows:
        key = (row.user_agent or "").strip() or f"id:{row.id}"
        if key in seen:
            row.revoked_at = now
            row.is_current = False
            revoked += 1
        else:
            seen.add(key)
    if revoked:
        await session.flush()
    return revoked


async def clear_current_flags(session: AsyncSession, user_id: uuid.UUID) -> None:
    await session.execute(
        update(UserSession).where(UserSession.user_id == user_id).values(is_current=False)
    )


async def create_session(session: AsyncSession, **kwargs: object) -> UserSession:
    s = UserSession(**kwargs)  # type: ignore[arg-type]
    session.add(s)
    await session.flush()
    return s


async def create_backup_record(session: AsyncSession, **kwargs: object) -> Backup:
    b = Backup(**kwargs)  # type: ignore[arg-type]
    session.add(b)
    await session.flush()
    return b


async def list_security_events(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    limit: int = 20,
    offset: int = 0,
    from_date: dt.date | None = None,
    to_date: dt.date | None = None,
) -> tuple[list[SecurityEvent], int]:
    """Return a page of security events plus the filtered total count."""
    filters = [SecurityEvent.user_id == user_id]
    if from_date is not None:
        start = dt.datetime(from_date.year, from_date.month, from_date.day, tzinfo=dt.UTC)
        filters.append(SecurityEvent.created_at >= start)
    if to_date is not None:
        end = dt.datetime(
            to_date.year, to_date.month, to_date.day, 23, 59, 59, 999999, tzinfo=dt.UTC
        )
        filters.append(SecurityEvent.created_at <= end)

    count_result = await session.execute(
        select(func.count()).select_from(SecurityEvent).where(*filters)
    )
    total = int(count_result.scalar_one())

    result = await session.execute(
        select(SecurityEvent)
        .where(*filters)
        .order_by(SecurityEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def create_security_event(session: AsyncSession, **kwargs: object) -> SecurityEvent:
    event = SecurityEvent(**kwargs)  # type: ignore[arg-type]
    session.add(event)
    await session.flush()
    return event


async def get_user(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

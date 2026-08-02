"""Shared pytest fixtures.

Integration tests run against a real Postgres (see docs/DATABASE_STANDARDS.md
- never SQLite-as-a-stand-in, its type/constraint behaviour diverges from
Postgres in ways that would hide real bugs). `alembic upgrade head` is
expected to have already been run against that database before the test
suite starts (CI/local docs both do this explicitly).
"""

import os

os.environ.setdefault("ENVIRONMENT", "test")

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text

from app.core.base_model import Base
from app.core.database import get_engine, get_sessionmaker
from app.middleware.rate_limit import limiter


@pytest.fixture(autouse=True)
def _reset_rate_limits() -> None:
    """Without this, slowapi's in-memory limiter state persists across
    tests within the same process. Auth endpoints carry a strict 5/minute
    limit (see app/middleware/rate_limit.py) - a test file that calls
    /auth/login more than 5 times (easy, once there are more than a
    handful of auth tests) would otherwise start getting spurious 429s
    partway through the suite, unrelated to what each test is verifying.
    """
    limiter.reset()


@pytest.fixture(autouse=True)
async def _clean_database() -> AsyncGenerator[None, None]:
    """Truncate every table after each test, then dispose the cached async
    engine and clear its `@lru_cache` entries.

    The truncation keeps tests from seeing another test's leftover rows.
    The dispose+cache-clear is the more subtle, more important part: pytest
    runs each test function as its own separate `loop.run_until_complete()`
    call. An asyncpg connection (held open inside the engine's connection
    pool, cached at module level via `get_engine`/`get_sessionmaker`) that
    was checked out during one test's `run_until_complete()` cycle cannot be
    safely reused in a *different* test's cycle, even though pytest-asyncio
    nominally reuses "the same" event loop object across tests by default -
    the stop/restart between cycles leaves the connection's low-level I/O
    callbacks in a state that raises "Future attached to a different loop"
    / "got result for unknown protocol state" the next time it's used.
    Disposing the engine and clearing the cache after every test forces a
    brand new engine+connection to be created fresh within whichever
    test/fixture touches the DB next, entirely avoiding the problem.
    """
    yield
    engine = get_engine()
    skip_tables = {"categories"}  # global seeded taxonomy — never user-owned rows
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            if table.name in skip_tables:
                continue
            await conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))
    await engine.dispose()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()

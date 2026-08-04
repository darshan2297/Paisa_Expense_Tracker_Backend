"""Idempotent seeding of global reference data (categories-like catalogs).

Runs after migrations on container start and once at API startup so a fresh
database always has the configuration option catalog populated from
`configuration/catalog.py`.
"""

from sqlalchemy import select

from app.api.v1.auth.models import User
from app.api.v1.configuration import service as config_service
from app.core.database import get_engine, get_sessionmaker


async def ensure_reference_data() -> None:
    """Seed the configurations catalog and backfill per-user default rows."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        inserted = await config_service.seed_catalog(session)
        users = await session.execute(select(User.id).where(User.deleted_at.is_(None)))
        for user_id in users.scalars():
            await config_service.initialize_user_defaults(session, user_id)
        await session.commit()

    if inserted:
        print(f"[reference-data] Seeded {inserted} configuration catalog row(s).")


async def ensure_reference_data_and_reset_pool() -> None:
    """Seed reference data, then drop the async engine so a new event loop can reconnect."""
    await ensure_reference_data()
    await get_engine().dispose()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()

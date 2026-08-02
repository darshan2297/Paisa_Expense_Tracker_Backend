"""Creates the single application user, if it doesn't already exist.

There is no public registration endpoint (a deliberate decision - this is a
single-user personal app, not a product anyone else signs up for), so this
script is the *only* way a user ever gets created. Idempotent: safe to run
on every deploy/container start.

Usage (from the `backend/` directory, with a real .env in place):

    poetry run python -m scripts.seed

Requires SEED_USER_EMAIL / SEED_USER_PASSWORD / SEED_USER_NAME to be set
(see .env.example) - refuses to guess a default password.
"""

import asyncio
import sys

from app.api.v1.auth import repository
from app.core.config import get_settings
from app.core.database import get_sessionmaker
from app.core.security import hash_password
from app.deps import ensure_default_account


async def _seed() -> int:
    settings = get_settings()
    if not (settings.SEED_USER_EMAIL and settings.SEED_USER_PASSWORD and settings.SEED_USER_NAME):
        print(
            "SEED_USER_EMAIL, SEED_USER_PASSWORD, and SEED_USER_NAME must all be set "
            "(see .env.example) - refusing to seed with a guessed/default password.",
            file=sys.stderr,
        )
        return 1

    session_factory = get_sessionmaker()
    async with session_factory() as session:
        existing = await repository.get_by_email(session, settings.SEED_USER_EMAIL)
        if existing is not None:
            print(f"User {settings.SEED_USER_EMAIL} already exists - nothing to do.")
            return 0

        user = await repository.create_user(
            session,
            email=settings.SEED_USER_EMAIL,
            hashed_password=hash_password(settings.SEED_USER_PASSWORD),
            name=settings.SEED_USER_NAME,
        )
        await ensure_default_account(session, user.id)
        await session.commit()

    print(f"Created user {settings.SEED_USER_EMAIL}.")
    return 0


def main() -> None:
    sys.exit(asyncio.run(_seed()))


if __name__ == "__main__":
    main()

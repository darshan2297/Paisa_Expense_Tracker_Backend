"""Seed global reference data after migrations.

Idempotent — safe to run on every container start, same as category taxonomy
is guaranteed by the create-table migration.

Usage (from the `backend/` directory):

    poetry run python -m scripts.seed_reference_data
"""

import asyncio
import sys

from app.bootstrap.reference_data import ensure_reference_data


async def _seed() -> int:
    await ensure_reference_data()
    print("Reference data seed complete.")
    return 0


def main() -> None:
    sys.exit(asyncio.run(_seed()))


if __name__ == "__main__":
    main()

"""Trivial example scheduled job proving the APScheduler wiring works end to end.

Remove-ready placeholder: once real background jobs exist (e.g. recurring
transaction generation, budget rollovers in a later phase), this can be
deleted along with its registration in `app.scheduler._register_jobs`.
"""

import logging

logger = logging.getLogger(__name__)


async def heartbeat_job() -> None:
    """Logs a heartbeat line. Runs hourly; see `app.scheduler._register_jobs`."""
    logger.info("scheduler alive")

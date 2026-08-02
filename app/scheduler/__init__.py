"""In-process background job scheduler (APScheduler, AsyncIOScheduler).

No external broker/worker (no Celery, no Redis) - jobs run in the same
event loop as the FastAPI app. `start()`/`shutdown()` are called from the
app's lifespan context manager in `app.main`, so the scheduler's lifetime is
tied exactly to the app's.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scheduler.jobs.heartbeat import heartbeat_job

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _register_jobs() -> None:
    """Register all recurring jobs. Add new jobs here as they're introduced."""
    scheduler.add_job(
        heartbeat_job,
        trigger="interval",
        hours=1,
        id="heartbeat",
        replace_existing=True,
    )


def start() -> None:
    """Start the scheduler and register jobs. Call once from app startup."""
    if scheduler.running:
        logger.warning("Scheduler already running; skipping start()")
        return
    _register_jobs()
    scheduler.start()
    logger.info("Scheduler started")


def shutdown() -> None:
    """Stop the scheduler gracefully. Call once from app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

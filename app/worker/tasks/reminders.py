"""Background reminder tasks (F5 / F17).

Uses asyncio.run() to reuse the existing async service/repository layer
from sync Celery workers.
"""

import asyncio
import logging

from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_bill_reminders() -> int:
    from app.worker.tasks._reminder_runner import run_bill_reminders

    return await run_bill_reminders()


async def _run_fixed_reminders() -> int:
    from app.worker.tasks._reminder_runner import run_fixed_commitment_reminders

    return await run_fixed_commitment_reminders()


@celery_app.task(name="app.worker.tasks.reminders.process_bill_reminders")
def process_bill_reminders() -> int:
    count = asyncio.run(_run_bill_reminders())
    logger.info("bill reminders processed", extra={"count": count})
    return count


@celery_app.task(name="app.worker.tasks.reminders.process_fixed_commitment_reminders")
def process_fixed_commitment_reminders() -> int:
    count = asyncio.run(_run_fixed_reminders())
    logger.info("fixed commitment reminders processed", extra={"count": count})
    return count


async def _run_bill_rollover() -> int:
    from app.worker.tasks._reminder_runner import run_bill_rollover

    return await run_bill_rollover()


@celery_app.task(name="app.worker.tasks.reminders.process_bill_rollover")
def process_bill_rollover() -> int:
    count = asyncio.run(_run_bill_rollover())
    logger.info("bill rollover processed", extra={"count": count})
    return count

"""Internal ops endpoints (cron / automation). Not for end-user clients."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.worker.tasks._reminder_runner import (
    run_bill_reminders,
    run_fixed_commitment_reminders,
    run_policy_reminders,
)

internal_router = APIRouter(prefix="/internal")


def _require_cron_secret(x_cron_secret: str | None) -> None:
    settings = get_settings()
    expected = settings.CRON_SECRET
    if not expected or not x_cron_secret or x_cron_secret != expected:
        raise UnauthorizedError("Invalid cron secret")


@internal_router.post("/reminders/run", summary="Run daily reminder jobs (cron)")
async def run_reminders(
    x_cron_secret: Annotated[str | None, Header(alias="X-Cron-Secret")] = None,
) -> dict[str, int]:
    """Send unpaid bill/EMI/policy reminders inside each user's lead window.

    Protected by `CRON_SECRET`. Intended for GitHub Actions schedule (or any
    external cron) because Render free tier only runs the API process.
    """
    _require_cron_secret(x_cron_secret)
    bills = await run_bill_reminders()
    fixed = await run_fixed_commitment_reminders()
    policies = await run_policy_reminders()
    return {"bills": bills, "fixed_commitments": fixed, "policies": policies}

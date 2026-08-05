"""Outbound email via Resend (F17 reminders).

Option B (no custom domain): set
  EMAIL_FROM=Paisa <onboarding@resend.dev>
Resend then only delivers to the email on your Resend account.
With a verified domain, use e.g. Paisa <reminders@yourdomain.com>.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

import resend

from app.core.config import get_settings
from app.core.email_templates import render_reminder_email

logger = logging.getLogger(__name__)


def email_configured() -> bool:
    settings = get_settings()
    return bool(settings.RESEND_API_KEY and settings.EMAIL_FROM)


def _format_inr(amount: Decimal | float | int | str) -> str:
    value = Decimal(str(amount))
    quantized = value.quantize(Decimal("0.01"))
    # Indian grouping for the integer part
    whole, _, frac = f"{quantized:.2f}".partition(".")
    sign = ""
    if whole.startswith("-"):
        sign = "-"
        whole = whole[1:]
    if len(whole) <= 3:
        grouped = whole
    else:
        last3 = whole[-3:]
        rest = whole[:-3]
        parts: list[str] = []
        while rest:
            parts.append(rest[-2:])
            rest = rest[:-2]
        grouped = ",".join(reversed(parts)) + "," + last3
    return f"{sign}₹{grouped}.{frac}"


def send_reminder_email(
    *,
    to: str,
    recipient_name: str,
    kind: str,
    title: str,
    body: str,
    amount: Decimal | float | int | str | None = None,
    due_label: str | None = None,
    days_until: int | None = None,
) -> bool:
    """Send a reminder email. Returns True on success, False if skipped/failed."""
    settings = get_settings()
    if not settings.RESEND_API_KEY or not settings.EMAIL_FROM:
        logger.debug("email skipped — RESEND_API_KEY / EMAIL_FROM not set")
        return False

    urgency = "due today" if days_until == 0 else (
        f"due in {days_until} day{'s' if days_until != 1 else ''}"
        if days_until is not None
        else None
    )
    amount_display = _format_inr(amount) if amount is not None else None
    html, text = render_reminder_email(
        recipient_name=recipient_name,
        kind=kind,
        title=title,
        body=body,
        amount_display=amount_display,
        due_label=due_label,
        urgency=urgency,
    )

    resend.api_key = settings.RESEND_API_KEY
    payload: dict[str, Any] = {
        "from": settings.EMAIL_FROM,
        "to": [to],
        "subject": title,
        "html": html,
        "text": text,
    }
    try:
        result = resend.Emails.send(payload)
        email_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)
        logger.info(
            "reminder email sent",
            extra={"to": to, "kind": kind, "email_id": email_id},
        )
        return True
    except Exception:
        logger.exception("reminder email failed", extra={"to": to, "kind": kind})
        return False

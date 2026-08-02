"""Stdlib logging configuration with request-id awareness.

The request id is stored in a `contextvars.ContextVar` (populated by
`app.middleware.request_id`) so any log line emitted while handling a
request — regardless of which module logs it — can be correlated back to
that request without threading the id through every function signature.
"""

import logging
import sys
from contextvars import ContextVar

from app.core.config import get_settings

# Populated per-request by app.middleware.request_id; defaults to "-" for
# log lines emitted outside of a request context (startup, scheduler jobs).
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Injects the current request id into every log record as `request_id`."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get()
        return True


def configure_logging() -> None:
    """Configure root logging handlers/formatters.

    Call once at process startup (see `app.main.create_app`). Idempotent:
    re-running clears and re-adds handlers rather than stacking duplicates.
    """
    settings = get_settings()

    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.addFilter(RequestIdFilter())

    # A readable console format for local/dev use. A later phase can swap
    # this for structured JSON logging in production if needed.
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | req_id=%(request_id)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    root_logger.setLevel(logging.DEBUG if settings.ENVIRONMENT == "dev" else logging.INFO)

    # Quiet down noisy third-party loggers unless we're actively debugging.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

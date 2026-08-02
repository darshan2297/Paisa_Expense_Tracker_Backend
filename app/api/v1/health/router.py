"""Health-check endpoint.

Deliberately dependency-free (no DB ping, no scheduler check) for Phase-0 -
this just proves the app boots and routing/middleware/envelope wiring work
end to end. A later phase can extend this with real readiness checks
(DB connectivity, migration status) if a separate `/health/ready` vs
`/health/live` split is needed.
"""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health", summary="Liveness check")
async def health_check() -> dict[str, str]:
    """Return basic liveness info. Wrapped in the standard envelope by
    `ResponseEnvelopeMiddleware`, so the raw shape returned here is just the
    `data` payload: `{"status": "ok", "version": "..."}`.
    """
    settings = get_settings()
    return {"status": "ok", "version": settings.APP_VERSION}

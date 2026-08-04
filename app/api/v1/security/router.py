"""HTTP layer for security settings, sessions, and backup."""

import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.security import service
from app.api.v1.security.schemas import (
    BackupImportRequest,
    BackupResponse,
    LoginHistoryListResponse,
    SecurityOverviewResponse,
    SecuritySettingsResponse,
    SecuritySettingsUpdateRequest,
    SessionResponse,
)
from app.deps import CurrentUser, PageParamsDep, get_session
from app.middleware.rate_limit import default_limit

security_router = APIRouter(prefix="/security")


@security_router.get("", summary="Security & Privacy overview")
@default_limit()
async def security_overview(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> SecurityOverviewResponse:
    return await service.get_overview(session, current_user)


@security_router.get("/login-history", summary="Paginated login history")
@default_limit()
async def login_history(
    request: Request,
    current_user: CurrentUser,
    params: PageParamsDep,
    session: AsyncSession = Depends(get_session),
    from_date: Annotated[
        dt.date | None,
        Query(
            description="Inclusive start date (YYYY-MM-DD). Defaults to today when omitted with to_date."
        ),
    ] = None,
    to_date: Annotated[
        dt.date | None,
        Query(
            description="Inclusive end date (YYYY-MM-DD). Defaults to today when omitted with from_date."
        ),
    ] = None,
) -> LoginHistoryListResponse:
    # Default both ends to today so the Security screen shows today's events
    # without the client needing a special "unset" mode.
    today = dt.datetime.now(dt.UTC).date()
    resolved_from = from_date if from_date is not None else today
    resolved_to = to_date if to_date is not None else today
    return await service.list_login_history(
        session, current_user, params, resolved_from, resolved_to
    )


@security_router.get("/settings", summary="Get security settings")
@default_limit()
async def get_security_settings(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> SecuritySettingsResponse:
    return await service.get_settings(session, current_user)


@security_router.patch("/settings", summary="Update security settings")
@default_limit()
async def update_security_settings(
    request: Request,
    payload: SecuritySettingsUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> SecuritySettingsResponse:
    return await service.update_settings(session, current_user, payload)


@security_router.post("/vault/lock", summary="Lock vault now")
@default_limit()
async def lock_vault(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> SecuritySettingsResponse:
    return await service.lock_vault(session, current_user)


@security_router.get("/sessions", summary="List active sessions")
@default_limit()
async def list_sessions(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[SessionResponse]:
    return await service.list_sessions(session, current_user.id)


@security_router.delete("/sessions/{session_id}", status_code=204, summary="Revoke session")
@default_limit()
async def revoke_session(
    request: Request,
    session_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.revoke_session(session, current_user.id, session_id)
    return Response(status_code=204)


@security_router.delete("/sessions", status_code=204, summary="Revoke all other sessions")
@default_limit()
async def revoke_all_sessions(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.revoke_all_sessions(session, current_user.id)
    return Response(status_code=204)


@security_router.post("/backup/export", summary="Export encrypted backup")
@default_limit()
async def export_backup(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BackupResponse:
    return await service.export_backup(session, current_user)


@security_router.post("/backup/import", summary="Restore from backup")
@default_limit()
async def import_backup(
    request: Request,
    payload: BackupImportRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    result = await service.import_backup(session, current_user, payload.content)
    return JSONResponse(result)

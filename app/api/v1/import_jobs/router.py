"""HTTP layer for bank import."""

import uuid

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.import_jobs import service
from app.api.v1.import_jobs.schemas import (
    ImportConfirmResponse,
    ImportPreviewResponse,
    ImportRowResponse,
    ImportRowUpdateRequest,
)
from app.deps import CurrentUser, DefaultAccountId, get_session
from app.middleware.rate_limit import default_limit

import_router = APIRouter(prefix="/import")


@import_router.post("/upload", status_code=201, summary="Upload bank statement")
@default_limit()
async def upload_import(
    request: Request,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> ImportPreviewResponse:
    content = await file.read()
    return await service.upload_file(session, current_user.id, file.filename or "import.csv", content)


@import_router.get("/{job_id}/preview", summary="Preview import rows")
@default_limit()
async def preview_import(
    request: Request,
    job_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> ImportPreviewResponse:
    return await service.get_preview(session, current_user.id, job_id)


@import_router.patch("/{job_id}/rows/{row_id}", summary="Update import row")
@default_limit()
async def update_import_row(
    request: Request,
    job_id: uuid.UUID,
    row_id: uuid.UUID,
    payload: ImportRowUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> ImportRowResponse:
    return await service.update_row(session, current_user.id, job_id, row_id, payload)


@import_router.post("/{job_id}/confirm", summary="Confirm import")
@default_limit()
async def confirm_import(
    request: Request,
    job_id: uuid.UUID,
    current_user: CurrentUser,
    account_id: DefaultAccountId,
    session: AsyncSession = Depends(get_session),
) -> ImportConfirmResponse:
    return await service.confirm_import(session, current_user.id, job_id, account_id)

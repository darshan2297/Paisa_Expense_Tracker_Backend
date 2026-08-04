"""Bank statement import service."""

import csv
import datetime as dt
import io
import uuid
from decimal import Decimal, InvalidOperation

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.import_jobs import repository
from app.api.v1.import_jobs.schemas import (
    ImportConfirmResponse,
    ImportPreviewResponse,
    ImportRowResponse,
    ImportRowUpdateRequest,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.deps import DefaultAccountId, list_categories, record_transaction


def _parse_csv(content: bytes) -> list[tuple[dt.date, str, Decimal]]:
    text = content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows: list[tuple[dt.date, str, Decimal]] = []
    for line in reader:
        if len(line) < 3:
            continue
        try:
            date = dt.date.fromisoformat(line[0].strip()[:10])
            merchant = line[1].strip()
            amount = Decimal(line[2].strip().replace(",", ""))
            if amount < 0:
                amount = abs(amount)
            rows.append((date, merchant, amount))
        except (ValueError, InvalidOperation):
            continue
    return rows


async def upload_file(
    session: AsyncSession, user_id: uuid.UUID, filename: str, content: bytes
) -> ImportPreviewResponse:
    parsed = _parse_csv(content)
    if not parsed:
        raise ValidationError("No valid rows found in file")
    job = await repository.create_job(session, user_id, filename)
    job.row_count = len(parsed)
    import_rows: list[ImportRowResponse] = []
    for date, merchant, amount in parsed:
        row = await repository.add_row(
            session,
            job_id=job.id,
            date=date,
            merchant=merchant,
            amount=amount,
            state="ready",
        )
        import_rows.append(ImportRowResponse.model_validate(row))
    await session.flush()
    return ImportPreviewResponse(
        job_id=job.id, filename=filename, status=job.status, rows=import_rows
    )


async def get_preview(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> ImportPreviewResponse:
    job = await repository.get_job(session, job_id, user_id)
    if job is None:
        raise NotFoundError("Import job not found")
    rows = await repository.list_rows(session, job_id)
    return ImportPreviewResponse(
        job_id=job.id,
        filename=job.filename,
        status=job.status,
        rows=[ImportRowResponse.model_validate(r) for r in rows],
    )


async def update_row(
    session: AsyncSession,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    row_id: uuid.UUID,
    payload: ImportRowUpdateRequest,
) -> ImportRowResponse:
    job = await repository.get_job(session, job_id, user_id)
    if job is None:
        raise NotFoundError("Import job not found")
    row = await repository.get_row(session, row_id, job_id)
    if row is None:
        raise NotFoundError("Import row not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.flush()
    return ImportRowResponse.model_validate(row)


async def confirm_import(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID, account_id: uuid.UUID
) -> ImportConfirmResponse:
    job = await repository.get_job(session, job_id, user_id)
    if job is None:
        raise NotFoundError("Import job not found")
    rows = await repository.list_rows(session, job_id)
    cats = await list_categories(session)
    default_cat = next((c for c in cats if c.name == "Other"), cats[0] if cats else None)
    created = 0
    skipped = 0
    for row in rows:
        if row.state == "ignored":
            skipped += 1
            continue
        cat_id = row.suggested_category_id or (default_cat.id if default_cat else None)
        if cat_id is None:
            skipped += 1
            continue
        await record_transaction(
            session,
            user_id=user_id,
            account_id=account_id,
            category_id=cat_id,
            type_="expense",
            amount=row.amount,
            date=row.date,
            note=row.merchant,
        )
        created += 1
    job.status = "confirmed"
    await session.flush()
    return ImportConfirmResponse(created_count=created, skipped_count=skipped)

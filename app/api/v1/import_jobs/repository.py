"""Data access for import jobs."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.import_jobs.models import ImportJob, ImportRow


async def get_job(session: AsyncSession, job_id: uuid.UUID, user_id: uuid.UUID) -> ImportJob | None:
    result = await session.execute(
        select(ImportJob).where(ImportJob.id == job_id, ImportJob.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_job(session: AsyncSession, user_id: uuid.UUID, filename: str) -> ImportJob:
    job = ImportJob(user_id=user_id, filename=filename, status="parsed")
    session.add(job)
    await session.flush()
    return job


async def list_rows(session: AsyncSession, job_id: uuid.UUID) -> list[ImportRow]:
    result = await session.execute(select(ImportRow).where(ImportRow.job_id == job_id))
    return list(result.scalars().all())


async def add_row(session: AsyncSession, **kwargs: object) -> ImportRow:
    row = ImportRow(**kwargs)
    session.add(row)
    await session.flush()
    return row


async def get_row(session: AsyncSession, row_id: uuid.UUID, job_id: uuid.UUID) -> ImportRow | None:
    result = await session.execute(
        select(ImportRow).where(ImportRow.id == row_id, ImportRow.job_id == job_id)
    )
    return result.scalar_one_or_none()

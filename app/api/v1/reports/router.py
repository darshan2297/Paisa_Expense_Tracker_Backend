"""HTTP layer for reports."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.reports import service
from app.api.v1.reports.schemas import ReportResponse
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

reports_router = APIRouter(prefix="/reports")
_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@reports_router.get("/{report_type}", summary="Generate report")
@default_limit()
async def get_report(
    request: Request,
    report_type: str,
    current_user: CurrentUser,
    month: str = Query(pattern=_MONTH_PATTERN),
    session: AsyncSession = Depends(get_session),
) -> ReportResponse:
    if report_type not in service.REPORT_TYPES:
        raise HTTPException(status_code=404, detail="Unknown report type")
    return await service.build_report(session, current_user.id, report_type, month)


@reports_router.get("/{report_type}/export", summary="Export report")
@default_limit()
async def export_report(
    request: Request,
    report_type: str,
    current_user: CurrentUser,
    month: str = Query(pattern=_MONTH_PATTERN),
    format: str = Query(default="csv", pattern=r"^(csv|pdf)$"),
    session: AsyncSession = Depends(get_session),
) -> Response:
    if report_type not in service.REPORT_TYPES:
        raise HTTPException(status_code=404, detail="Unknown report type")
    report = await service.build_report(session, current_user.id, report_type, month)
    if format == "csv":
        csv_content = service.export_csv(report)
        return Response(content=csv_content, media_type="text/csv")
    pdf_content = service.export_pdf_text(report)
    return Response(content=pdf_content, media_type="application/pdf")

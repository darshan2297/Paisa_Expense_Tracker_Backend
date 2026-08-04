"""HTTP layer for receipt scanner."""

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.scanner import service
from app.api.v1.scanner.schemas import ScanConfirmRequest, ScanResponse
from app.deps import CurrentUser, DefaultAccountId, get_session, list_categories
from app.middleware.rate_limit import default_limit

scanner_router = APIRouter(prefix="/scanner")


@scanner_router.post("/scan", summary="Scan receipt image")
@default_limit()
async def scan_receipt(
    request: Request,
    file: UploadFile = File(...),
) -> ScanResponse:
    return await service.scan_receipt(file)


@scanner_router.post("/confirm", status_code=201, summary="Create transaction from scan")
@default_limit()
async def confirm_scan(
    request: Request,
    payload: ScanConfirmRequest,
    current_user: CurrentUser,
    account_id: DefaultAccountId,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    cats = await list_categories(session)
    cat_by_id = {c.id: c for c in cats}
    txn_id = await service.confirm_scan(session, current_user.id, account_id, payload, cat_by_id)
    return {"transaction_id": str(txn_id)}

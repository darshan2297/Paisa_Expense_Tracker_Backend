"""Receipt OCR service — self-hosted stub with optional Tesseract."""

import datetime as dt
import re
import uuid
from decimal import Decimal

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.scanner.schemas import ScanConfirmRequest, ScanLineItem, ScanResponse
from app.api.v1.transactions.schemas import TransactionResponse
from app.deps import DefaultAccountId, list_categories, record_transaction


def _extract_text(content: bytes) -> str:
    try:
        import pytesseract  # type: ignore[import-untyped]
        from PIL import Image  # type: ignore[import-untyped]
        import io

        image = Image.open(io.BytesIO(content))
        return pytesseract.image_to_string(image)
    except Exception:
        return ""


def _parse_receipt_text(text: str) -> ScanResponse:
    amount_match = re.search(r"(\d[\d,]*\.\d{2})", text)
    amount = Decimal(amount_match.group(1).replace(",", "")) if amount_match else Decimal("0")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    merchant = lines[0] if lines else "Unknown merchant"
    return ScanResponse(
        merchant=merchant[:255],
        date=dt.date.today(),
        amount=amount,
        gst=None,
        payment_method=None,
        note="Scanned receipt",
        line_items=[ScanLineItem(left=ln, right="") for ln in lines[1:6]],
        suggested_category_id=None,
    )


async def scan_receipt(file: UploadFile) -> ScanResponse:
    content = await file.read()
    text = _extract_text(content)
    if text:
        return _parse_receipt_text(text)
    return ScanResponse(
        merchant="Scanned merchant",
        date=dt.date.today(),
        amount=Decimal("0"),
        gst=None,
        payment_method=None,
        note="Upload a clearer image for OCR",
        line_items=[],
        suggested_category_id=None,
    )


async def confirm_scan(
    session: AsyncSession,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    payload: ScanConfirmRequest,
    cat_by_id: dict,
) -> uuid.UUID:
    txn_id = await record_transaction(
        session,
        user_id=user_id,
        account_id=account_id,
        category_id=payload.category_id,
        type_="expense",
        amount=payload.amount,
        date=payload.date,
        note=f"{payload.merchant} — {payload.note or ''}".strip(),
    )
    return txn_id

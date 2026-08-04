"""Pydantic schemas for net worth."""

import datetime as dt
from decimal import Decimal

from pydantic import BaseModel


class NetWorthPart(BaseModel):
    label: str
    value: Decimal


class NetWorthCurrentResponse(BaseModel):
    net_worth: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    delta_month: Decimal | None
    parts: list[NetWorthPart]


class NetWorthHistoryPoint(BaseModel):
    date: dt.date
    net_worth: Decimal
    total_assets: Decimal
    total_liabilities: Decimal


class NetWorthHistoryResponse(BaseModel):
    points: list[NetWorthHistoryPoint]

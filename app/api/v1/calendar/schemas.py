"""Pydantic schemas for calendar and heatmap."""

import datetime as dt
from decimal import Decimal

from pydantic import BaseModel


class PlannedItem(BaseModel):
    label: str
    kind: str
    amount: Decimal


class ActualItem(BaseModel):
    id: str
    title: str
    amount: Decimal
    type: str


class DayCell(BaseModel):
    date: dt.date
    inflow: Decimal
    outflow: Decimal
    planned: list[PlannedItem]
    actual: list[ActualItem]


class CalendarResponse(BaseModel):
    month: str
    days: list[DayCell]
    net_flow: Decimal
    highest_day_outflow: Decimal
    planned_total: Decimal
    actual_total: Decimal


class HeatmapCell(BaseModel):
    date: dt.date
    intensity: int
    amount: Decimal


class HeatmapResponse(BaseModel):
    weeks: int
    cells: list[HeatmapCell]
    weekday_totals: dict[str, Decimal]

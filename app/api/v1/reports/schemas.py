"""Report engine schemas."""

from pydantic import BaseModel


class ReportKpi(BaseModel):
    label: str
    value: str


class ReportRow(BaseModel):
    cells: list[str]


class ReportChartBar(BaseModel):
    label: str
    height: int
    color: str


class ReportResponse(BaseModel):
    report_type: str
    month: str
    summary: list[ReportKpi]
    rows: list[ReportRow]
    chart: list[ReportChartBar]

"""Generic report builder."""

import csv
import io
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.budget import service as budget_service
from app.api.v1.goals import repository as goals_repo
from app.api.v1.investments import service as investments_service
from app.api.v1.loans import service as loans_service
from app.api.v1.net_worth import service as net_worth_service
from app.api.v1.reports.schemas import ReportChartBar, ReportKpi, ReportResponse, ReportRow
from app.api.v1.transactions import repository as txn_repo
from app.api.v1.transactions.service import get_month_totals
from app.deps import list_categories

REPORT_TYPES = (
    "monthly",
    "yearly",
    "income",
    "expense",
    "budget",
    "investment",
    "loan",
    "networth",
    "goal",
    "tax",
)


async def build_report(
    session: AsyncSession, user_id: uuid.UUID, report_type: str, month: str
) -> ReportResponse:
    income, expense = await get_month_totals(session, user_id, month)
    budget_summary = await budget_service.get_summary(session, user_id, month)
    cats = await list_categories(session)
    cat_by_id = {c.id: c for c in cats}
    category_sums = await txn_repo.sum_expense_by_category(session, user_id, month)

    rows: list[ReportRow] = []
    chart: list[ReportChartBar] = []
    summary: list[ReportKpi] = []

    if report_type in ("monthly", "expense"):
        summary = [
            ReportKpi(label="Total spent", value=f"₹{expense}"),
            ReportKpi(label="Categories", value=str(len(category_sums))),
            ReportKpi(label="Daily average", value=f"₹{expense / 30:.0f}"),
        ]
        for cat_id, amount in category_sums:
            cat = cat_by_id.get(cat_id)
            name = cat.name if cat else "Unknown"
            pct = float(amount / expense * 100) if expense else 0
            rows.append(ReportRow(cells=[name, "—", f"₹{amount}", f"{pct:.0f}%"]))
            # Bar height is pixels for the frontend chart track (max 140).
            chart.append(
                ReportChartBar(
                    label=name[:5],
                    height=max(8, int(pct / 100 * 140)),
                    color=cat.color if cat else "#888",
                )
            )

    elif report_type == "income":
        summary = [ReportKpi(label="Total income", value=f"₹{income}")]
        rows = [ReportRow(cells=["Income", "—", f"₹{income}", "100%"])]

    elif report_type == "budget":
        summary = [
            ReportKpi(label="Budget", value=f"₹{budget_summary.monthly_amount}"),
            ReportKpi(label="Spent", value=f"₹{budget_summary.spent}"),
            ReportKpi(label="Remaining", value=f"₹{budget_summary.remaining}"),
        ]

    elif report_type == "investment":
        inv = await investments_service.get_summary(session, user_id)
        summary = [
            ReportKpi(label="Portfolio", value=f"₹{inv.portfolio_total}"),
            ReportKpi(label="Gain", value=f"₹{inv.total_gain}"),
        ]
        for i in inv.investments:
            rows.append(ReportRow(cells=[i.name, i.kind, f"₹{i.current_value}", f"{i.gain_pct}%"]))

    elif report_type == "loan":
        loans = await loans_service.get_summary(session, user_id, month)
        summary = [ReportKpi(label="Outstanding", value=f"₹{loans.total_outstanding}")]
        for loan in loans.loans:
            rows.append(
                ReportRow(cells=[loan.name, loan.kind, f"₹{loan.outstanding}", f"₹{loan.emi} EMI"])
            )

    elif report_type == "networth":
        nw = await net_worth_service.get_current(session, user_id)
        summary = [ReportKpi(label="Net worth", value=f"₹{nw.net_worth}")]
        for p in nw.parts:
            rows.append(ReportRow(cells=[p.label, "—", f"₹{p.value}", ""]))

    elif report_type == "goal":
        goals = await goals_repo.list_by_user(session, user_id)
        summary = [ReportKpi(label="Goals", value=str(len(goals)))]
        for g in goals:
            pct = float(g.saved_amount / g.target_amount * 100) if g.target_amount else 0
            rows.append(
                ReportRow(
                    cells=[g.name, f"{pct:.0f}%", f"₹{g.saved_amount}", f"₹{g.target_amount}"]
                )
            )

    else:
        summary = [
            ReportKpi(label="Income", value=f"₹{income}"),
            ReportKpi(label="Expenses", value=f"₹{expense}"),
        ]

    return ReportResponse(
        report_type=report_type,
        month=month,
        summary=summary,
        rows=rows,
        chart=chart,
    )


def export_csv(report: ReportResponse) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([f"Report: {report.report_type}", report.month])
    writer.writerow([])
    writer.writerow(["Summary"])
    for kpi in report.summary:
        writer.writerow([kpi.label, kpi.value])
    writer.writerow([])
    for row in report.rows:
        writer.writerow(row.cells)
    return output.getvalue()


def export_pdf_text(report: ReportResponse) -> bytes:
    lines = [f"Paisa Report — {report.report_type} ({report.month})", ""]
    lines.append("Summary")
    for kpi in report.summary:
        lines.append(f"  {kpi.label}: {kpi.value}")
    lines.append("")
    for row in report.rows:
        lines.append(" | ".join(row.cells))
    return "\n".join(lines).encode("utf-8")

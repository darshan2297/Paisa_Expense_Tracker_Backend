"""Aggregated router registration for all v1 modules."""

from fastapi import APIRouter

from app.api.v1.accounts.router import accounts_router
from app.api.v1.assets.router import assets_router
from app.api.v1.auth.router import auth_router, profile_router
from app.api.v1.bills.router import bills_router
from app.api.v1.budget.router import budget_router
from app.api.v1.calendar.router import calendar_router
from app.api.v1.cards.router import cards_router
from app.api.v1.categories.router import categories_router
from app.api.v1.dashboard.router import dashboard_router
from app.api.v1.fixed_commitments.router import fixed_commitments_router
from app.api.v1.goals.router import goals_router
from app.api.v1.groups.router import groups_router
from app.api.v1.health.router import router as health_router
from app.api.v1.import_jobs.router import import_router
from app.api.v1.insights.router import insights_router
from app.api.v1.internal.router import internal_router
from app.api.v1.investments.router import investments_router
from app.api.v1.ledger.router import ledger_router
from app.api.v1.loans.router import loans_router
from app.api.v1.milestones.router import milestones_router
from app.api.v1.net_worth.router import net_worth_router
from app.api.v1.notifications.router import notifications_router
from app.api.v1.policies.router import policies_router
from app.api.v1.reports.router import reports_router
from app.api.v1.scanner.router import scanner_router
from app.api.v1.security.router import security_router
from app.api.v1.transactions.router import transactions_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(auth_router, tags=["auth"])
api_v1_router.include_router(profile_router, tags=["profile"])
api_v1_router.include_router(accounts_router, tags=["accounts"])
api_v1_router.include_router(categories_router, tags=["categories"])
api_v1_router.include_router(transactions_router, tags=["transactions"])
api_v1_router.include_router(budget_router, tags=["budget"])
api_v1_router.include_router(fixed_commitments_router, tags=["fixed-commitments"])
api_v1_router.include_router(bills_router, tags=["bills"])
api_v1_router.include_router(cards_router, tags=["cards"])
api_v1_router.include_router(goals_router, tags=["goals"])
api_v1_router.include_router(investments_router, tags=["investments"])
api_v1_router.include_router(loans_router, tags=["loans"])
api_v1_router.include_router(assets_router, tags=["assets"])
api_v1_router.include_router(net_worth_router, tags=["net-worth"])
api_v1_router.include_router(ledger_router, tags=["ledger"])
api_v1_router.include_router(groups_router, tags=["groups"])
api_v1_router.include_router(policies_router, tags=["policies"])
api_v1_router.include_router(calendar_router, tags=["calendar"])
api_v1_router.include_router(insights_router, tags=["insights"])
api_v1_router.include_router(milestones_router, tags=["milestones"])
api_v1_router.include_router(dashboard_router, tags=["dashboard"])
api_v1_router.include_router(reports_router, tags=["reports"])
api_v1_router.include_router(notifications_router, tags=["notifications"])
api_v1_router.include_router(import_router, tags=["import"])
api_v1_router.include_router(scanner_router, tags=["scanner"])
api_v1_router.include_router(security_router, tags=["security"])
api_v1_router.include_router(internal_router, tags=["internal"])

"""Aggregates all v1 feature routers under a single `/api/v1` prefix.

New feature modules (auth, accounts, transactions, ...) register their
router here as they're added in later phases.
"""

from fastapi import APIRouter

from app.api.v1.accounts.router import accounts_router
from app.api.v1.auth.router import auth_router, profile_router
from app.api.v1.bills.router import bills_router
from app.api.v1.budget.router import budget_router
from app.api.v1.cards.router import cards_router
from app.api.v1.categories.router import categories_router
from app.api.v1.fixed_commitments.router import fixed_commitments_router
from app.api.v1.health.router import router as health_router
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

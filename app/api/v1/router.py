"""Aggregates all v1 feature routers under a single `/api/v1` prefix.

New feature modules (auth, accounts, transactions, ...) register their
router here as they're added in later phases - Phase-0 only has `health`.
"""

from fastapi import APIRouter

from app.api.v1.health.router import router as health_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router, tags=["health"])

"""Shared FastAPI dependencies, re-exported here for a single, stable import
path (`from app.deps import ...`) that feature modules can rely on without
needing to know which `app.core.*` submodule something actually lives in.
"""

from app.api.v1.accounts.deps import DefaultAccountId, get_default_account_id
from app.api.v1.accounts.service import ensure_default_account
from app.api.v1.auth.deps import CurrentUser, get_current_user
from app.api.v1.categories.deps import UtilitiesCategoryId, get_utilities_category_id
from app.api.v1.categories.service import get_category, list_categories
from app.api.v1.transactions.service import (
    find_transaction_for_bill,
    find_transaction_for_commitment,
    get_month_totals,
    record_transaction,
    remove_transaction_by_id,
)
from app.core.database import get_session
from app.core.pagination import PageParams, PageParamsDep, page_params_dependency

__all__ = [
    "get_session",
    "PageParams",
    "PageParamsDep",
    "page_params_dependency",
    "CurrentUser",
    "get_current_user",
    "DefaultAccountId",
    "get_default_account_id",
    "UtilitiesCategoryId",
    "get_utilities_category_id",
    "ensure_default_account",
    "get_category",
    "list_categories",
    "get_month_totals",
    "find_transaction_for_commitment",
    "find_transaction_for_bill",
    "record_transaction",
    "remove_transaction_by_id",
]

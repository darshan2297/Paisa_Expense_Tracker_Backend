"""Shared FastAPI dependencies, re-exported here for a single, stable import
path (`from app.deps import ...`) that feature modules can rely on without
needing to know which `app.core.*` submodule something actually lives in.
"""

from app.core.database import get_session
from app.core.pagination import PageParams, PageParamsDep, page_params_dependency

__all__ = [
    "get_session",
    "PageParams",
    "PageParamsDep",
    "page_params_dependency",
]

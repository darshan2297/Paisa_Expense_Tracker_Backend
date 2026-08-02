"""Pagination FastAPI dependency and helper.

`PageParams` reads `page`/`size` query params (with sane defaults and an
upper bound on `size` to prevent clients from requesting unbounded result
sets). `paginate()` turns a full result list plus those params into the
standard paginated payload shape.

Phase-0 note: `paginate()` here operates on an in-memory sequence for
simplicity and unit-testability. Once real domain queries exist, list
endpoints should prefer pushing `LIMIT`/`OFFSET` down to the database
(e.g. via `.limit()`/`.offset()` on the SQLAlchemy select) rather than
fetching everything into memory first — this helper's `total`/`pages` math
still applies in that case, just fed a DB-side count instead of `len()`.
"""

from typing import Annotated, Any, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel, Field

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

T = TypeVar("T")


class PageParams(BaseModel):
    """Validated pagination query parameters."""

    page: int = Field(default=1, ge=1, description="1-indexed page number")
    size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Items per page, capped at {MAX_PAGE_SIZE}",
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


def page_params_dependency(
    page: Annotated[int, Query(ge=1, description="1-indexed page number")] = 1,
    size: Annotated[
        int, Query(ge=1, le=MAX_PAGE_SIZE, description=f"Items per page, capped at {MAX_PAGE_SIZE}")
    ] = DEFAULT_PAGE_SIZE,
) -> PageParams:
    """FastAPI dependency callable producing a `PageParams` instance."""
    return PageParams(page=page, size=size)


PageParamsDep = Annotated[PageParams, Depends(page_params_dependency)]


class Page(BaseModel):
    """Standard paginated response payload."""

    data: list[Any]
    total: int
    page: int
    size: int
    pages: int


def paginate(items: list[T], params: PageParams) -> Page:
    """Slice `items` according to `params` and compute pagination metadata.

    `total` is `len(items)` here since this operates on an already-fetched
    in-memory list (see module docstring re: pushing pagination to the DB
    for real queries).
    """
    total = len(items)
    pages = (total + params.size - 1) // params.size if total else 0
    start = params.offset
    end = start + params.size
    page_items = items[start:end]
    return Page(data=page_items, total=total, page=params.page, size=params.size, pages=pages)

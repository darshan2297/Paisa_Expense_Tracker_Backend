"""Unit tests for `app.core.pagination.paginate`."""

from app.core.pagination import MAX_PAGE_SIZE, PageParams, paginate


def test_paginate_first_page_default_size() -> None:
    items = list(range(1, 51))  # 50 items
    params = PageParams(page=1, size=20)

    result = paginate(items, params)

    assert result.data == list(range(1, 21))
    assert result.total == 50
    assert result.page == 1
    assert result.size == 20
    assert result.pages == 3


def test_paginate_middle_page() -> None:
    items = list(range(1, 51))
    params = PageParams(page=2, size=20)

    result = paginate(items, params)

    assert result.data == list(range(21, 41))
    assert result.page == 2


def test_paginate_last_partial_page() -> None:
    items = list(range(1, 51))
    params = PageParams(page=3, size=20)

    result = paginate(items, params)

    assert result.data == list(range(41, 51))
    assert len(result.data) == 10


def test_paginate_page_beyond_range_returns_empty() -> None:
    items = list(range(1, 11))
    params = PageParams(page=5, size=20)

    result = paginate(items, params)

    assert result.data == []
    assert result.total == 10
    assert result.pages == 1


def test_paginate_empty_items() -> None:
    params = PageParams(page=1, size=20)

    result = paginate([], params)

    assert result.data == []
    assert result.total == 0
    assert result.pages == 0


def test_page_params_size_capped_at_max() -> None:
    params = PageParams(page=1, size=MAX_PAGE_SIZE)
    assert params.size == MAX_PAGE_SIZE


def test_page_params_offset_calculation() -> None:
    params = PageParams(page=3, size=10)
    assert params.offset == 20

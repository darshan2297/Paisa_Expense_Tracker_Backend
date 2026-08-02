"""Integration tests for /api/v1/transactions/* - full request cycle (real
Postgres, all middleware) via httpx.AsyncClient.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

TEST_EMAIL = "transactions.test@example.com"
TEST_PASSWORD = "correct-horse-battery-staple"
TEST_NAME = "Test User"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": TEST_NAME},
    )
    access_token = register_response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


async def _category_id(client: AsyncClient, headers: dict[str, str], name: str) -> str:
    response = await client.get("/api/v1/categories", headers=headers)
    categories = response.json()["data"]
    return next(c["id"] for c in categories if c["name"] == name)


async def test_transactions_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/transactions", params={"month": "2026-08"})
    assert response.status_code == 401


async def test_create_transaction_then_appears_in_list(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    category_id = await _category_id(client, auth_headers, "Groceries")

    create_response = await client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "type": "expense",
            "category_id": category_id,
            "amount": "1450.50",
            "date": "2026-08-05",
            "note": "Weekend run",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["amount"] == "1450.50"
    assert created["category"]["name"] == "Groceries"
    assert created["type"] == "expense"

    list_response = await client.get(
        "/api/v1/transactions", headers=auth_headers, params={"month": "2026-08"}
    )
    assert list_response.status_code == 200
    body = list_response.json()["data"]
    assert body["total"] == 1
    assert body["data"][0]["id"] == created["id"]


async def test_create_transaction_rejects_mismatched_category_kind(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    salary_id = await _category_id(client, auth_headers, "Salary")  # an income category

    response = await client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"type": "expense", "category_id": salary_id, "amount": "100", "date": "2026-08-05"},
    )
    assert response.status_code == 422


async def test_create_transaction_rejects_non_positive_amount(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    category_id = await _category_id(client, auth_headers, "Groceries")

    response = await client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"type": "expense", "category_id": category_id, "amount": "0", "date": "2026-08-05"},
    )
    assert response.status_code == 422


async def test_list_filters_by_month(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    category_id = await _category_id(client, auth_headers, "Groceries")
    for date in ("2026-07-20", "2026-08-05"):
        await client.post(
            "/api/v1/transactions",
            headers=auth_headers,
            json={"type": "expense", "category_id": category_id, "amount": "100", "date": date},
        )

    august = await client.get(
        "/api/v1/transactions", headers=auth_headers, params={"month": "2026-08"}
    )
    assert august.json()["data"]["total"] == 1
    july = await client.get("/api/v1/transactions", headers=auth_headers, params={"month": "2026-07"})
    assert july.json()["data"]["total"] == 1


async def test_list_filters_by_type(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    expense_cat = await _category_id(client, auth_headers, "Groceries")
    income_cat = await _category_id(client, auth_headers, "Salary")
    await client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"type": "expense", "category_id": expense_cat, "amount": "100", "date": "2026-08-05"},
    )
    await client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"type": "income", "category_id": income_cat, "amount": "5000", "date": "2026-08-01"},
    )

    response = await client.get(
        "/api/v1/transactions",
        headers=auth_headers,
        params={"month": "2026-08", "type": "income"},
    )
    body = response.json()["data"]
    assert body["total"] == 1
    assert body["data"][0]["type"] == "income"


async def test_list_search_matches_note_or_category_name(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    category_id = await _category_id(client, auth_headers, "Groceries")
    await client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "type": "expense",
            "category_id": category_id,
            "amount": "100",
            "date": "2026-08-05",
            "note": "Weekend run",
        },
    )

    by_note = await client.get(
        "/api/v1/transactions", headers=auth_headers, params={"month": "2026-08", "q": "weekend"}
    )
    assert by_note.json()["data"]["total"] == 1

    by_category = await client.get(
        "/api/v1/transactions", headers=auth_headers, params={"month": "2026-08", "q": "grocer"}
    )
    assert by_category.json()["data"]["total"] == 1

    no_match = await client.get(
        "/api/v1/transactions", headers=auth_headers, params={"month": "2026-08", "q": "nonexistent"}
    )
    assert no_match.json()["data"]["total"] == 0


async def test_delete_transaction_removes_it_from_list(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    category_id = await _category_id(client, auth_headers, "Groceries")
    created = await client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"type": "expense", "category_id": category_id, "amount": "100", "date": "2026-08-05"},
    )
    transaction_id = created.json()["data"]["id"]

    delete_response = await client.delete(
        f"/api/v1/transactions/{transaction_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204

    list_response = await client.get(
        "/api/v1/transactions", headers=auth_headers, params={"month": "2026-08"}
    )
    assert list_response.json()["data"]["total"] == 0


async def test_delete_unknown_transaction_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.delete(
        "/api/v1/transactions/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )
    assert response.status_code == 404


async def test_summary_computes_income_expense_and_category_breakdown(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    groceries = await _category_id(client, auth_headers, "Groceries")
    rent = await _category_id(client, auth_headers, "Rent")
    salary = await _category_id(client, auth_headers, "Salary")

    await client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"type": "income", "category_id": salary, "amount": "80000", "date": "2026-08-01"},
    )
    await client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"type": "expense", "category_id": groceries, "amount": "6000", "date": "2026-08-06"},
    )
    await client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={"type": "expense", "category_id": rent, "amount": "24000", "date": "2026-08-03"},
    )

    response = await client.get(
        "/api/v1/transactions/summary", headers=auth_headers, params={"month": "2026-08"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["income_total"] == "80000.00"
    assert data["expense_total"] == "30000.00"
    assert data["net_balance"] == "50000.00"
    breakdown_by_name = {item["name"]: item["pct"] for item in data["category_breakdown"]}
    assert breakdown_by_name["Rent"] == 80.0
    assert breakdown_by_name["Groceries"] == 20.0
    assert len(data["recent"]) == 3

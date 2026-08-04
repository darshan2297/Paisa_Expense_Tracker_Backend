"""Integration tests for /api/v1/budget/* - full request cycle (real
Postgres, all middleware) via httpx.AsyncClient.
"""

from collections.abc import AsyncGenerator
from typing import cast

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

TEST_EMAIL = "budget.test@example.com"
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
    return cast(str, next(c["id"] for c in categories if c["name"] == name))


async def test_get_budget_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/budget")
    assert response.status_code == 401


async def test_get_budget_returns_defaults_when_unset(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/budget", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["monthly_amount"] == "0"
    assert data["alert_pct"] == 20
    assert data["reminder_lead_days"] == 15


async def test_put_budget_creates_then_updates(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    create_response = await client.put(
        "/api/v1/budget",
        headers=auth_headers,
        json={"monthly_amount": "55000", "alert_pct": 20, "reminder_lead_days": 15},
    )
    assert create_response.status_code == 200
    assert create_response.json()["data"]["monthly_amount"] == "55000"

    update_response = await client.put(
        "/api/v1/budget",
        headers=auth_headers,
        json={"monthly_amount": "60000", "alert_pct": 25, "reminder_lead_days": 10},
    )
    assert update_response.status_code == 200
    data = update_response.json()["data"]
    assert data["monthly_amount"] in ("60000", "60000.00")
    assert data["alert_pct"] == 25
    assert data["reminder_lead_days"] == 10

    get_response = await client.get("/api/v1/budget", headers=auth_headers)
    assert get_response.json()["data"]["monthly_amount"] in ("60000", "60000.00")


async def test_put_budget_rejects_out_of_range_alert_pct(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.put(
        "/api/v1/budget",
        headers=auth_headers,
        json={"monthly_amount": "55000", "alert_pct": 99, "reminder_lead_days": 15},
    )
    assert response.status_code == 422


async def test_budget_summary_computes_remaining_against_spent(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.put(
        "/api/v1/budget",
        headers=auth_headers,
        json={"monthly_amount": "10000", "alert_pct": 20, "reminder_lead_days": 15},
    )
    category_id = await _category_id(client, auth_headers, "Groceries")
    await client.post(
        "/api/v1/transactions",
        headers=auth_headers,
        json={
            "type": "expense",
            "category_id": category_id,
            "amount": "4000",
            "date": "2026-08-05",
        },
    )

    response = await client.get(
        "/api/v1/budget/summary", headers=auth_headers, params={"month": "2026-08"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["monthly_amount"] == "10000.00"
    assert data["spent"] == "4000.00"
    assert data["remaining"] == "6000.00"
    assert data["pct_remaining"] == 60.0

"""Integration tests for /api/v1/cards/*."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

TEST_EMAIL = "cards.test@example.com"
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


async def test_cards_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/cards/summary")
    assert response.status_code == 401


async def test_create_card_summary_and_pay_minimum(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    create_response = await client.post(
        "/api/v1/cards",
        headers=auth_headers,
        json={
            "name": "HDFC Regalia",
            "bank": "HDFC",
            "last4": "4242",
            "credit_limit": "100000",
            "outstanding": "25000",
            "statement_day": 26,
            "due_day": 8,
        },
    )
    assert create_response.status_code == 201
    card = create_response.json()["data"]
    card_id = card["id"]
    assert card["minimum_due"] == "2500.00"
    assert card["utilization_pct"] == 25.0

    summary_response = await client.get("/api/v1/cards/summary", headers=auth_headers)
    assert summary_response.status_code == 200
    summary = summary_response.json()["data"]
    assert summary["total_outstanding"] == "25000.00"
    assert len(summary["cards"]) == 1

    pay_response = await client.post(
        f"/api/v1/cards/{card_id}/pay",
        headers=auth_headers,
        json={"amount": "2500"},
    )
    assert pay_response.status_code == 200
    assert pay_response.json()["data"]["outstanding"] == "22500.00"

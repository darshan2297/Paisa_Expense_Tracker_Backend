"""Integration tests for /api/v1/goals/*."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

TEST_EMAIL = "goals.test@example.com"
TEST_PASSWORD = "correct-horse-battery-staple"
TEST_NAME = "Goals User"


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


async def test_list_goals_empty(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.get("/api/v1/goals", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"] == []


async def test_create_and_contribute_goal(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    create_response = await client.post(
        "/api/v1/goals",
        headers=auth_headers,
        json={
            "name": "Japan trip",
            "target_amount": "250000",
            "saved_amount": "62000",
            "monthly_contribution": "9000",
            "due_day": 5,
        },
    )
    assert create_response.status_code == 201
    goal = create_response.json()["data"]
    assert goal["name"] == "Japan trip"
    assert goal["pct_complete"] == 24.8
    goal_id = goal["id"]

    contribute_response = await client.post(
        f"/api/v1/goals/{goal_id}/contribute",
        headers=auth_headers,
        json={"amount": "10000"},
    )
    assert contribute_response.status_code == 200
    assert contribute_response.json()["data"]["saved_amount"] == "72000.00"


async def test_emergency_fund_goal(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    await client.post(
        "/api/v1/goals",
        headers=auth_headers,
        json={
            "name": "Emergency fund",
            "target_amount": "300000",
            "saved_amount": "185000",
            "monthly_contribution": "12000",
            "is_emergency": True,
        },
    )

    emergency_response = await client.get("/api/v1/goals/emergency", headers=auth_headers)
    assert emergency_response.status_code == 200
    data = emergency_response.json()["data"]
    assert data["saved"] == "185000.00"
    assert data["goal_id"] is not None
    assert data["months_of_expenses_covered"] >= 0


async def test_goals_summary(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    await client.post(
        "/api/v1/goals",
        headers=auth_headers,
        json={"name": "Laptop", "target_amount": "120000", "saved_amount": "96000", "monthly_contribution": "6000"},
    )

    response = await client.get("/api/v1/goals/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["active_count"] == 1
    assert data["total_saved"] == "96000.00"
    assert len(data["next_contributions"]) == 1

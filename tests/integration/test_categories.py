"""Integration tests for /api/v1/categories and /api/v1/accounts - full
request cycle (real Postgres, all middleware) via httpx.AsyncClient.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

TEST_EMAIL = "categories.test@example.com"
TEST_PASSWORD = "correct-horse-battery-staple"
TEST_NAME = "Test User"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Registers via the real POST /auth/register endpoint (rather than
    inserting a user directly via the repository) specifically so the
    account-auto-provisioning behavior under test (`ensure_default_account`,
    called from `auth.service.register`) actually runs.
    """
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": TEST_NAME},
    )
    access_token = register_response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


async def test_categories_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/categories")
    assert response.status_code == 401


async def test_categories_returns_the_seeded_taxonomy(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/categories", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 19  # 12 expense + 7 income, see the migration's seed data
    expense = [c for c in data if c["kind"] == "expense"]
    income = [c for c in data if c["kind"] == "income"]
    assert len(expense) == 12
    assert len(income) == 7
    assert {c["name"] for c in expense} >= {"Food & Dining", "Rent", "Other"}
    assert {c["name"] for c in income} >= {"Salary", "Freelance", "Other"}
    # Every row carries a hex color for the frontend category chips.
    assert all(c["color"].startswith("#") for c in data)


async def test_accounts_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/accounts")
    assert response.status_code == 401


async def test_registration_creates_a_default_cash_account(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """No accounts UI exists yet - every user gets exactly one implicit
    "Cash" account, created during registration (see
    `ensure_default_account`, called from `auth.service.register`).
    """
    response = await client.get("/api/v1/accounts", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Cash"
    assert data[0]["kind"] == "cash"
    assert data[0]["currency"] == "INR"

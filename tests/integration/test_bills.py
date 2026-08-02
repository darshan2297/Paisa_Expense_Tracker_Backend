"""Integration tests for /api/v1/bills/*."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

TEST_EMAIL = "bills.test@example.com"
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


async def test_bills_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/bills", params={"month": "2026-08"})
    assert response.status_code == 401


async def test_create_pay_and_unpay_bill(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    create_response = await client.post(
        "/api/v1/bills",
        headers=auth_headers,
        json={
            "name": "Electricity",
            "kind": "electricity",
            "amount": "2500",
            "due_date": "2026-08-10",
            "frequency": "monthly",
        },
    )
    assert create_response.status_code == 201
    bill_id = create_response.json()["data"]["id"]
    assert create_response.json()["data"]["paid_on"] is None

    pay_response = await client.post(f"/api/v1/bills/{bill_id}/pay", headers=auth_headers)
    assert pay_response.status_code == 200
    assert pay_response.json()["data"]["paid_on"] == "2026-08-02"

    unpay_response = await client.post(f"/api/v1/bills/{bill_id}/unpay", headers=auth_headers)
    assert unpay_response.status_code == 200
    assert unpay_response.json()["data"]["paid_on"] is None


async def test_toggle_auto_and_delete_bill(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    create_response = await client.post(
        "/api/v1/bills",
        headers=auth_headers,
        json={
            "name": "Broadband",
            "kind": "internet",
            "amount": "999",
            "due_date": "2026-08-15",
            "auto_pay": True,
        },
    )
    bill_id = create_response.json()["data"]["id"]

    toggle_response = await client.post(f"/api/v1/bills/{bill_id}/toggle-auto", headers=auth_headers)
    assert toggle_response.status_code == 200
    assert toggle_response.json()["data"]["auto_pay"] is False

    delete_response = await client.delete(f"/api/v1/bills/{bill_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    list_response = await client.get("/api/v1/bills", headers=auth_headers, params={"month": "2026-08"})
    assert list_response.json()["data"] == []

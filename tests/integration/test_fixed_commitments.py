"""Integration tests for /api/v1/fixed-commitments/* - full request cycle
(real Postgres, all middleware) via httpx.AsyncClient.
"""

from collections.abc import AsyncGenerator
from typing import cast

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

TEST_EMAIL = "fixed.test@example.com"
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


async def _create_commitment(client: AsyncClient, headers: dict[str, str], category_id: str) -> str:
    response = await client.post(
        "/api/v1/fixed-commitments",
        headers=headers,
        json={
            "name": "Home loan EMI",
            "category_id": category_id,
            "amount": "18400",
            "due_day": 5,
            "kind": "home_loan",
        },
    )
    assert response.status_code == 201
    return cast(str, response.json()["data"]["id"])


async def test_fixed_commitments_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/fixed-commitments", params={"month": "2026-08"})
    assert response.status_code == 401


async def test_create_and_list_fixed_commitment_starts_unpaid(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    category_id = await _category_id(client, auth_headers, "Rent")
    commitment_id = await _create_commitment(client, auth_headers, category_id)

    response = await client.get(
        "/api/v1/fixed-commitments", headers=auth_headers, params={"month": "2026-08"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == commitment_id
    assert data[0]["paid_this_month"] is False
    assert data[0]["linked_transaction_id"] is None


async def test_toggle_paid_creates_a_linked_transaction(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    category_id = await _category_id(client, auth_headers, "Rent")
    commitment_id = await _create_commitment(client, auth_headers, category_id)

    toggle_response = await client.post(
        f"/api/v1/fixed-commitments/{commitment_id}/toggle-paid",
        headers=auth_headers,
        params={"month": "2026-08"},
    )
    assert toggle_response.status_code == 200
    data = toggle_response.json()["data"]
    assert data["paid_this_month"] is True
    assert data["linked_transaction_id"] is not None

    transactions_response = await client.get(
        "/api/v1/transactions", headers=auth_headers, params={"month": "2026-08"}
    )
    body = transactions_response.json()["data"]
    assert body["total"] == 1
    assert body["data"][0]["id"] == data["linked_transaction_id"]
    assert body["data"][0]["amount"] == "18400.00"
    assert body["data"][0]["note"] == "Home loan EMI"


async def test_toggle_paid_again_removes_the_linked_transaction(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    category_id = await _category_id(client, auth_headers, "Rent")
    commitment_id = await _create_commitment(client, auth_headers, category_id)

    await client.post(
        f"/api/v1/fixed-commitments/{commitment_id}/toggle-paid",
        headers=auth_headers,
        params={"month": "2026-08"},
    )
    second_toggle = await client.post(
        f"/api/v1/fixed-commitments/{commitment_id}/toggle-paid",
        headers=auth_headers,
        params={"month": "2026-08"},
    )

    assert second_toggle.status_code == 200
    data = second_toggle.json()["data"]
    assert data["paid_this_month"] is False
    assert data["linked_transaction_id"] is None

    transactions_response = await client.get(
        "/api/v1/transactions", headers=auth_headers, params={"month": "2026-08"}
    )
    assert transactions_response.json()["data"]["total"] == 0


async def test_toggle_paid_is_scoped_per_month(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    category_id = await _category_id(client, auth_headers, "Rent")
    commitment_id = await _create_commitment(client, auth_headers, category_id)

    await client.post(
        f"/api/v1/fixed-commitments/{commitment_id}/toggle-paid",
        headers=auth_headers,
        params={"month": "2026-08"},
    )

    july_status = await client.get(
        "/api/v1/fixed-commitments", headers=auth_headers, params={"month": "2026-07"}
    )
    assert july_status.json()["data"][0]["paid_this_month"] is False


async def test_delete_fixed_commitment(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    category_id = await _category_id(client, auth_headers, "Rent")
    commitment_id = await _create_commitment(client, auth_headers, category_id)

    delete_response = await client.delete(
        f"/api/v1/fixed-commitments/{commitment_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204

    list_response = await client.get(
        "/api/v1/fixed-commitments", headers=auth_headers, params={"month": "2026-08"}
    )
    assert list_response.json()["data"] == []


async def test_delete_unknown_fixed_commitment_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.delete(
        "/api/v1/fixed-commitments/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )
    assert response.status_code == 404


async def test_patch_fixed_commitment_updates_amount_and_due_day(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    category_id = await _category_id(client, auth_headers, "Rent")
    commitment_id = await _create_commitment(client, auth_headers, category_id)

    patch_response = await client.patch(
        f"/api/v1/fixed-commitments/{commitment_id}",
        headers=auth_headers,
        params={"month": "2026-08"},
        json={"amount": "20000", "due_day": 10},
    )
    assert patch_response.status_code == 200
    data = patch_response.json()["data"]
    assert data["amount"] in ("20000", "20000.00")
    assert data["due_day"] == 10

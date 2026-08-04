"""Integration tests for the one-time bootstrap POST /auth/register endpoint
and its GET /auth/registration-open companion.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.auth import repository
from app.core.database import get_sessionmaker
from app.core.security import hash_password
from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_registration_open_when_no_users_exist(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/registration-open")
    assert response.status_code == 200
    assert response.json()["data"]["open"] is True


async def test_register_succeeds_when_no_users_exist_and_returns_tokens(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "first@example.com", "password": "a-strong-password", "name": "First User"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access_token"]
    assert data["refresh_token"]


async def test_register_then_registration_open_reports_closed(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "first@example.com", "password": "a-strong-password", "name": "First User"},
    )

    response = await client.get("/api/v1/auth/registration-open")
    assert response.json()["data"]["open"] is False


async def test_register_rejects_a_second_account(client: AsyncClient) -> None:
    first = await client.post(
        "/api/v1/auth/register",
        json={"email": "first@example.com", "password": "a-strong-password", "name": "First User"},
    )
    assert first.status_code == 200

    second = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "second@example.com",
            "password": "another-strong-password",
            "name": "Second User",
        },
    )
    assert second.status_code == 409


async def test_register_rejects_when_a_user_already_exists_via_seed(client: AsyncClient) -> None:
    """Same guard, but for a user created outside the API (e.g. scripts/seed.py)."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        await repository.create_user(
            session,
            email="seeded@example.com",
            hashed_password=hash_password("whatever"),
            name="Seeded User",
        )
        await session.commit()

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "a-strong-password", "name": "New User"},
    )
    assert response.status_code == 409


async def test_register_validates_password_length(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "first@example.com", "password": "short", "name": "First User"},
    )
    assert response.status_code == 422

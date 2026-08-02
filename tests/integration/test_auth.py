"""Integration tests for /api/v1/auth/* and /api/v1/profile - full request
cycle (real Postgres, all middleware) via httpx.AsyncClient.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.auth import repository
from app.core.database import get_sessionmaker
from app.core.security import hash_password
from app.main import app

TEST_EMAIL = "test.user@example.com"
TEST_PASSWORD = "correct-horse-battery-staple"
TEST_NAME = "Test User"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def seeded_user_id() -> str:
    """Create a user directly via the repository (bypassing the API, since
    there is no public registration endpoint) and return its id as a str.
    """
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        user = await repository.create_user(
            session,
            email=TEST_EMAIL,
            hashed_password=hash_password(TEST_PASSWORD),
            name=TEST_NAME,
        )
        await session.commit()
        return str(user.id)


async def test_login_with_correct_credentials_returns_token_pair(
    client: AsyncClient, seeded_user_id: str
) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


async def test_login_with_wrong_password_returns_401(
    client: AsyncClient, seeded_user_id: str
) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": "wrong-password"}
    )

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["message"]


async def test_login_with_unknown_email_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever"}
    )
    assert response.status_code == 401


async def test_profile_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/profile")
    assert response.status_code == 401


async def test_profile_returns_current_user_with_valid_token(
    client: AsyncClient, seeded_user_id: str
) -> None:
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    access_token = login_response.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/profile", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == TEST_EMAIL
    assert data["name"] == TEST_NAME
    assert data["currency"] == "INR"


async def test_update_profile_persists_changes(client: AsyncClient, seeded_user_id: str) -> None:
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = await client.patch(
        "/api/v1/profile", json={"city": "Ahmedabad", "dark_mode": True}, headers=headers
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["city"] == "Ahmedabad"
    assert data["dark_mode"] is True
    assert data["name"] == TEST_NAME  # untouched fields are unchanged


async def test_refresh_returns_new_working_token_pair(
    client: AsyncClient, seeded_user_id: str
) -> None:
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    refresh_token = login_response.json()["data"]["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()["data"]["access_token"]

    profile_response = await client.get(
        "/api/v1/profile", headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert profile_response.status_code == 200


async def test_an_access_token_cannot_be_used_to_refresh(
    client: AsyncClient, seeded_user_id: str
) -> None:
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    access_token = login_response.json()["data"]["access_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401


async def test_logout_invalidates_the_access_token_used_to_call_it(
    client: AsyncClient, seeded_user_id: str
) -> None:
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    logout_response = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 204

    # The same access token must now be rejected - credential_version moved on.
    profile_response = await client.get("/api/v1/profile", headers=headers)
    assert profile_response.status_code == 401


async def test_change_password_requires_correct_current_password(
    client: AsyncClient, seeded_user_id: str
) -> None:
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "totally-wrong", "new_password": "new-password-123"},
        headers=headers,
    )
    assert response.status_code == 401


async def test_change_password_then_login_with_new_password(
    client: AsyncClient, seeded_user_id: str
) -> None:
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    new_password = "brand-new-password-456"
    change_response = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": TEST_PASSWORD, "new_password": new_password},
        headers=headers,
    )
    assert change_response.status_code == 204

    # Old token is now invalid (credential_version bumped)...
    old_token_response = await client.get("/api/v1/profile", headers=headers)
    assert old_token_response.status_code == 401

    # ...but the new password logs in fine.
    relogin_response = await client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": new_password}
    )
    assert relogin_response.status_code == 200

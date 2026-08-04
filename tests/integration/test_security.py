"""Integration tests for /api/v1/security and /api/v1/profile/config."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.auth import repository
from app.core.database import get_sessionmaker
from app.core.security import hash_password
from app.main import app

TEST_EMAIL = "security.test@example.com"
TEST_PASSWORD = "correct-horse-battery-staple"
TEST_NAME = "Security Test User"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        await repository.create_user(
            session,
            email=TEST_EMAIL,
            hashed_password=hash_password(TEST_PASSWORD),
            name=TEST_NAME,
        )
        await session.commit()

    login = await client.post(
        "/api/v1/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_security_overview_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/security")
    assert response.status_code == 401


async def test_security_overview_returns_defaults(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/security", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["settings"]["pin_lock_enabled"] is True
    assert data["settings"]["auto_logout_minutes"] == 5
    assert isinstance(data["sessions"], list)
    assert isinstance(data["login_history"], list)


async def test_patch_security_settings(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.patch(
        "/api/v1/security/settings",
        headers=auth_headers,
        json={"hide_sensitive_amounts": True, "auto_logout_minutes": 15},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["hide_sensitive_amounts"] is True
    assert data["auto_logout_minutes"] == 15


async def test_repeated_login_reuses_same_device_session(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """Same browser fingerprint must not pile up identical trusted devices."""
    headers = {
        **auth_headers,
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0",
    }
    # Login again with the same UA (auth_headers already came from one login).
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        headers={"User-Agent": headers["User-Agent"]},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    overview = await client.get(
        "/api/v1/security",
        headers={"Authorization": f"Bearer {token}", "User-Agent": headers["User-Agent"]},
    )
    assert overview.status_code == 200
    sessions = overview.json()["data"]["sessions"]
    chrome = [
        s
        for s in sessions
        if s.get("user_agent") == headers["User-Agent"] or "Chrome" in s["device_label"]
    ]
    assert len(chrome) == 1
    assert chrome[0]["is_current"] is True


async def test_logout_clears_trusted_device_sessions(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    logout = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout.status_code == 204
    # Tokens are dead; re-login and confirm only the new session remains.
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        headers={"User-Agent": "Mozilla/5.0 Firefox/120.0"},
    )
    token = login.json()["data"]["access_token"]
    overview = await client.get(
        "/api/v1/security",
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "Mozilla/5.0 Firefox/120.0",
        },
    )
    sessions = overview.json()["data"]["sessions"]
    assert len(sessions) == 1
    assert sessions[0]["is_current"] is True


async def test_login_history_defaults_to_today(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/security/login-history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data["data"], list)
    assert data["page"] == 1
    assert data["size"] == 20
    assert "total" in data
    assert "pages" in data
    assert data["from_date"] is not None
    assert data["to_date"] is not None


async def test_login_history_rejects_inverted_range(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get(
        "/api/v1/security/login-history",
        headers=auth_headers,
        params={"from_date": "2026-08-10", "to_date": "2026-08-01"},
    )
    assert response.status_code == 422


async def test_profile_config_is_public(client: AsyncClient) -> None:
    response = await client.get("/api/v1/profile/config")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["auto_logout_minutes_options"] == [1, 5, 15, 30]
    assert data["currencies"] == ["INR"]
    assert len(data["options"]) == 19  # see configuration/catalog.py

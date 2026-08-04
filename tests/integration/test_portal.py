"""Integration test for GET / developer portal."""

from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_developer_portal_returns_html() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    assert "Developer Portal" in body
    assert "/docs" in body
    assert "/api/v1/health/live" in body

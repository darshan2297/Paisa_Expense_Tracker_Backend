"""Integration test for GET /api/v1/health.

Uses `httpx.AsyncClient` with `ASGITransport` to exercise the full app
(including all middleware: CORS, request-id, rate limiting, response
envelope, error handling) in-process, without needing a running server or a
real database connection.
"""

from httpx import ASGITransport, AsyncClient

from app.main import app


# No explicit marker needed: pyproject.toml sets `asyncio_mode = "auto"`
# for pytest-asyncio, so plain `async def` tests are picked up automatically.
async def test_health_check_returns_ok_envelope() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["status_code"] == 200
    assert body["data"]["status"] == "ok"
    assert "version" in body["data"]
    assert body["message"] is None
    assert body["errors"] is None

    # RequestIdMiddleware should have stamped a correlation id header.
    assert "x-request-id" in response.headers

"""Integration test for GET /openapi.json.

Swagger UI fetches this path directly and requires the raw OpenAPI document,
not the standard API response envelope.
"""

from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_openapi_json_is_not_enveloped() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200

    body = response.json()
    assert "openapi" in body
    assert "success" not in body
    assert body["info"]["title"] == "Paisa API"

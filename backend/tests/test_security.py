import pytest
from httpx import AsyncClient
from app.config import get_settings


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_rate_limiter_exceeded(client: AsyncClient):
    settings = get_settings()
    original_rate = settings.rate_limit_per_minute
    isolated_headers = {"x-forwarded-for": "203.0.113.199"}
    try:
        # Lower rate limit for test
        settings.rate_limit_per_minute = 3
        settings.rate_limit_enabled = True

        for _ in range(3):
            res = await client.get("/api/watchlist?device_id=test_rl", headers=isolated_headers)
            assert res.status_code in (200, 404, 422)

        # 4th request should be rate-limited
        blocked_res = await client.get("/api/watchlist?device_id=test_rl", headers=isolated_headers)
        assert blocked_res.status_code == 429
        assert "Retry-After" in blocked_res.headers
        assert "Too many requests" in blocked_res.json()["detail"]
    finally:
        settings.rate_limit_per_minute = original_rate


@pytest.mark.asyncio
async def test_api_key_auth(client: AsyncClient):
    settings = get_settings()
    original_key = settings.api_secret_key
    try:
        settings.api_secret_key = "test-secret-123"

        # Request without key should fail
        unauth_res = await client.get("/api/watchlist?device_id=test_auth")
        assert unauth_res.status_code == 401
        assert "Invalid or missing API key" in unauth_res.json()["detail"]

        # Health check is always exempt
        health_res = await client.get("/health")
        assert health_res.status_code == 200

        # Request with key should succeed
        auth_res = await client.get(
            "/api/watchlist?device_id=test_auth",
            headers={"x-api-key": "test-secret-123"}
        )
        assert auth_res.status_code == 200
    finally:
        settings.api_secret_key = original_key

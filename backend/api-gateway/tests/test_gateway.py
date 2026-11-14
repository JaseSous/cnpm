import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/api/gateway/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "api-gateway"

@pytest.mark.asyncio
async def test_protected_route_missing_token(client: AsyncClient):
    # Route yêu cầu auth nhưng không truyền token
    resp = await client.post("/api/pois", json={"title": "Test POI"})
    assert resp.status_code == 401
    assert resp.json()["detail"]["error_code"] == "MISSING_TOKEN"

@pytest.mark.asyncio
async def test_protected_route_invalid_token(client: AsyncClient):
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    resp = await client.post("/api/pois", json={"title": "Test POI"}, headers=headers)
    assert resp.status_code == 401
    assert resp.json()["detail"]["error_code"] == "INVALID_TOKEN"

@pytest.mark.asyncio
async def test_rbac_customer_denied_admin_route(client: AsyncClient, customer_token: str):
    headers = {"Authorization": f"Bearer {customer_token}"}
    # Customer cố gắng tạo POI (chỉ dành cho Admin)
    resp = await client.post("/api/pois", json={"title": "Test POI"}, headers=headers)
    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "PERMISSION_DENIED"

@pytest.mark.asyncio
async def test_rbac_staff_denied_admin_route(client: AsyncClient, staff_token: str):
    headers = {"Authorization": f"Bearer {staff_token}"}
    # Staff cố gắng xóa POI (chỉ dành cho Admin)
    resp = await client.delete("/api/pois/1", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "PERMISSION_DENIED"

@pytest.mark.asyncio
async def test_ip_rate_limiting(client: AsyncClient):
    from app.config import settings
    original_limit = settings.RATE_LIMIT_IP_MAX
    settings.RATE_LIMIT_IP_MAX = 2

    try:
        # Request 1: OK
        r1 = await client.get("/api/gateway/health", headers={"x-forwarded-for": "192.168.1.100"})
        assert r1.status_code == 200

        # Request 2: OK
        r2 = await client.get("/api/gateway/health", headers={"x-forwarded-for": "192.168.1.100"})
        assert r2.status_code == 200

        # Request 3: Exceeded -> 429
        r3 = await client.get("/api/gateway/health", headers={"x-forwarded-for": "192.168.1.100"})
        assert r3.status_code == 429
        assert r3.json()["detail"]["error_code"] == "IP_RATE_LIMIT_EXCEEDED"
    finally:
        settings.RATE_LIMIT_IP_MAX = original_limit

@pytest.mark.asyncio
async def test_reverse_proxy_downstream_connection_error(client: AsyncClient):
    # Gọi tới public route /api/auth/login khi auth service chưa bật -> 503
    resp = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "123"},
        headers={"x-forwarded-for": "192.168.1.200"}
    )
    assert resp.status_code == 503
    assert resp.json()["detail"]["error_code"] == "SERVICE_UNAVAILABLE"

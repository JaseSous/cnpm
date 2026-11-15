import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_admin_login_success(client: AsyncClient):
    """UC07: Đăng nhập admin thành công trả về JWT token"""
    res = await client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["username"] == "admin"
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_staff_login_success(client: AsyncClient):
    """UC07: Đăng nhập staff thành công trả về JWT token"""
    res = await client.post("/api/auth/login", json={
        "username": "staff01",
        "password": "staff123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "staff"
    assert data["username"] == "staff01"

@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """UC07-E1: Đăng nhập sai mật khẩu trả về 401 và số lần thử còn lại"""
    res = await client.post("/api/auth/login", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert res.status_code == 401
    detail = res.json()["detail"]
    assert detail["error_code"] == "INVALID_CREDENTIALS"
    assert "Còn 4 lần thử" in detail["message"]

@pytest.mark.asyncio
async def test_login_brute_force_lockout(client: AsyncClient):
    """UC07-E3: Đăng nhập sai 5 lần liên tiếp sẽ bị khóa tài khoản (423 Locked)"""
    for i in range(4):
        res = await client.post("/api/auth/login", json={
            "username": "staff01",
            "password": f"wrong_{i}"
        })
        assert res.status_code == 401

    # Lần thứ 5 sai -> Khóa tài khoản
    res_lock = await client.post("/api/auth/login", json={
        "username": "staff01",
        "password": "wrong_5"
    })
    assert res_lock.status_code == 423
    assert res_lock.json()["detail"]["error_code"] == "ACCOUNT_LOCKED"

    # Thử đăng nhập lại dù đúng mật khẩu vẫn bị từ chối do đang bị khóa
    res_retry = await client.post("/api/auth/login", json={
        "username": "staff01",
        "password": "staff123"
    })
    assert res_retry.status_code == 423
    assert res_retry.json()["detail"]["error_code"] == "ACCOUNT_LOCKED"

@pytest.mark.asyncio
async def test_get_me_profile(client: AsyncClient):
    """Lấy thông tin profile với token hợp lệ"""
    login_res = await client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_res.json()["access_token"]

    me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["username"] == "admin"
    assert user_data["role"] == "admin"

@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Gọi /api/auth/me không có token trả về 401"""
    res = await client.get("/api/auth/me")
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_get_dashboard_stats_success(client: AsyncClient):
    """Lấy dữ liệu thống kê Dashboard với token admin"""
    login_res = await client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_res.json()["access_token"]

    res = await client.get("/api/auth/dashboard-stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "codes_created_today" in data
    assert "total_codes_created" in data
    assert "pending_codes" in data
    assert "active_sessions" in data
    assert isinstance(data["codes_created_today"], int)
    assert isinstance(data["total_codes_created"], int)
    assert isinstance(data["pending_codes"], int)
    assert isinstance(data["active_sessions"], int)
    assert "server_time" in data
    assert "recent_sessions" in data

@pytest.mark.asyncio
async def test_get_dashboard_stats_unauthorized(client: AsyncClient):
    """Gọi /api/auth/dashboard-stats không có token trả về 401"""
    res = await client.get("/api/auth/dashboard-stats")
    assert res.status_code == 401

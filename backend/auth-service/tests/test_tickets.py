import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_staff_create_ticket_success(client: AsyncClient):
    """UC08: Staff tạo mã vé tiền mặt thành công"""
    # 1. Staff login
    login_res = await client.post("/api/auth/login", json={
        "username": "staff01",
        "password": "staff123"
    })
    token = login_res.json()["access_token"]

    # 2. Tạo vé
    res = await client.post(
        "/api/auth/tickets",
        json={"package_id": 1, "amount": 50000.0, "payment_method": "cash"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    ticket = res.json()
    assert len(ticket["shorted_code"]) == 10
    assert ticket["expires_in"] == 1800
    assert ticket["amount"] == 50000.0
    assert "session_id" in ticket

@pytest.mark.asyncio
async def test_create_ticket_forbidden_without_auth(client: AsyncClient):
    """Không có token hoặc không phải staff/admin không được phép tạo vé"""
    res = await client.post(
        "/api/auth/tickets",
        json={"package_id": 1, "amount": 50000.0}
    )
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_customer_verify_code_success(client: AsyncClient):
    """UC01: Du khách đổi mã vé lấy JWT access_token thành công"""
    # 1. Staff tạo vé
    login_res = await client.post("/api/auth/login", json={
        "username": "staff01",
        "password": "staff123"
    })
    token = login_res.json()["access_token"]

    ticket_res = await client.post(
        "/api/auth/tickets",
        json={"package_id": 1, "amount": 50000.0},
        headers={"Authorization": f"Bearer {token}"}
    )
    code = ticket_res.json()["shorted_code"]
    session_id = ticket_res.json()["session_id"]

    # 2. Du khách đổi mã vé
    verify_res = await client.post(
        "/api/auth/verify-code",
        json={"shorted_code": code}
    )
    assert verify_res.status_code == 200
    customer_token = verify_res.json()
    assert "access_token" in customer_token
    assert customer_token["role"] == "customer"
    assert customer_token["session_id"] == session_id

@pytest.mark.asyncio
async def test_verify_code_atomic_getdel(client: AsyncClient):
    """UC01: Mã vé sau khi đổi một lần sẽ bị xóa (GETDEL) và không thể dùng lại"""
    # 1. Staff tạo vé
    login_res = await client.post("/api/auth/login", json={
        "username": "staff01",
        "password": "staff123"
    })
    token = login_res.json()["access_token"]

    ticket_res = await client.post(
        "/api/auth/tickets",
        json={"package_id": 1, "amount": 50000.0},
        headers={"Authorization": f"Bearer {token}"}
    )
    code = ticket_res.json()["shorted_code"]

    # 2. Đổi vé lần đầu -> Thành công
    res1 = await client.post("/api/auth/verify-code", json={"shorted_code": code})
    assert res1.status_code == 200

    # 3. Đổi vé lần thứ 2 với cùng mã -> Bị từ chối (401 CODE_INVALID_OR_EXPIRED)
    res2 = await client.post("/api/auth/verify-code", json={"shorted_code": code})
    assert res2.status_code == 401
    assert res2.json()["detail"]["error_code"] == "CODE_INVALID_OR_EXPIRED"

@pytest.mark.asyncio
async def test_verify_code_invalid_format(client: AsyncClient):
    """Mã vé sai độ dài (không đủ 10 ký tự) trả về mã lỗi 422"""
    res = await client.post("/api/auth/verify-code", json={"shorted_code": "SHORT"})
    assert res.status_code in [400, 422]

@pytest.mark.asyncio
async def test_get_ticket_packages(client: AsyncClient):
    """Lấy danh mục các gói vé mở bán"""
    res = await client.get("/api/auth/packages")
    assert res.status_code == 200
    pkgs = res.json()
    assert len(pkgs) >= 1
    assert pkgs[0]["package_name"] == "Vé tham quan Chùa Linh Ứng"

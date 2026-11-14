import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    resp = await async_client.get("/api/chatbot/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "chatbot-service"

@pytest.mark.asyncio
async def test_ask_chatbot_unauthorized(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/chatbot/ask",
        json={"question": "Chùa Linh Ứng có gì?", "lang": "vi"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["error_code"] == "MISSING_TOKEN"

@pytest.mark.asyncio
async def test_ask_chatbot_forbidden_role(async_client: AsyncClient, staff_token: str):
    headers = {"Authorization": f"Bearer {staff_token}"}
    resp = await async_client.post(
        "/api/chatbot/ask",
        json={"question": "Chùa Linh Ứng có gì?", "lang": "vi"},
        headers=headers
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "PERMISSION_DENIED"

@pytest.mark.asyncio
async def test_ask_chatbot_success(async_client: AsyncClient, customer_token: str):
    headers = {"Authorization": f"Bearer {customer_token}"}
    resp = await async_client.post(
        "/api/chatbot/ask",
        json={"question": "Chùa Linh Ứng xây dựng năm nào?", "lang": "vi"},
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert data["cached"] is False

@pytest.mark.asyncio
async def test_ask_chatbot_faq_cache_hit(async_client: AsyncClient, customer_token: str):
    headers = {"Authorization": f"Bearer {customer_token}"}
    payload = {"question": "Giờ mở cửa Chùa Linh Ứng?", "lang": "vi"}

    # Lần 1: Chưa có trong cache -> cached=False
    resp1 = await async_client.post("/api/chatbot/ask", json=payload, headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["cached"] is False

    # Lần 2: Cùng câu hỏi -> FAQ Cache HIT -> cached=True
    resp2 = await async_client.post("/api/chatbot/ask", json=payload, headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["cached"] is True
    assert resp2.json()["answer"] == resp1.json()["answer"]

@pytest.mark.asyncio
async def test_ask_chatbot_rate_limit(async_client: AsyncClient, customer_token: str):
    from app.config import settings
    headers = {"Authorization": f"Bearer {customer_token}"}

    # Đặt giới hạn tạm thời thành 2 để test
    original_limit = settings.RATE_LIMIT_CHAT_MAX_PER_SESSION
    settings.RATE_LIMIT_CHAT_MAX_PER_SESSION = 2

    try:
        # Lần 1: OK
        r1 = await async_client.post("/api/chatbot/ask", json={"question": "Câu hỏi 1?", "lang": "vi"}, headers=headers)
        assert r1.status_code == 200

        # Lần 2: OK
        r2 = await async_client.post("/api/chatbot/ask", json={"question": "Câu hỏi 2?", "lang": "vi"}, headers=headers)
        assert r2.status_code == 200

        # Lần 3: Vượt quá giới hạn 2 câu hỏi -> 429 CHAT_RATE_LIMIT
        r3 = await async_client.post("/api/chatbot/ask", json={"question": "Câu hỏi 3?", "lang": "vi"}, headers=headers)
        assert r3.status_code == 429
        assert r3.json()["detail"]["error_code"] == "CHAT_RATE_LIMIT"
    finally:
        settings.RATE_LIMIT_CHAT_MAX_PER_SESSION = original_limit

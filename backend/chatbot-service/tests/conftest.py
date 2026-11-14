import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from jose import jwt

# Đảm bảo đường dẫn import tới app của chatbot-service
current_dir = Path(__file__).resolve().parent
service_root = current_dir.parent
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

from app.config import settings
from app.main import app
from app.services import redis_service, qdrant_service

@pytest_asyncio.fixture(autouse=True)
async def setup_test_env():
    # Đảm bảo Qdrant dùng in-memory và redis store được làm mới
    redis_service.in_memory._faq_store.clear()
    redis_service.in_memory._rate_limits.clear()
    qdrant_service.ensure_collection_exists()
    yield

@pytest.fixture
def customer_token() -> str:
    """Tạo JWT Token hợp lệ cho vai trò khách du lịch"""
    payload = {
        "sub": "customer:session_test_001",
        "session_id": "session_test_001",
        "role": "customer",
        "exp": datetime.utcnow() + timedelta(hours=2)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

@pytest.fixture
def admin_token() -> str:
    """Tạo JWT Token hợp lệ cho Admin"""
    payload = {
        "sub": "1",
        "username": "admin",
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

@pytest.fixture
def staff_token() -> str:
    """Tạo JWT Token cho Staff (không có quyền truy cập Chatbot)"""
    payload = {
        "sub": "2",
        "username": "staff",
        "role": "staff",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

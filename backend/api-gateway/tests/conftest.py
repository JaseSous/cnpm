import sys
from pathlib import Path
from datetime import datetime, timedelta
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from jose import jwt

gateway_root = Path(__file__).resolve().parent.parent
if str(gateway_root) not in sys.path:
    sys.path.insert(0, str(gateway_root))

from app.config import settings
from app.main import app
from app.services.rate_limiter import rate_limiter

@pytest_asyncio.fixture(autouse=True)
async def setup_env():
    rate_limiter.in_memory._ip_counts.clear()
    yield

@pytest.fixture
def admin_token():
    payload = {
        "sub": "1",
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

@pytest.fixture
def staff_token():
    payload = {
        "sub": "2",
        "role": "staff",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

@pytest.fixture
def customer_token():
    payload = {
        "sub": "customer:123",
        "role": "customer",
        "session_id": "123",
        "exp": datetime.utcnow() + timedelta(hours=2)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

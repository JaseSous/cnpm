import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from app.database import Base, get_db
from app.models import User, TicketPackage
from app.services.security import hash_password
from app.services.redis_client import InMemoryRedisClient, get_redis
from app.main import app

# Sử dụng SQLite in-memory cho Unit Tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False}
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

test_redis_client = InMemoryRedisClient()

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        yield session

async def override_get_redis():
    return test_redis_client

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_redis] = override_get_redis

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed dữ liệu ban đầu cho bài test
    async with TestAsyncSessionLocal() as session:
        admin_user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin",
            is_active=True
        )
        staff_user = User(
            username="staff01",
            password_hash=hash_password("staff123"),
            role="staff",
            is_active=True
        )
        package_standard = TicketPackage(
            package_name="Vé tham quan Chùa Linh Ứng",
            price=50000.00,
            description="Vé tiêu chuẩn",
            is_active=True
        )
        session.add_all([admin_user, staff_user, package_standard])
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Xóa sạch store redis test
    test_redis_client._store.clear()

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

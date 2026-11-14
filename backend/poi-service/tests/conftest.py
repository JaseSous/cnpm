import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport
from jose import jwt

from app.database import Base, get_db
from app.models import SupportedLanguage, SystemMetadata
from app.config import settings
from app.main import app

# In-memory test DB
TEST_POI_DB_URL = "sqlite+aiosqlite:///:memory:"

test_poi_engine = create_async_engine(
    TEST_POI_DB_URL,
    connect_args={"check_same_thread": False}
)

TestPOISessionLocal = async_sessionmaker(
    bind=test_poi_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestPOISessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_poi_test_db():
    async with test_poi_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed 15 languages & SystemMetadata
    async with TestPOISessionLocal() as session:
        languages = [
            {"code": "vi", "name": "Vietnamese", "native": "Tiếng Việt", "fallback": True, "tts": True},
            {"code": "en", "name": "English", "native": "English", "fallback": False, "tts": True},
            {"code": "zh", "name": "Chinese", "native": "中文 (简体)", "fallback": False, "tts": True},
            {"code": "ja", "name": "Japanese", "native": "日本語", "fallback": False, "tts": True},
            {"code": "ko", "name": "Korean", "native": "한국어", "fallback": False, "tts": True},
            {"code": "fr", "name": "French", "native": "Français", "fallback": False, "tts": True},
            {"code": "de", "name": "German", "native": "Deutsch", "fallback": False, "tts": True},
            {"code": "es", "name": "Spanish", "native": "Español", "fallback": False, "tts": True},
            {"code": "th", "name": "Thai", "native": "ไทย", "fallback": False, "tts": True},
            {"code": "ru", "name": "Russian", "native": "Русский", "fallback": False, "tts": True},
            {"code": "pt", "name": "Portuguese", "native": "Português", "fallback": False, "tts": True},
            {"code": "it", "name": "Italian", "native": "Italiano", "fallback": False, "tts": True},
            {"code": "id", "name": "Indonesian", "native": "Bahasa Indonesia", "fallback": False, "tts": True},
            {"code": "ar", "name": "Arabic", "native": "العربية", "fallback": False, "tts": True},
            {"code": "hi", "name": "Hindi", "native": "हिन्दी", "fallback": False, "tts": True},
        ]
        for l in languages:
            session.add(SupportedLanguage(
                language_code=l["code"],
                language_name=l["name"],
                native_name=l["native"],
                is_fallback=l["fallback"],
                tts_supported=l["tts"],
                is_active=True
            ))
        session.add(SystemMetadata(config_key="poi_data_version", data_version=1))
        await session.commit()

    yield

    async with test_poi_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.fixture
def admin_token():
    return jwt.encode(
        {"user_id": 1, "username": "admin", "role": "admin"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

@pytest.fixture
def customer_token():
    return jwt.encode(
        {"session_id": "test-session-123", "role": "customer"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

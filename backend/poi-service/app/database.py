import os
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Đảm bảo thư mục lưu file database tồn tại nếu dùng SQLite
if settings.POI_DB_URL.startswith("sqlite"):
    db_path = settings.POI_DB_URL.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    settings.POI_DB_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if settings.POI_DB_URL.startswith("sqlite") else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

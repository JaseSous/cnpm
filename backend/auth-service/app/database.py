import os
import re
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Hàm chuẩn hóa URL database cho SQLAlchemy Async (tự động thêm driver asyncpg nếu là Postgres và xử lý IPv4 cho Supabase)
def normalize_async_db_url(url: str) -> str:
    url = url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Supabase Direct host (db.<ref>.supabase.co) là IPv6-only.
    # Render Free Tier không có mạng IPv6 nên sẽ báo lỗi 'Network is unreachable'.
    # Tự động chuyển đổi sang Supabase Connection Pooler IPv4:
    if "supabase.co" in url and "db." in url:
        match = re.search(r"db\.([a-zA-Z0-9]+)\.supabase\.co", url)
        if match:
            project_ref = match.group(1)
            url = url.replace(f"db.{project_ref}.supabase.co", "aws-0-ap-southeast-1.pooler.supabase.com")
            url = re.sub(r":5432(?=/|\?|$)", ":6543", url)
            if "://postgres:" in url:
                url = url.replace("://postgres:", f"://postgres.{project_ref}:", 1)
            elif "://postgres@" in url:
                url = url.replace("://postgres@", f"://postgres.{project_ref}@", 1)

    return url

db_url = normalize_async_db_url(settings.AUTH_DB_URL)

# Đảm bảo thư mục lưu file database tồn tại nếu dùng SQLite
if db_url.startswith("sqlite"):
    db_path = db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Tắt statement cache cho các connection pooler như Supavisor / PgBouncer
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0
    }

engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    connect_args=connect_args
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

import os
import re
import urllib.parse
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Hàm chuẩn hóa URL database cho SQLAlchemy Async (tự động thêm driver asyncpg nếu là Postgres và xử lý IPv4 cho Supabase)
def normalize_async_db_url(url: str) -> str:
    url = url.strip()
    if url.startswith("sqlite"):
        return url

    # Tự động encode ký tự đặc biệt trong mật khẩu nếu có
    match = re.match(r"^([a-zA-Z0-9\+\-]+://)([^:]+):(.*)@([^@/]+)(/.*)?$", url)
    if match:
        proto, user, pwd, host, rest = match.groups()
        rest = rest or ""
        pwd_decoded = urllib.parse.unquote(pwd)
        pwd_encoded = urllib.parse.quote_plus(pwd_decoded)
        url = f"{proto}{user}:{pwd_encoded}@{host}{rest}"

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Supabase Direct host (db.<ref>.supabase.co) là IPv6-only.
    # Render Free Tier không có mạng IPv6 nên sẽ báo lỗi 'Network is unreachable'.
    # Tự động chuyển đổi sang Supabase Connection Pooler IPv4 (mặc định vùng ap-southeast-2):
    if "supabase.co" in url and "db." in url:
        match = re.search(r"db\.([a-zA-Z0-9]+)\.supabase\.co", url)
        if match:
            project_ref = match.group(1)
            region = os.environ.get("SUPABASE_REGION", "ap-southeast-2")
            url = url.replace(f"db.{project_ref}.supabase.co", f"aws-0-{region}.pooler.supabase.com")
            if "://postgres:" in url:
                url = url.replace("://postgres:", f"://postgres.{project_ref}:", 1)
            elif "://postgres@" in url:
                url = url.replace("://postgres@", f"://postgres.{project_ref}@", 1)

    return url

db_url = normalize_async_db_url(settings.POI_DB_URL)

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
    pool_pre_ping=True,
    pool_recycle=300,
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

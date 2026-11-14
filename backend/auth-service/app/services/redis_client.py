import time
import logging
from typing import Optional, Dict, Tuple
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger("auth-redis")

class InMemoryRedisClient:
    """In-memory Redis fallback hỗ trợ phát triển offline hoặc chạy unit tests không cần Docker"""
    def __init__(self):
        self._store: Dict[str, Tuple[str, Optional[float]]] = {}
        logger.warning("Sử dụng In-memory Redis Store dự phòng (offline mode).")

    def _is_expired(self, key: str) -> bool:
        if key not in self._store:
            return True
        val, expire_at = self._store[key]
        if expire_at and time.time() > expire_at:
            del self._store[key]
            return True
        return False

    async def get(self, key: str) -> Optional[str]:
        if self._is_expired(key):
            return None
        return self._store[key][0]

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        expire_at = time.time() + ex if ex else None
        self._store[key] = (str(value), expire_at)
        return True

    async def getdel(self, key: str) -> Optional[str]:
        if self._is_expired(key):
            return None
        val, _ = self._store.pop(key)
        return val

    async def exists(self, key: str) -> int:
        return 0 if self._is_expired(key) else 1

    async def incr(self, key: str) -> int:
        if self._is_expired(key):
            self._store[key] = ("1", None)
            return 1
        current_val, exp = self._store[key]
        new_val = int(current_val) + 1
        self._store[key] = (str(new_val), exp)
        return new_val

    async def expire(self, key: str, seconds: int) -> bool:
        if self._is_expired(key):
            return False
        val, _ = self._store[key]
        self._store[key] = (val, time.time() + seconds)
        return True

    async def ttl(self, key: str) -> int:
        if self._is_expired(key):
            return -2
        _, exp = self._store[key]
        if not exp:
            return -1
        return max(0, int(exp - time.time()))

class RedisService:
    def __init__(self):
        self.client = None
        self._is_connected = False

    async def get_client(self):
        if self.client is None:
            try:
                real_client = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                await real_client.ping()
                self.client = real_client
                self._is_connected = True
                logger.info(f"Đã kết nối thành công tới Redis: {settings.REDIS_URL}")
            except Exception as e:
                logger.warning(f"Không thể kết nối Redis ({e}). Chuyển sang In-memory fallback.")
                self.client = InMemoryRedisClient()
                self._is_connected = False
        return self.client

redis_service = RedisService()

async def get_redis():
    """Dependency cung cấp client Redis cho các route FastAPI"""
    return await redis_service.get_client()

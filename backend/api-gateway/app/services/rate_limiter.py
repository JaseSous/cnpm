import time
import logging
from typing import Tuple, Dict, Optional
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger("gateway-rate-limiter")

class InMemoryIPRateLimiter:
    def __init__(self):
        self._ip_counts: Dict[str, Tuple[int, float]] = {}

    def check_and_increment(self, ip: str, max_limit: int, window_secs: int) -> Tuple[bool, int]:
        now = time.time()
        if ip in self._ip_counts:
            count, expire_at = self._ip_counts[ip]
            if expire_at > now:
                new_count = count + 1
                self._ip_counts[ip] = (new_count, expire_at)
                return new_count <= max_limit, new_count

        self._ip_counts[ip] = (1, now + window_secs)
        return True, 1

class GatewayRateLimiter:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.in_memory = InMemoryIPRateLimiter()
        self._is_connected = False

    async def connect(self):
        try:
            base_url = settings.REDIS_URL.rstrip("/")
            if base_url.count("/") >= 3:
                base_parts = base_url.rsplit("/", 1)
                redis_url = f"{base_parts[0]}/{settings.REDIS_DB}"
            else:
                redis_url = f"{base_url}/{settings.REDIS_DB}"

            self.redis = aioredis.from_url(redis_url, decode_responses=True, socket_timeout=3)
            await self.redis.ping()
            self._is_connected = True
            logger.info("Kết nối Redis DB 0 thành công cho Gateway Rate Limiter!")
        except Exception as e:
            logger.warning(f"Không thể kết nối Redis ({e}). Dùng In-memory Rate Limiter fallback.")
            self._is_connected = False

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            self._is_connected = False

    async def is_allowed(self, ip: str) -> Tuple[bool, int]:
        """Kiểm tra giới hạn số request từ địa chỉ IP (mặc định: 100 req/giờ)"""
        max_limit = settings.RATE_LIMIT_IP_MAX
        window = settings.RATE_LIMIT_IP_WINDOW_SECONDS
        key = f"ratelimit:ip:{ip}"

        if self._is_connected and self.redis:
            try:
                current = await self.redis.incr(key)
                if current == 1:
                    await self.redis.expire(key, window)
                return current <= max_limit, current
            except Exception as e:
                logger.warning(f"Lỗi kiểm tra Rate Limit trên Redis ({e})")

        return self.in_memory.check_and_increment(ip, max_limit, window)

rate_limiter = GatewayRateLimiter()

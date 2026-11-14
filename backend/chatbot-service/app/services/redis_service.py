import time
import logging
from typing import Optional, Tuple, Dict, Any
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger("chatbot-redis")

class InMemoryChatbotStore:
    """Kho lưu trữ trong bộ nhớ tạm thời khi Redis ngoại vi chưa sẵn sàng"""
    def __init__(self):
        self._faq_store: Dict[str, Tuple[str, float]] = {}
        self._rate_limits: Dict[str, Tuple[int, float]] = {}

    def get_faq(self, key: str) -> Optional[str]:
        now = time.time()
        if key in self._faq_store:
            val, expire_at = self._faq_store[key]
            if expire_at > now:
                return val
            del self._faq_store[key]
        return None

    def set_faq(self, key: str, value: str, ttl: int = 86400):
        expire_at = time.time() + ttl
        self._faq_store[key] = (value, expire_at)

    def incr_rate_limit(self, key: str, window_seconds: int = 86400) -> int:
        now = time.time()
        if key in self._rate_limits:
            count, expire_at = self._rate_limits[key]
            if expire_at > now:
                new_count = count + 1
                self._rate_limits[key] = (new_count, expire_at)
                return new_count
        # Reset hoặc mới
        self._rate_limits[key] = (1, now + window_seconds)
        return 1

    def invalidate(self, pattern: str = "faq:*") -> int:
        count = 0
        keys_to_del = []
        if pattern == "faq:*" or not pattern:
            keys_to_del = list(self._faq_store.keys())
        else:
            prefix = pattern.replace("*", "")
            keys_to_del = [k for k in self._faq_store.keys() if k.startswith(prefix)]
        for k in keys_to_del:
            del self._faq_store[k]
            count += 1
        return count


class RedisChatbotService:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.in_memory = InMemoryChatbotStore()
        self._is_connected = False

    async def connect(self):
        """Khởi tạo kết nối tới Redis DB 1"""
        try:
            # Tách URL và chỉ định DB 1
            base_url = settings.REDIS_URL.rstrip("/")
            if base_url.count("/") >= 3:
                # Đã có số DB, thay thế bằng DB_CHATBOT
                base_parts = base_url.rsplit("/", 1)
                redis_db_url = f"{base_parts[0]}/{settings.REDIS_DB_CHATBOT}"
            else:
                redis_db_url = f"{base_url}/{settings.REDIS_DB_CHATBOT}"

            self.redis = aioredis.from_url(
                redis_db_url,
                decode_responses=True,
                socket_timeout=3
            )
            await self.redis.ping()
            self._is_connected = True
            logger.info(f"Kết nối Redis DB {settings.REDIS_DB_CHATBOT} thành công cho Chatbot Service!")
        except Exception as e:
            logger.warning(f"Không thể kết nối tới Redis DB {settings.REDIS_DB_CHATBOT} ({e}). Sử dụng In-memory Store.")
            self._is_connected = False

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            self._is_connected = False

    async def get_faq_cache(self, lang: str, question_hash: str) -> Optional[str]:
        """Lấy câu trả lời FAQ từ Cache theo ngôn ngữ và hash câu hỏi"""
        key = f"faq:{lang}:{question_hash}"
        if self._is_connected and self.redis:
            try:
                return await self.redis.get(key)
            except Exception as e:
                logger.warning(f"Lỗi khi đọc FAQ Cache Redis ({e})")
        return self.in_memory.get_faq(key)

    async def set_faq_cache(
        self,
        lang: str,
        question_hash: str,
        answer: str,
        ttl: int = 86400
    ):
        """Lưu câu trả lời vào FAQ Cache với TTL 24h"""
        key = f"faq:{lang}:{question_hash}"
        if self._is_connected and self.redis:
            try:
                await self.redis.set(key, answer, ex=ttl)
                return
            except Exception as e:
                logger.warning(f"Lỗi khi ghi FAQ Cache Redis ({e})")
        self.in_memory.set_faq(key, answer, ttl)

    async def check_and_increment_rate_limit(
        self,
        session_id: str,
        limit: int = 30
    ) -> Tuple[bool, int]:
        """
        Kiểm tra và tăng số lượt hỏi của phiên chat du khách.
        Tối đa 30 câu hỏi / phiên (khoảng thời gian vé còn hiệu lực).
        Trả về: (is_allowed, current_count)
        """
        key = f"ratelimit:chat:{session_id}"
        current = 0
        if self._is_connected and self.redis:
            try:
                current = await self.redis.incr(key)
                if current == 1:
                    # Đặt expire 24h
                    await self.redis.expire(key, 86400)
            except Exception as e:
                logger.warning(f"Lỗi khi kiểm tra Chat Rate Limit Redis ({e})")
                current = self.in_memory.incr_rate_limit(key)
        else:
            current = self.in_memory.incr_rate_limit(key)

        is_allowed = current <= limit
        return is_allowed, current

    async def invalidate_faq_cache(self, pattern: str = "faq:*") -> int:
        """Xóa toàn bộ hoặc một phần FAQ Cache khi nội dung POI thay đổi"""
        cleared = 0
        if self._is_connected and self.redis:
            try:
                keys = []
                async for key in self.redis.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    cleared = await self.redis.delete(*keys)
                logger.info(f"Đã xóa {cleared} keys FAQ Cache trên Redis")
            except Exception as e:
                logger.warning(f"Lỗi khi xóa FAQ Cache Redis ({e})")
        
        mem_cleared = self.in_memory.invalidate(pattern)
        return max(cleared, mem_cleared)

redis_service = RedisChatbotService()

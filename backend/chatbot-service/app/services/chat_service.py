import re
import json
import hashlib
import logging
from typing import Tuple, Optional, Dict, Any, List

from fastapi import HTTPException, status
from app.config import settings
from app.services.redis_service import redis_service
from app.schemas.chat import ChatAskResponse, SourceItem

logger = logging.getLogger("chat-service")

def normalize_question(question: str) -> Tuple[str, str]:
    """
    Chuẩn hóa câu hỏi và sinh mã SHA256:
    - Bỏ khoảng trắng đầu đuôi
    - Chuyển thành chữ thường
    - Rút gọn nhiều khoảng trắng liên tiếp
    - Trả về: (câu hỏi đã chuẩn hóa, chuỗi hash SHA256)
    """
    q = (question or "").strip().lower()
    q = re.sub(r"\s+", " ", q)
    q_hash = hashlib.sha256(q.encode("utf-8")).hexdigest()
    return q, q_hash

async def check_chat_rate_limit(session_id: str):
    """Kiểm tra giới hạn tần suất chat theo phiên du khách (30 câu/phiên)"""
    allowed, count = await redis_service.check_and_increment_rate_limit(
        session_id=session_id,
        limit=settings.RATE_LIMIT_CHAT_MAX_PER_SESSION
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error_code": "CHAT_RATE_LIMIT",
                "message": f"Bạn đã đạt giới hạn tối đa {settings.RATE_LIMIT_CHAT_MAX_PER_SESSION} câu hỏi trong phiên tham quan này.",
                "current_count": count
            }
        )

async def get_cached_answer(lang: str, question_hash: str) -> Optional[ChatAskResponse]:
    """Kiểm tra FAQ Cache trên Redis DB 1"""
    cached_data = await redis_service.get_faq_cache(lang=lang, question_hash=question_hash)
    if cached_data:
        try:
            parsed = json.loads(cached_data)
            return ChatAskResponse(
                answer=parsed.get("answer", ""),
                sources=[
                    SourceItem(**s) for s in parsed.get("sources", [])
                ],
                cached=True,
                lang=lang
            )
        except Exception:
            return None
    return None

async def save_cached_answer(lang: str, question_hash: str, response: ChatAskResponse):
    """Lưu câu trả lời vào FAQ Cache Redis DB 1"""
    data = {
        "answer": response.answer,
        "sources": [s.model_dump() for s in response.sources]
    }
    await redis_service.set_faq_cache(
        lang=lang,
        question_hash=question_hash,
        answer=json.dumps(data, ensure_ascii=False),
        ttl=settings.FAQ_CACHE_TTL_SECONDS
    )

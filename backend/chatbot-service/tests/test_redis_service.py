import pytest
from app.services.redis_service import redis_service

@pytest.mark.asyncio
async def test_faq_cache_lifecycle():
    lang = "vi"
    q_hash = "abc123hash"
    answer = '{"answer": "Tượng Phật Bà cao 67m", "sources": []}'

    # Chưa lưu cache
    cached = await redis_service.get_faq_cache(lang=lang, question_hash=q_hash)
    assert cached is None

    # Lưu cache
    await redis_service.set_faq_cache(lang=lang, question_hash=q_hash, answer=answer, ttl=10)

    # Đọc lại cache
    cached = await redis_service.get_faq_cache(lang=lang, question_hash=q_hash)
    assert cached == answer

    # Xóa cache
    cleared = await redis_service.invalidate_faq_cache("faq:*")
    assert cleared >= 1

    # Kiểm tra sau khi xóa
    cached = await redis_service.get_faq_cache(lang=lang, question_hash=q_hash)
    assert cached is None

@pytest.mark.asyncio
async def test_rate_limit_increment():
    session_id = "test_sess_limit"
    limit = 3

    # Lần 1
    allowed, count = await redis_service.check_and_increment_rate_limit(session_id, limit=limit)
    assert allowed is True
    assert count == 1

    # Lần 2
    allowed, count = await redis_service.check_and_increment_rate_limit(session_id, limit=limit)
    assert allowed is True
    assert count == 2

    # Lần 3
    allowed, count = await redis_service.check_and_increment_rate_limit(session_id, limit=limit)
    assert allowed is True
    assert count == 3

    # Lần 4 (vượt quá)
    allowed, count = await redis_service.check_and_increment_rate_limit(session_id, limit=limit)
    assert allowed is False
    assert count == 4

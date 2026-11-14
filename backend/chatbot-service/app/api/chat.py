import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, status

from app.schemas.chat import ChatAskRequest, ChatAskResponse
from app.services.security import require_customer_or_admin
from app.services.chat_service import (
    normalize_question,
    check_chat_rate_limit,
    get_cached_answer,
    save_cached_answer
)

logger = logging.getLogger("chat-api")

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot AI"])

@router.post(
    "/ask",
    response_model=ChatAskResponse,
    status_code=status.HTTP_200_OK,
    summary="Hỏi đáp thông minh về Chùa Linh Ứng (UC03)"
)
async def ask_chatbot(
    request: ChatAskRequest,
    current_user: Dict[str, Any] = Depends(require_customer_or_admin)
):
    """
    Điểm cuối tiếp nhận câu hỏi của du khách:
    1. Chuẩn hóa câu hỏi & tạo SHA256 hash
    2. Kiểm tra FAQ Cache (Redis DB 1) -> Trả ngay nếu đã có (cache hit)
    3. Kiểm tra Rate Limit (tối đa 30 câu hỏi / phiên)
    4. Tìm kiếm tri thức liên quan (Qdrant) & Gọi LLM (Gemini) sinh câu trả lời
    5. Lưu kết quả vào FAQ Cache và trả về du khách
    """
    session_id = current_user.get("session_id") or current_user.get("sub", "customer_session")
    lang = (request.lang or "vi").lower()

    # 1. Chuẩn hóa câu hỏi
    norm_question, q_hash = normalize_question(request.question)

    # 2. Kiểm tra FAQ Cache
    cached_response = await get_cached_answer(lang=lang, question_hash=q_hash)
    if cached_response:
        logger.info(f"FAQ Cache HIT cho câu hỏi '{norm_question[:40]}...' ({lang})")
        return cached_response

    # 3. Kiểm tra Rate Limit
    await check_chat_rate_limit(session_id=session_id)

    # 4. Thực thi RAG Pipeline (Gemini Embedding + Qdrant Search + Gemini LLM)
    from app.services.rag_service import generate_rag_answer
    response = await generate_rag_answer(
        question=norm_question,
        lang=lang,
        session_id=session_id
    )

    # 5. Lưu vào FAQ Cache nếu có câu trả lời hợp lệ
    if response and response.answer:
        await save_cached_answer(lang=lang, question_hash=q_hash, response=response)

    return response

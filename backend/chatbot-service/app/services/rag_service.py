import logging
from typing import Optional
from app.schemas.chat import ChatAskResponse, SourceItem

logger = logging.getLogger("rag-service")

async def generate_rag_answer(
    question: str,
    lang: str = "vi",
    session_id: str = ""
) -> ChatAskResponse:
    """Hàm khung sinh câu trả lời RAG (sẽ hoàn thiện cùng Gemini ở Commit 3)"""
    return ChatAskResponse(
        answer=f"Chào mừng bạn đến với Chùa Linh Ứng! Bạn đang hỏi: '{question}'.",
        sources=[],
        cached=False,
        lang=lang
    )

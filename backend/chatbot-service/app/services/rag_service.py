import logging
from typing import List, Dict, Any, Optional

from app.config import settings
from app.schemas.chat import ChatAskResponse, SourceItem
from app.services.gemini_service import gemini_service
from app.services.qdrant_service import qdrant_service

logger = logging.getLogger("chatbot-rag")

NOT_FOUND_MESSAGES = {
    "vi": "Xin lỗi, tôi không tìm thấy thông tin liên quan trong cẩm nang hướng dẫn của Chùa Linh Ứng. Quý khách có thể hỏi về các điểm nổi bật như Tượng Phật Bà Quan Âm 67m, Chánh Điện, Cổng Tam Quan, Vườn Lâm Tỳ Ni...",
    "en": "I am sorry, I could not find relevant information in the Linh Ung Pagoda visitor guide. You may ask about attractions such as the 67m Lady Buddha Statue, Main Sanctuary, Three-Entrance Gate, or Lumbini Garden.",
    "zh": "对不起，在灵应寺的导游指南中未找到相关信息。您可以询问关于67米观音大佛像、大雄宝殿或三关门等景点的信息。",
    "ja": "申し訳ありません。リンウン寺の案内ガイドに関連情報が見つかりませんでした。高さ67メートルの観音像や本堂、三門についてお尋ねください。",
    "ko": "죄송합니다. 린응사 안내 가이드에서 관련 정보를 찾을 수 없습니다. 67m 해수관음상, 대웅전, 일주문 등에 대해 문의해 보세요.",
    "fr": "Désolé, je n'ai pas trouvé d'informations pertinentes dans le guide de la pagode Linh Ung. Vous pouvez poser des questions sur la statue de Lady Buddha de 67m, le sanctuaire principal ou la porte à trois entrées.",
    "ru": "Извините, я не нашел соответствующей информации в путеводителе по пагоде Линь Ынг. Вы можете спросить о статуе Леди Будды (67 м), Главном святилище или Трехарочных воротах."
}

def get_not_found_message(lang: str) -> str:
    return NOT_FOUND_MESSAGES.get(lang, NOT_FOUND_MESSAGES["en"])

async def generate_rag_answer(
    question: str,
    lang: str = "vi",
    session_id: str = ""
) -> ChatAskResponse:
    """
    Quy trình RAG (Retrieval-Augmented Generation):
    1. Vector hóa câu hỏi qua Gemini text-embedding-004 (768 chiều)
    2. Tìm kiếm top-5 đoạn thông tin liên quan trong Qdrant (score >= 0.35)
    3. Nếu không có thông tin thỏa mãn -> Trả câu từ chối lịch sự theo ngôn ngữ
    4. Nếu có thông tin -> Ghép Context + System Prompt -> Gọi Gemini LLM sinh câu trả lời
    5. Đính kèm danh sách nguồn tham khảo (sources)
    """
    logger.info(f"Bắt đầu RAG cho câu hỏi: '{question}' (ngôn ngữ: {lang})")

    # 1. Tạo vector embedding của câu hỏi
    query_vector = await gemini_service.get_embedding(question)

    # 2. Tìm kiếm trong Qdrant Vector DB
    # Ưu tiên tìm theo đúng mã ngôn ngữ; nếu không có kết quả tìm tiếp ở các ngôn ngữ khác (ví dụ: tiếng Việt gốc)
    hits = qdrant_service.search_vectors(
        query_vector=query_vector,
        top_k=settings.TOP_K_VECTORS,
        score_threshold=settings.SIMILARITY_SCORE_THRESHOLD,
        language_code=lang
    )

    if not hits and lang != "vi":
        # Fallback tìm theo tài liệu tiếng Việt nếu bản dịch chưa có vector
        hits = qdrant_service.search_vectors(
            query_vector=query_vector,
            top_k=settings.TOP_K_VECTORS,
            score_threshold=settings.SIMILARITY_SCORE_THRESHOLD
        )

    # 3. Xử lý trường hợp không tìm thấy thông tin liên quan
    if not hits:
        logger.info(f"Không tìm thấy đoạn kiến thức phù hợp trong Qdrant (score < {settings.SIMILARITY_SCORE_THRESHOLD})")
        return ChatAskResponse(
            answer=get_not_found_message(lang),
            sources=[],
            cached=False,
            lang=lang
        )

    # 4. Trích xuất danh sách nguồn tham khảo duy nhất (Sources)
    seen_pois = set()
    sources: List[SourceItem] = []
    context_chunks: List[str] = []

    for h in hits:
        poi_id = h.get("poi_id")
        title = h.get("title") or f"Điểm tham quan #{poi_id}"
        score = h.get("score", 0.0)
        chunk_text = h.get("chunk_text", "").strip()

        if chunk_text:
            context_chunks.append(f"- Điểm tham quan: {title}\n  Nội dung: {chunk_text}")

        if poi_id and poi_id not in seen_pois:
            seen_pois.add(poi_id)
            sources.append(
                SourceItem(
                    poi_id=poi_id,
                    title=title,
                    score=score
                )
            )

    # 5. Xây dựng Prompt cho Gemini LLM
    context_str = "\n\n".join(context_chunks)
    system_instruction = (
        f"Bạn là hướng dẫn viên ảo AI chính thức của Chùa Linh Ứng (Bãi Bụt, Bán đảo Sơn Trà, TP Đà Nẵng). "
        f"Nhiệm vụ của bạn là giải đáp thắc mắc của du khách một cách lịch sự, trang trọng, chuẩn xác dựa trên các thông tin được cung cấp trong [NGỮ CẢNH]. "
        f"Yêu cầu bắt buộc: Trả lời hoàn toàn bằng ngôn ngữ có mã ISO '{lang}'. "
        f"Không tự ý bịa đặt thông tin nếu không có trong ngữ cảnh. "
        f"Nếu thông tin ngữ cảnh đủ để trả lời, hãy diễn giải ngắn gọn, súc tích, văn phong nhã nhặn, tôn nghiêm của chốn thiền môn."
    )

    prompt = (
        f"[NGỮ CẢNH KIẾN THỨC CHÙA LINH ỨNG]:\n{context_str}\n\n"
        f"[CÂU HỎI CỦA DU KHÁCH]:\n{question}\n\n"
        f"[CÂU TRẢ LỜI CỦA BẠN (bằng ngôn ngữ '{lang}')]:"
    )

    # 6. Gọi Gemini LLM sinh câu trả lời
    llm_answer = await gemini_service.generate_response(
        prompt=prompt,
        system_instruction=system_instruction
    )

    if not llm_answer:
        # Fallback tổng hợp câu trả lời tự nhiên nếu offline
        summary_points = "\n".join([f"• {c.replace('- ', '')}" for c in context_chunks[:2]])
        llm_answer = (
            f"Dựa trên cẩm nang thông tin Chùa Linh Ứng Bãi Bụt:\n\n{summary_points}\n\n"
            f"Chúc quý khách có chuyến chiêm bái và tham quan Chùa Linh Ứng an lạc, thanh tịnh!"
        )

    logger.info(f"Hoàn thành câu trả lời RAG với {len(sources)} nguồn tham khảo")
    return ChatAskResponse(
        answer=llm_answer,
        sources=sources,
        cached=False,
        lang=lang
    )

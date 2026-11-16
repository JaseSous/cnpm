import re
import logging
from typing import List, Dict, Any, Optional

from app.config import settings
from app.schemas.chat import ChatAskResponse, SourceItem
from app.services.gemini_service import gemini_service
from app.services.qdrant_service import qdrant_service

logger = logging.getLogger("chatbot-rag")

GREETING_PATTERNS = [
    r"^(xin\s+)?ch[aà]o(\s+b[aạ]n|\s+em|\s+ad|\s+ch[uù]a|\s+qu[yý]\s+kh[aá]ch)?$",
    r"^(h[eê]llo|hi|hey|alo|al[oô])$",
    r"^(nam\s+m[oô]\s+)?a\s+di\s+[đd][aà]\s+ph[aậ]t$",
    r"^m[oô]\s+ph[aậ]t$",
    r"^(good\s+)?(morning|afternoon|evening)$",
    r"^(b[aạ]n\s+l[aà]\s+ai|who\s+are\s+you|b[aạ]n\s+t[eê]n\s+g[iì]|what\s+is\s+your\s+name)$"
]

THANKS_PATTERNS = [
    r"^(c[aả]m\s+[oơ]n(\s+b[aạ]n|\s+nhi[eề]u|\s+nha)?|thank(\s+you|\s+u)?|thanks)$"
]

FAREWELL_PATTERNS = [
    r"^(t[aạ]m\s+bi[eệ]t|bye(\s+bye)?|goodbye)$"
]

CONVERSATIONAL_RESPONSES = {
    "greeting": {
        "vi": (
            "Nam Mô A Di Đà Phật! Xin kính chào quý khách đến với Chùa Linh Ứng Bãi Bụt (Bán đảo Sơn Trà, TP. Đà Nẵng). "
            "Tôi là trợ lý hướng dẫn viên ảo của chùa.\n\n"
            "Quý khách có thể hỏi tôi về:\n"
            "• Các điểm tham quan nổi bật: Tượng Phật Bà Quan Âm 67m, Chánh Điện, Cổng Tam Quan, Vườn Thập Bát La Hán, Bảo Tháp Xá Lợi, Vườn Lâm Tỳ Ni...\n"
            "• Cẩm nang & Tiện ích: Giờ mở cửa, giá vé (hoàn toàn miễn phí), quy định trang phục, bãi gửi xe, ẩm thực chay...\n"
            "• Lịch sử hình thành và sự tích tên gọi 'Bãi Bụt'.\n\n"
            "Tôi có thể hỗ trợ thông tin gì cho chuyến chiêm bái của quý khách hôm nay ạ?"
        ),
        "en": (
            "Namo Amitabha Buddha! Welcome to Linh Ung Pagoda Bai But on Son Tra Peninsula, Da Nang City. "
            "I am your virtual temple tour guide.\n\n"
            "You can ask me about:\n"
            "• Highlight attractions: The 67m Lady Buddha Statue, Main Sanctuary, Three-Entrance Gate, 18 Arhats Garden, Relic Stupa, Lumbini Garden...\n"
            "• Practical guide: Opening hours (6:00 AM - 9:00 PM), free admission, dress code, directions, parking, and vegetarian meals...\n"
            "• History and the sacred legend of 'Bai But'.\n\n"
            "How may I assist you with your pilgrimage today?"
        ),
        "zh": (
            "南无阿弥陀佛！欢迎光临岘港山茶半岛灵应寺。我是您的寺庙虚拟导游助手。\n\n"
            "您可以向我询问：\n"
            "• 著名景点：67米观音大佛像、大雄宝殿、三关门、十八罗汉园、舍利塔等...\n"
            "• 实用指南：开放时间（早上6点至晚上9点）、免费门票、着装要求、素食体验...\n"
            "• 寺庙历史与'佛滩'（Bai But）传奇故事。\n\n"
            "请问有什么我可以为您效劳的吗？"
        ),
        "ja": (
            "南無阿弥陀仏！ダナン・ソンチャ半島のリンウン寺へようこそ。私はバーチャル案内ガイドです。\n\n"
            "以下の情報についてお気軽にお尋ねください：\n"
            "• 主な見どころ：高さ67mの観音像、本堂、三門、十八羅漢像、仏舎利塔など\n"
            "• 参拝案内：開門時間（6:00〜21:00）、入場無料、服装マナー、アクセス、精進料理など\n"
            "• リンウン寺の歴史や「バイ・ブット」の伝説\n\n"
            "どのようなご案内が必要でしょうか？"
        ),
        "ko": (
            "나무아미타불! 다낭 손트라 반도 린응사에 오신 것을 환영합니다. 저는 사찰 가상 가이드입니다.\n\n"
            "다음 내용에 대해 언제든지 질문해 주세요:\n"
            "• 주요 명소: 67m 해수관음상, 대웅전, 일주문, 십팔나한상, 사리탑 등\n"
            "• 이용 안내: 운영 시간(오전 6시~오후 9시), 무료 입장, 복장 규정, 주차 및 사찰 음식\n"
            "• 린응사의 역사 및 '바이붓' 전설\n\n"
            "무엇을 도와드릴까요?"
        ),
        "fr": (
            "Namo Amitabha Bouddha ! Bienvenue à la pagode Linh Ung Bai But sur la péninsule de Son Tra, Da Nang. "
            "Je suis votre guide virtuel.\n\n"
            "N'hésitez pas à me poser des questions sur les monuments (statue de 67m, sanctuaire principal...), "
            "les horaires (6h-21h), l'entrée gratuite ou les consignes de visite. Comment puis-je vous aider ?"
        )
    },
    "thanks": {
        "vi": "Dạ không có chi ạ! Kính chúc quý khách và gia quyến một chuyến chiêm bái Chùa Linh Ứng tràn đầy bình an, thanh tịnh và vạn sự cát tường!",
        "en": "You are most welcome! Wishing you and your loved ones a peaceful and blessed pilgrimage to Linh Ung Pagoda!"
    },
    "farewell": {
        "vi": "Tạm biệt quý khách! Kính chúc quý khách thượng lộ bình an và hẹn gặp lại tại Chùa Linh Ứng Bãi Bụt!",
        "en": "Goodbye and safe travels! Wishing you joy and peace, and we hope to welcome you again to Linh Ung Pagoda!"
    }
}

NOT_FOUND_MESSAGES = {
    "vi": "Xin lỗi, tôi không tìm thấy thông tin liên quan trong cẩm nang hướng dẫn của Chùa Linh Ứng. Quý khách có thể hỏi về các điểm nổi bật như Tượng Phật Bà Quan Âm 67m, Chánh Điện, Cổng Tam Quan, Vườn Lâm Tỳ Ni, giờ mở cửa hay quy định trang phục...",
    "en": "I am sorry, I could not find relevant information in the Linh Ung Pagoda visitor guide. You may ask about attractions such as the 67m Lady Buddha Statue, Main Sanctuary, Three-Entrance Gate, Lumbini Garden, opening hours, or dress code.",
    "zh": "对不起，在灵应寺的导游指南中未找到相关信息。您可以询问关于67米观音大佛像、大雄宝殿、三关门、开放时间或参观注意事项等信息。",
    "ja": "申し訳ありません。リンウン寺の案内ガイドに関連情報が見つかりませんでした。高さ67メートルの観音像や本堂、三門、開門時間についてお尋ねください。",
    "ko": "죄송합니다. 린응사 안내 가이드에서 관련 정보를 찾을 수 없습니다. 67m 해수관음상, 대웅전, 일주문, 개방 시간 등에 대해 문의해 보세요.",
    "fr": "Désolé, je n'ai pas trouvé d'informations pertinentes dans le guide de la pagode Linh Ung. Vous pouvez poser des questions sur la statue de Lady Buddha de 67m, le sanctuaire principal, les horaires ou les consignes.",
    "ru": "Извините, я не нашел соответствующей информации в путеводителе по пагоде Линь Ынг. Вы можете спросить о статуе Леди Будды (67 м), Главном святилище, часах работы hoặc quy định tham quan."
}

def get_not_found_message(lang: str) -> str:
    return NOT_FOUND_MESSAGES.get(lang, NOT_FOUND_MESSAGES["en"])

async def generate_rag_answer(
    question: str,
    lang: str = "vi",
    session_id: str = ""
) -> ChatAskResponse:
    """
    Quy trình RAG (Retrieval-Augmented Generation) thông minh:
    1. Kiểm tra nhận diện câu chào hỏi / xã giao (Greetings, Thanks, Farewell) -> Phản hồi trực tiếp trang nhã
    2. Vector hóa câu hỏi qua Gemini text-embedding-004 (768 chiều)
    3. Tìm kiếm top đoạn thông tin liên quan trong Qdrant (score >= SIMILARITY_SCORE_THRESHOLD)
    4. Nếu không có thông tin thỏa mãn -> Trả câu từ chối lịch sự theo ngôn ngữ
    5. Nếu có thông tin -> Ghép Context + System Prompt -> Gọi Gemini LLM sinh câu trả lời
    6. Đính kèm danh sách nguồn tham khảo (sources)
    """
    logger.info(f"Bắt đầu RAG cho câu hỏi: '{question}' (ngôn ngữ: {lang})")

    # 1. Kiểm tra câu chào hỏi xã giao / cảm ơn / tạm biệt
    q_norm = re.sub(r"[^\w\s]", "", question.lower()).strip()
    
    if any(re.match(p, q_norm) for p in GREETING_PATTERNS):
        ans = CONVERSATIONAL_RESPONSES["greeting"].get(lang, CONVERSATIONAL_RESPONSES["greeting"]["vi"])
        return ChatAskResponse(answer=ans, sources=[], cached=False, lang=lang)
        
    if any(re.match(p, q_norm) for p in THANKS_PATTERNS):
        ans = CONVERSATIONAL_RESPONSES["thanks"].get(lang, CONVERSATIONAL_RESPONSES["thanks"]["vi"])
        return ChatAskResponse(answer=ans, sources=[], cached=False, lang=lang)
        
    if any(re.match(p, q_norm) for p in FAREWELL_PATTERNS):
        ans = CONVERSATIONAL_RESPONSES["farewell"].get(lang, CONVERSATIONAL_RESPONSES["farewell"]["vi"])
        return ChatAskResponse(answer=ans, sources=[], cached=False, lang=lang)

    # 2. Tạo vector embedding của câu hỏi
    query_vector = await gemini_service.get_embedding(question)

    # 3. Tìm kiếm trong Qdrant Vector DB
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

    # 4. Xử lý trường hợp không tìm thấy thông tin liên quan
    if not hits:
        logger.info(f"Không tìm thấy đoạn kiến thức phù hợp trong Qdrant (score < {settings.SIMILARITY_SCORE_THRESHOLD})")
        return ChatAskResponse(
            answer=get_not_found_message(lang),
            sources=[],
            cached=False,
            lang=lang
        )

    # 5. Trích xuất danh sách nguồn tham khảo duy nhất (Sources)
    seen_pois = set()
    sources: List[SourceItem] = []
    context_chunks: List[str] = []

    for h in hits:
        poi_id = h.get("poi_id")
        title = h.get("title") or (f"Điểm tham quan #{poi_id}" if poi_id else "Cẩm nang Chùa Linh Ứng")
        score = h.get("score", 0.0)
        chunk_text = h.get("chunk_text", "").strip()

        if chunk_text:
            context_chunks.append(f"- Chủ đề: {title}\n  Nội dung: {chunk_text}")

        # poi_id có thể là 0 (Cẩm nang chung) hoặc > 0 (Điểm tham quan)
        poi_key = poi_id if poi_id is not None else 0
        if poi_key not in seen_pois:
            seen_pois.add(poi_key)
            sources.append(
                SourceItem(
                    poi_id=poi_key,
                    title=title,
                    score=score
                )
            )

    # 6. Xây dựng Prompt cho Gemini LLM
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

    # 7. Gọi Gemini LLM sinh câu trả lời
    llm_answer = await gemini_service.generate_response(
        prompt=prompt,
        system_instruction=system_instruction
    )

    if not llm_answer:
        # Fallback tổng hợp câu trả lời tự nhiên nếu offline hoặc quota exceeded
        summary_points = "\n\n".join([f"• {c.replace('- ', '')}" for c in context_chunks[:2]])
        llm_answer = (
            f"Dựa trên cẩm nang thông tin Chùa Linh Ứng Bãi Bụt:\n\n{summary_points}\n\n"
            f"Kính chúc quý khách có chuyến chiêm bái và tham quan Chùa Linh Ứng an lạc, thanh tịnh!"
        )

    logger.info(f"Hoàn thành câu trả lời RAG với {len(sources)} nguồn tham khảo")
    return ChatAskResponse(
        answer=llm_answer,
        sources=sources,
        cached=False,
        lang=lang
    )

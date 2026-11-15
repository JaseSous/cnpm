import logging
import asyncio
import json
import re
from typing import Optional, Dict
from deep_translator import GoogleTranslator, MyMemoryTranslator
from app.config import settings

logger = logging.getLogger("pipeline-translator")

# Ánh xạ mã ngôn ngữ ISO sang định dạng của deep-translator
LANGUAGE_CODE_MAP = {
    "vi": "vi",
    "en": "en",
    "zh": "zh-CN",
    "ja": "ja",
    "ko": "ko",
    "fr": "fr",
    "de": "de",
    "es": "es",
    "th": "th",
    "ru": "ru",
    "pt": "pt",
    "it": "it",
    "id": "id",
    "ar": "ar",
    "hi": "hi"
}

MYMEMORY_CODE_MAP = {
    "vi": "vi-VN",
    "en": "en-US",
    "zh": "zh-CN",
    "ja": "ja-JP",
    "ko": "ko-KR",
    "fr": "fr-FR",
    "de": "de-DE",
    "es": "es-ES",
    "th": "th-TH",
    "ru": "ru-RU",
    "pt": "pt-PT",
    "it": "it-IT",
    "id": "id-ID",
    "ar": "ar-SA",
    "hi": "hi-IN"
}

# Khởi tạo Gemini Client nếu có API key hợp lệ
_gemini_client = None
if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ("your-gemini-api-key", "dummy", ""):
    try:
        from google import genai
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Đã khởi tạo Gemini Client cho dịch thuật (Model: {getattr(settings, 'GEMINI_MODEL', 'gemini-3.5-flash')})")
    except Exception as e:
        logger.warning(f"Không thể khởi tạo Gemini Client cho dịch thuật: {e}")


async def translate_with_gemini(
    title: str,
    description: str,
    target_lang: str,
    source_lang: str = "vi"
) -> Optional[Dict[str, str]]:
    """Dịch tiêu đề và mô tả bằng Gemini AI chuẩn bối cảnh văn hóa Phật giáo"""
    if not _gemini_client:
        return None

    try:
        model = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash")
        prompt = (
            f"You are a professional multilingual translator for Buddhist pagoda tourism in Vietnam.\n"
            f"Translate the following pagoda attraction title and description from '{source_lang}' to target language '{target_lang}'.\n"
            f"Maintain respectful, solemn Buddhist heritage terminology (e.g. Avalokiteshvara, Bodhisattva, Pagoda).\n"
            f"Return ONLY a valid JSON object with keys 'title' and 'description' without markdown formatting or code blocks:\n"
            f"{{\"title\": \"...\", \"description\": \"...\"}}\n\n"
            f"Title: {title}\n"
            f"Description: {description}"
        )
        response = await asyncio.wait_for(
            _gemini_client.aio.models.generate_content(
                model=model,
                contents=prompt
            ),
            timeout=15.0
        )
        if response and response.text:
            raw_text = response.text.strip()
            # Xóa markdown code fence nếu có
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text).strip()

            data = json.loads(raw_text)
            t_title = str(data.get("title", "")).strip()
            t_desc = str(data.get("description", "")).strip()
            if t_title and t_desc:
                logger.info(f"Gemini AI dịch thành công sang '{target_lang}': '{t_title[:30]}...'")
                return {"title": t_title, "description": t_desc}
    except Exception as e:
        logger.warning(f"Gemini AI dịch thất bại sang '{target_lang}': {e}. Sẽ thử fallback.")

    return None


async def translate_text(
    text: str,
    target_lang: str,
    source_lang: str = "auto"
) -> str:
    """
    Tự động dịch văn bản sang ngôn ngữ đích với cơ chế dự phòng đa tầng:
    1. GoogleTranslator (deep-translator)
    2. MyMemoryTranslator (deep-translator)
    3. Fallback có định danh ngôn ngữ nếu mạng mất kết nối
    """
    if not text or not text.strip():
        return ""

    target_code = LANGUAGE_CODE_MAP.get(target_lang, target_lang)

    # 1. Thử Google Translator với timeout 5s
    try:
        loop = asyncio.get_event_loop()
        translated = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: GoogleTranslator(source=source_lang, target=target_code).translate(text)
            ),
            timeout=5.0
        )
        if translated:
            return translated
    except Exception as e:
        logger.warning(f"GoogleTranslator gặp sự cố hoặc timeout ({e}). Chuyển sang MyMemoryTranslator...")

    # 2. Thử MyMemory Translator với timeout 5s
    try:
        source_mm = MYMEMORY_CODE_MAP.get(source_lang, "vi-VN") if source_lang != "auto" else "vi-VN"
        target_mm = MYMEMORY_CODE_MAP.get(target_lang, f"{target_lang}-{target_lang.upper()}")
        loop = asyncio.get_event_loop()
        translated = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: MyMemoryTranslator(source=source_mm, target=target_mm).translate(text[:450])
            ),
            timeout=5.0
        )
        if translated:
            return translated
    except Exception as e:
        logger.warning(f"MyMemoryTranslator gặp sự cố hoặc timeout ({e}). Sử dụng Fallback giả lập...")

    # 3. Fallback an toàn (không để dừng luồng pipeline)
    return f"[{target_lang.upper()}] {text}"


async def translate_poi_content(
    title: str,
    description: str,
    target_lang: str,
    source_lang: str = "vi"
) -> Dict[str, str]:
    """
    Dịch cả title và description sang ngôn ngữ đích:
    1. Trả ngay nếu target_lang == source_lang
    2. Thử Gemini AI (chất lượng cao nhất, chuẩn bối cảnh Phật giáo)
    3. Fallback sang deep-translator (GoogleTranslator -> MyMemoryTranslator)
    """
    if target_lang == source_lang:
        return {
            "title": title,
            "description": description
        }

    # 1. Thử dịch bằng Gemini AI
    gemini_result = await translate_with_gemini(
        title=title,
        description=description,
        target_lang=target_lang,
        source_lang=source_lang
    )
    if gemini_result:
        return gemini_result

    # 2. Fallback sang GoogleTranslator / MyMemoryTranslator
    translated_title = await translate_text(title, target_lang=target_lang, source_lang=source_lang)
    translated_desc = await translate_text(description, target_lang=target_lang, source_lang=source_lang)

    return {
        "title": translated_title or title,
        "description": translated_desc or description
    }

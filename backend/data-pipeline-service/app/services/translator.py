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
CANDIDATE_GEMINI_MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]

if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY not in ("your-gemini-api-key", "dummy", ""):
    try:
        from google import genai
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Đã khởi tạo Gemini Client cho dịch thuật (Ưu tiên: {CANDIDATE_GEMINI_MODELS[0]})")
    except Exception as e:
        logger.warning(f"Không thể khởi tạo Gemini Client cho dịch thuật: {e}")


async def batch_translate_with_gemini(
    title: str,
    description: str,
    target_languages: list,
    source_lang: str = "vi"
) -> Dict[str, Dict[str, str]]:
    """
    Dịch hàng loạt (Batch Translation) sang nhiều ngôn ngữ cùng lúc trong 1 request Gemini duy nhất.
    Giúp tiết kiệm 15 lần quota và tránh chạm giới hạn Rate Limit.
    """
    if not _gemini_client or not target_languages:
        return {}

    prompt = (
        f"You are a professional multilingual translator for Buddhist pagoda tourism in Vietnam.\n"
        f"Translate the following pagoda attraction title and description from '{source_lang}' to ALL these target languages: {target_languages}.\n"
        f"Maintain respectful, solemn Buddhist heritage terminology (e.g. Avalokiteshvara, Bodhisattva, Pagoda).\n"
        f"Return ONLY a valid JSON object where keys are the target language codes and values are objects with 'title' and 'description':\n"
        f"{{\n"
        f"  \"ja\": {{\"title\": \"...\", \"description\": \"...\"}},\n"
        f"  \"en\": {{\"title\": \"...\", \"description\": \"...\"}}\n"
        f"}}\n\n"
        f"Title: {title}\n"
        f"Description: {description}"
    )

    for model in CANDIDATE_GEMINI_MODELS:
        try:
            from google.genai import types
            config = types.GenerateContentConfig(response_mime_type="application/json")
            response = await asyncio.wait_for(
                _gemini_client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                ),
                timeout=25.0
            )
            if response and response.text:
                raw_text = response.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
                    raw_text = re.sub(r"\n?```$", "", raw_text).strip()

                data = json.loads(raw_text)
                if isinstance(data, dict) and len(data) > 0:
                    logger.info(f"Gemini AI ({model}) dịch Batch thành công {len(data)}/{len(target_languages)} ngôn ngữ!")
                    return data
        except Exception as e:
            logger.warning(f"Gemini AI ({model}) dịch Batch thất bại: {e}. Đang thử model tiếp theo...")

    return {}


async def translate_with_gemini(
    title: str,
    description: str,
    target_lang: str,
    source_lang: str = "vi"
) -> Optional[Dict[str, str]]:
    """Dịch tiêu đề và mô tả bằng Gemini AI chuẩn bối cảnh văn hóa Phật giáo (có cơ chế xoay vòng model)"""
    if not _gemini_client:
        return None

    prompt = (
        f"You are a professional multilingual translator for Buddhist pagoda tourism in Vietnam.\n"
        f"Translate the following pagoda attraction title and description from '{source_lang}' to target language '{target_lang}'.\n"
        f"Maintain respectful, solemn Buddhist heritage terminology (e.g. Avalokiteshvara, Bodhisattva, Pagoda).\n"
        f"Return ONLY a valid JSON object with keys 'title' and 'description':\n"
        f"{{\"title\": \"...\", \"description\": \"...\"}}\n\n"
        f"Title: {title}\n"
        f"Description: {description}"
    )

    for model in CANDIDATE_GEMINI_MODELS:
        try:
            from google.genai import types
            config = types.GenerateContentConfig(response_mime_type="application/json")
            response = await asyncio.wait_for(
                _gemini_client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                ),
                timeout=15.0
            )
            if response and response.text:
                raw_text = response.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
                    raw_text = re.sub(r"\n?```$", "", raw_text).strip()

                data = json.loads(raw_text)
                t_title = str(data.get("title", "")).strip()
                t_desc = str(data.get("description", "")).strip()
                if t_title and t_desc:
                    logger.info(f"Gemini AI ({model}) dịch thành công sang '{target_lang}': '{t_title[:30]}...'")
                    return {"title": t_title, "description": t_desc}
        except Exception as e:
            logger.warning(f"Gemini AI ({model}) dịch thất bại sang '{target_lang}': {e}. Đang thử model tiếp theo...")

    return None


async def translate_text(
    text: str,
    target_lang: str,
    source_lang: str = "auto"
) -> str:
    """
    Tự động dịch văn bản sang ngôn ngữ đích với cơ chế dự phòng đa tầng:
    1. GoogleTranslator (deep-translator)
    2. MyMemoryTranslator (kèm email định danh mở khóa 10.000 từ/ngày)
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
        logger.warning(f"GoogleTranslator gặp sự cố ({e}). Chuyển sang MyMemoryTranslator...")

    # 2. Thử MyMemory Translator với email định danh (10.000 từ/ngày)
    try:
        source_mm = MYMEMORY_CODE_MAP.get(source_lang, "vi-VN") if source_lang != "auto" else "vi-VN"
        target_mm = MYMEMORY_CODE_MAP.get(target_lang, f"{target_lang}-{target_lang.upper()}")
        loop = asyncio.get_event_loop()
        translated = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: MyMemoryTranslator(
                    source=source_mm, 
                    target=target_mm, 
                    email="contact@linhungpagoda.vn"
                ).translate(text[:450])
            ),
            timeout=5.0
        )
        if translated and not translated.startswith("MYMEMORY WARNING"):
            return translated
    except Exception as e:
        logger.warning(f"MyMemoryTranslator gặp sự cố ({e}). Sử dụng Fallback...")

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

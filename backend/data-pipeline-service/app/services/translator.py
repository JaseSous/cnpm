import logging
import asyncio
from typing import Optional, Dict
from deep_translator import GoogleTranslator, MyMemoryTranslator

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

    # 1. Thử Google Translator
    try:
        loop = asyncio.get_event_loop()
        translated = await loop.run_in_executor(
            None,
            lambda: GoogleTranslator(source=source_lang, target=target_code).translate(text)
        )
        if translated:
            return translated
    except Exception as e:
        logger.warning(f"GoogleTranslator gặp sự cố ({e}). Chuyển sang MyMemoryTranslator...")

    # 2. Thử MyMemory Translator
    try:
        source_mm = MYMEMORY_CODE_MAP.get(source_lang, "vi-VN") if source_lang != "auto" else "vi-VN"
        target_mm = MYMEMORY_CODE_MAP.get(target_lang, f"{target_lang}-{target_lang.upper()}")
        loop = asyncio.get_event_loop()
        translated = await loop.run_in_executor(
            None,
            lambda: MyMemoryTranslator(source=source_mm, target=target_mm).translate(text[:450])
        )
        if translated:
            return translated
    except Exception as e:
        logger.warning(f"MyMemoryTranslator gặp sự cố ({e}). Sử dụng Fallback giả lập...")

    # 3. Fallback an toàn (không để dừng luồng pipeline)
    return f"[{target_lang.upper()}] {text}"

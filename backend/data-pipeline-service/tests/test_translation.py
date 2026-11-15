import pytest
from unittest.mock import patch
from app.services.translator import translate_text, translate_poi_content

@pytest.mark.asyncio
async def test_translate_text_empty():
    res = await translate_text("", target_lang="en")
    assert res == ""

@pytest.mark.asyncio
async def test_translate_text_google_success():
    with patch("deep_translator.GoogleTranslator.translate", return_value="Linh Ung Pagoda"):
        res = await translate_text("Chùa Linh Ứng", target_lang="en", source_lang="vi")
        assert res == "Linh Ung Pagoda"

@pytest.mark.asyncio
async def test_translate_text_fallback():
    with patch("deep_translator.GoogleTranslator.translate", side_effect=Exception("Network error")):
        with patch("deep_translator.MyMemoryTranslator.translate", side_effect=Exception("Quota exceeded")):
            res = await translate_text("Chùa Linh Ứng", target_lang="en", source_lang="vi")
            assert "[EN]" in res

@pytest.mark.asyncio
async def test_translate_poi_content_same_language():
    res = await translate_poi_content(
        title="Chùa Linh Ứng",
        description="Ngôi chùa nổi tiếng tại Bãi Bụt",
        target_lang="vi",
        source_lang="vi"
    )
    assert res["title"] == "Chùa Linh Ứng"
    assert res["description"] == "Ngôi chùa nổi tiếng tại Bãi Bụt"

@pytest.mark.asyncio
async def test_translate_poi_content_different_language():
    with patch("app.services.translator.translate_text", side_effect=lambda text, target_lang, source_lang: f"{text} in {target_lang}"):
        res = await translate_poi_content(
            title="Tượng Phật Bà",
            description="Tượng Phật Quan Âm cao 67m",
            target_lang="en",
            source_lang="vi"
        )
        assert res["title"] == "Tượng Phật Bà in en"
        assert res["description"] == "Tượng Phật Quan Âm cao 67m in en"

@pytest.mark.asyncio
async def test_translate_poi_content_gemini_success():
    with patch("app.services.translator.translate_with_gemini", return_value={"title": "Lady Buddha", "description": "67m Statue"}):
        res = await translate_poi_content(
            title="Tượng Phật Bà",
            description="Tượng Phật Quan Âm cao 67m",
            target_lang="en",
            source_lang="vi"
        )
        assert res["title"] == "Lady Buddha"
        assert res["description"] == "67m Statue"

import pytest
import math
from app.services.gemini_service import generate_mock_embedding
from app.services.chat_service import normalize_question
from app.services.rag_service import generate_rag_answer
from app.services.qdrant_service import qdrant_service

def test_mock_embedding_properties():
    emb = generate_mock_embedding("Chùa Linh Ứng", dim=768)
    assert len(emb) == 768
    norm = math.sqrt(sum(x * x for x in emb))
    assert abs(norm - 1.0) < 0.01

def test_normalize_question():
    q, q_hash = normalize_question("   Chùa   Linh Ứng    ở   Đâu?   ")
    assert q == "chùa linh ứng ở đâu?"
    assert len(q_hash) == 64

@pytest.mark.asyncio
async def test_rag_not_found():
    # Khi Qdrant không có vector nào phù hợp
    res = await generate_rag_answer(
        question="Hà Nội có bao nhiêu quận?",
        lang="vi"
    )
    assert "không tìm thấy thông tin liên quan" in res.answer
    assert len(res.sources) == 0

@pytest.mark.asyncio
async def test_rag_success_with_sources():
    # Nạp 1 vector vào Qdrant
    text = "Vườn Lâm Tỳ Ni là nơi đức Phật đản sinh, có nhiều pho tượng đắp nổi tinh xảo."
    emb = generate_mock_embedding(text)
    qdrant_service.upsert_poi_vectors(
        poi_id=7,
        revision=1,
        language_code="vi",
        chunks=[{
            "chunk_id": "c7",
            "chunk_text": text,
            "embedding": emb,
            "metadata": {"title": "Vườn Lâm Tỳ Ni"}
        }]
    )

    # Hỏi câu khớp với text
    res = await generate_rag_answer(
        question=text,
        lang="vi"
    )
    assert len(res.sources) >= 1
    assert any(s.title == "Vườn Lâm Tỳ Ni" for s in res.sources)
    assert "Vườn Lâm Tỳ Ni" in res.answer

@pytest.mark.asyncio
async def test_rag_greeting():
    res = await generate_rag_answer(question="Xin chào", lang="vi")
    assert "Nam Mô A Di Đà Phật" in res.answer
    assert len(res.sources) == 0

@pytest.mark.asyncio
async def test_rag_thanks():
    res = await generate_rag_answer(question="Cảm ơn bạn", lang="vi")
    assert "không có chi" in res.answer.lower()
    assert len(res.sources) == 0

@pytest.mark.asyncio
async def test_rag_farewell():
    res = await generate_rag_answer(question="Tạm biệt", lang="vi")
    assert "tạm biệt" in res.answer.lower()
    assert len(res.sources) == 0

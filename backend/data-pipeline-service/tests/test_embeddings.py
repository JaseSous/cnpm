import pytest
import math
from app.services.embedding_service import (
    chunk_text,
    generate_mock_embedding,
    EmbeddingService
)

def test_chunk_text_short():
    chunks = chunk_text("Ngắn gọn", max_chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0] == "Ngắn gọn"

def test_chunk_text_empty():
    chunks = chunk_text("")
    assert chunks == []

def test_chunk_text_long():
    text = "Câu một.\n\n" * 50
    chunks = chunk_text(text, max_chunk_size=100, overlap=10)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 150

def test_generate_mock_embedding():
    emb = generate_mock_embedding("Chùa Linh Ứng", dim=768)
    assert len(emb) == 768
    # Kiểm tra L2 norm gần bằng 1.0
    norm = math.sqrt(sum(x * x for x in emb))
    assert abs(norm - 1.0) < 0.01

@pytest.mark.asyncio
async def test_embedding_service_generate_chunks():
    service = EmbeddingService()
    chunks = await service.generate_poi_chunks(
        poi_id=1,
        revision=1,
        language_code="vi",
        title="Tượng Phật Bà",
        description="Bức tượng Quan Thế Âm Bồ Tát cao nhất Việt Nam."
    )
    assert len(chunks) >= 1
    first = chunks[0]
    assert first["chunk_id"].startswith("poi_1_vi_rev1_")
    assert len(first["embedding"]) == 768
    assert first["metadata"]["poi_id"] == "1"
    assert first["metadata"]["language_code"] == "vi"

@pytest.mark.asyncio
async def test_embedding_service_sync(mock_poi_grpc, mock_chatbot_grpc):
    service = EmbeddingService()
    success = await service.sync_poi_embeddings(
        poi_id=1,
        revision=1,
        language_code="vi",
        title="Chánh Điện",
        description="Khu vực trung tâm chùa."
    )
    assert success is True
    mock_chatbot_grpc.upsert_vectors.assert_called_once()
    mock_poi_grpc.update_vector_status.assert_called_with(
        poi_id=1,
        status="Synced",
        error_message=""
    )

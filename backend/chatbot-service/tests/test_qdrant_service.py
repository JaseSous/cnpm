import pytest
from app.services.qdrant_service import qdrant_service
from app.services.gemini_service import generate_mock_embedding

def test_qdrant_collection_exists():
    qdrant_service.ensure_collection_exists()
    assert qdrant_service.client.collection_exists(qdrant_service.collection_name) is True

def test_upsert_and_search_vectors():
    poi_id = 1
    revision = 1
    lang = "vi"
    text = "Tượng Phật Bà Quan Âm cao 67 mét tại Chùa Linh Ứng Bãi Bụt."
    embedding = generate_mock_embedding(text)

    chunks = [
        {
            "chunk_id": "chunk_01",
            "chunk_text": text,
            "embedding": embedding,
            "metadata": {"title": "Tượng Phật Bà Quan Âm"}
        }
    ]

    count = qdrant_service.upsert_poi_vectors(
        poi_id=poi_id,
        revision=revision,
        language_code=lang,
        chunks=chunks
    )
    assert count == 1

    # Tìm kiếm với cùng vector (score sẽ gần 1.0)
    hits = qdrant_service.search_vectors(
        query_vector=embedding,
        top_k=3,
        score_threshold=0.35,
        language_code=lang
    )
    assert len(hits) >= 1
    assert hits[0]["poi_id"] == 1
    assert "Tượng Phật Bà" in hits[0]["chunk_text"]
    assert hits[0]["score"] >= 0.90

def test_delete_poi_vectors():
    poi_id = 2
    chunks = [
        {
            "chunk_id": "chunk_02",
            "chunk_text": "Chánh Điện Chùa Linh Ứng",
            "embedding": generate_mock_embedding("Chánh Điện"),
            "metadata": {"title": "Chánh Điện"}
        }
    ]
    qdrant_service.upsert_poi_vectors(poi_id=poi_id, revision=1, language_code="vi", chunks=chunks)
    
    deleted = qdrant_service.delete_poi_vectors(poi_id=poi_id)
    assert deleted == 1

    # Tìm kiếm lại không thấy
    hits = qdrant_service.search_vectors(
        query_vector=generate_mock_embedding("Chánh Điện"),
        top_k=3,
        score_threshold=0.8
    )
    matching = [h for h in hits if h["poi_id"] == poi_id]
    assert len(matching) == 0

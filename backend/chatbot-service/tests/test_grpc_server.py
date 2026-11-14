import pytest
from app.grpc_server.chatbot_grpc_server import ChatbotInternalServiceImpl
import chatbot_service_pb2
from app.services.gemini_service import generate_mock_embedding

@pytest.mark.asyncio
async def test_grpc_upsert_vectors():
    servicer = ChatbotInternalServiceImpl()
    
    vec = generate_mock_embedding("Chùa Linh Ứng")
    chunk = chatbot_service_pb2.VectorChunk(
        chunk_id="chunk_test_grpc",
        chunk_text="Nội dung thuyết minh điểm tham quan",
        embedding=vec,
        metadata={"title": "Điểm tham quan test"}
    )
    req = chatbot_service_pb2.UpsertVectorsRequest(
        poi_id=15,
        revision=1,
        language_code="vi",
        chunks=[chunk]
    )

    res = await servicer.UpsertVectors(req, context=None)
    assert res.success is True
    assert res.upserted_count == 1

@pytest.mark.asyncio
async def test_grpc_delete_vectors():
    servicer = ChatbotInternalServiceImpl()
    req = chatbot_service_pb2.DeleteVectorsRequest(poi_id=15)
    res = await servicer.DeleteVectors(req, context=None)
    assert res.success is True
    assert res.deleted_count >= 1

@pytest.mark.asyncio
async def test_grpc_invalidate_faq_cache():
    servicer = ChatbotInternalServiceImpl()
    req = chatbot_service_pb2.InvalidateCacheRequest(poi_id=15, pattern="faq:*")
    res = await servicer.InvalidateFaqCache(req, context=None)
    assert res.success is True

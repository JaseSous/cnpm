import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import grpc

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import chatbot_service_pb2
import chatbot_service_pb2_grpc
from app.config import settings

logger = logging.getLogger("chatbot-grpc-client")

class ChatbotServiceClient:
    def __init__(self, target: Optional[str] = None):
        self.target = target or settings.CHATBOT_GRPC_TARGET

    async def upsert_vectors(
        self,
        poi_id: int,
        revision: int,
        language_code: str,
        chunks: List[Dict[str, Any]]
    ) -> bool:
        """Đồng bộ các vector embeddings của POI vào Chatbot AI Service"""
        try:
            async with grpc.aio.insecure_channel(self.target) as channel:
                stub = chatbot_service_pb2_grpc.ChatbotInternalServiceStub(channel)
                proto_chunks = [
                    chatbot_service_pb2.VectorChunk(
                        chunk_id=c.get("chunk_id", ""),
                        chunk_text=c.get("chunk_text", ""),
                        embedding=c.get("embedding", []),
                        metadata=c.get("metadata", {})
                    )
                    for c in chunks
                ]
                req = chatbot_service_pb2.UpsertVectorsRequest(
                    poi_id=poi_id,
                    revision=revision,
                    language_code=language_code,
                    chunks=proto_chunks
                )
                res = await stub.UpsertVectors(req, timeout=10)
                return res.success
        except Exception as e:
            logger.warning(f"Chưa thể kết nối tới Chatbot Service gRPC ({e}). Bỏ qua bước đồng bộ vector.")
            return False

    async def delete_vectors(self, poi_id: int) -> bool:
        """Xóa toàn bộ vector chunks của POI khỏi Qdrant"""
        try:
            async with grpc.aio.insecure_channel(self.target) as channel:
                stub = chatbot_service_pb2_grpc.ChatbotInternalServiceStub(channel)
                req = chatbot_service_pb2.DeleteVectorsRequest(poi_id=poi_id)
                res = await stub.DeleteVectors(req, timeout=5)
                return res.success
        except Exception as e:
            logger.warning(f"Lỗi khi gọi gRPC DeleteVectors ({e})")
            return False

    async def invalidate_faq_cache(self, poi_id: int = 0, pattern: str = "") -> bool:
        """Xóa FAQ Cache trên Redis khi POI thay đổi hoặc bị xóa"""
        try:
            async with grpc.aio.insecure_channel(self.target) as channel:
                stub = chatbot_service_pb2_grpc.ChatbotInternalServiceStub(channel)
                req = chatbot_service_pb2.InvalidateCacheRequest(poi_id=poi_id, pattern=pattern)
                res = await stub.InvalidateFaqCache(req, timeout=5)
                return res.success
        except Exception as e:
            logger.warning(f"Lỗi khi gọi gRPC InvalidateFaqCache ({e})")
            return False

chatbot_grpc_client = ChatbotServiceClient()

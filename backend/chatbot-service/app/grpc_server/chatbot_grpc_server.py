import sys
import logging
from pathlib import Path
import grpc
from grpc.aio import server as aio_server

# Đảm bảo import được các module pb2 tự sinh
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import chatbot_service_pb2
import chatbot_service_pb2_grpc

from app.services.qdrant_service import qdrant_service
from app.services.redis_service import redis_service
from app.config import settings

logger = logging.getLogger("chatbot-grpc-server")

class ChatbotInternalServiceImpl(chatbot_service_pb2_grpc.ChatbotInternalServiceServicer):
    async def UpsertVectors(self, request, context):
        """Đồng bộ và lưu trữ các vector embeddings của POI vào Qdrant"""
        try:
            chunks = []
            for c in request.chunks:
                chunks.append({
                    "chunk_id": c.chunk_id,
                    "chunk_text": c.chunk_text,
                    "embedding": list(c.embedding),
                    "metadata": dict(c.metadata)
                })

            upserted = qdrant_service.upsert_poi_vectors(
                poi_id=request.poi_id,
                revision=request.revision,
                language_code=request.language_code,
                chunks=chunks
            )

            logger.info(
                f"[gRPC] UpsertVectors thành công cho POI #{request.poi_id} ({request.language_code}): {upserted} chunks"
            )
            return chatbot_service_pb2.UpsertVectorsResponse(
                success=True,
                upserted_count=upserted,
                message="Vector embeddings upserted successfully"
            )
        except Exception as e:
            logger.error(f"[gRPC] Lỗi trong UpsertVectors cho POI #{request.poi_id}: {e}")
            return chatbot_service_pb2.UpsertVectorsResponse(
                success=False,
                upserted_count=0,
                message=str(e)
            )

    async def DeleteVectors(self, request, context):
        """Xóa toàn bộ vector embeddings thuộc về POI khi bị xóa"""
        try:
            deleted = qdrant_service.delete_poi_vectors(poi_id=request.poi_id)
            logger.info(f"[gRPC] DeleteVectors thành công cho POI #{request.poi_id}")
            return chatbot_service_pb2.DeleteVectorsResponse(
                success=True,
                deleted_count=deleted,
                message=f"Deleted vectors for POI #{request.poi_id}"
            )
        except Exception as e:
            logger.error(f"[gRPC] Lỗi trong DeleteVectors cho POI #{request.poi_id}: {e}")
            return chatbot_service_pb2.DeleteVectorsResponse(
                success=False,
                deleted_count=0,
                message=str(e)
            )

    async def InvalidateFaqCache(self, request, context):
        """Xóa bộ nhớ đệm câu trả lời FAQ Cache trên Redis DB 1"""
        try:
            pattern = request.pattern or "faq:*"
            cleared = await redis_service.invalidate_faq_cache(pattern=pattern)
            logger.info(f"[gRPC] InvalidateFaqCache thành công (pattern={pattern}): {cleared} keys")
            return chatbot_service_pb2.InvalidateCacheResponse(
                success=True,
                cleared_keys=cleared,
                message=f"Cleared {cleared} cached FAQ entries"
            )
        except Exception as e:
            logger.error(f"[gRPC] Lỗi trong InvalidateFaqCache: {e}")
            return chatbot_service_pb2.InvalidateCacheResponse(
                success=False,
                cleared_keys=0,
                message=str(e)
            )

class AsyncChatbotGRPCServer:
    def __init__(self):
        self.server = None

    async def start(self):
        self.server = aio_server()
        chatbot_service_pb2_grpc.add_ChatbotInternalServiceServicer_to_server(
            ChatbotInternalServiceImpl(), self.server
        )
        bind_address = f"0.0.0.0:{settings.GRPC_PORT}"
        self.server.add_insecure_port(bind_address)
        await self.server.start()
        logger.info(f"Chatbot gRPC Server nội bộ đã khởi động trên cổng {settings.GRPC_PORT}!")

    async def stop(self):
        if self.server:
            logger.info("Đang dừng Chatbot gRPC Server nội bộ...")
            await self.server.stop(grace=3)

chatbot_grpc_server_manager = AsyncChatbotGRPCServer()

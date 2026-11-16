import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services import redis_service, qdrant_service
from app.api import chat_router
from app.routes.internal import router as internal_router
from app.grpc_server import chatbot_grpc_server_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("chatbot-service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động kết nối
    logger.info("Chatbot AI Service đang khởi động...")
    await redis_service.connect()
    qdrant_service.ensure_collection_exists()
    try:
        from app.services.knowledge_base import sync_knowledge_base_to_qdrant
        await sync_knowledge_base_to_qdrant()
    except Exception as e:
        logger.warning(f"Lỗi khởi tạo kho tri thức cẩm nang: {e}")
    try:
        await chatbot_grpc_server_manager.start()
    except Exception as e:
        logger.warning(f"Không thể khởi động gRPC Server nội bộ: {e}")
    yield
    # Tắt kết nối
    logger.info("Chatbot AI Service đang tắt...")
    try:
        await chatbot_grpc_server_manager.stop()
    except Exception:
        pass
    await redis_service.disconnect()

app = FastAPI(
    title="Chùa Linh Ứng - Chatbot AI Service",
    description="Microservice hỏi đáp thông minh RAG đa ngôn ngữ, tích hợp Qdrant Vector DB & Gemini LLM",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(internal_router)

@app.get("/health", tags=["System"])
@app.get("/api/chatbot/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "chatbot-service",
        "redis_connected": redis_service._is_connected,
        "qdrant_collection": qdrant_service.collection_name,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)

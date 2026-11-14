import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services import redis_service, qdrant_service

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
    yield
    # Tắt kết nối
    logger.info("Chatbot AI Service đang tắt...")
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

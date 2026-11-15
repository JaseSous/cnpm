from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # JWT Auth
    JWT_SECRET_KEY: str = "change-this-to-a-super-secret-random-key-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Redis Cache (DB 1 cho Chatbot FAQ & Rate Limit)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB_CHATBOT: int = 1
    FAQ_CACHE_TTL_SECONDS: int = 86400  # 24 giờ
    RATE_LIMIT_CHAT_MAX_PER_SESSION: int = 30

    # Google Gemini AI
    GEMINI_API_KEY: str = "your-gemini-api-key"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    LLM_MODEL: str = "gemini-3.8-flash"

    # Qdrant Vector Database
    QDRANT_URL: Optional[str] = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "poi_embeddings"
    SIMILARITY_SCORE_THRESHOLD: float = 0.35
    TOP_K_VECTORS: int = 5

    # gRPC Internal Server
    GRPC_PORT: int = 50052

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

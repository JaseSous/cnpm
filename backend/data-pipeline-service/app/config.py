from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # RabbitMQ Connection
    AMQP_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_EXCHANGE: str = "poi_events"

    # gRPC Target Services
    POI_GRPC_TARGET: str = "localhost:50051"
    CHATBOT_GRPC_TARGET: str = "localhost:50052"

    # Google Gemini AI Embedding
    GEMINI_API_KEY: str = "your-gemini-api-key"
    EMBEDDING_MODEL: str = "text-embedding-004"

    # Supabase Storage cho Audio Files
    SUPABASE_URL: Optional[str] = "https://your-project-id.supabase.co"
    SUPABASE_SERVICE_KEY: Optional[str] = "your-supabase-service-role-key"
    SUPABASE_BUCKET_NAME: str = "public-media"

    # Retry và Dead-Letter Queue
    MAX_RETRIES: int = 3
    BACKOFF_BASE_SECONDS: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

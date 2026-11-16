from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # JWT Secret dùng chung để verify token từ Gateway hoặc trực tiếp
    JWT_SECRET_KEY: str = "change-this-to-a-super-secret-random-key-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Database POI DB
    POI_DB_URL: str = "sqlite+aiosqlite:///./data/poi.db"

    # Redis Cache (Logical DB 0 cho version cache nếu cần)
    REDIS_URL: str = "redis://localhost:6379/0"

    # RabbitMQ Broker
    AMQP_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_EXCHANGE: str = "poi_events"

    # gRPC Server
    GRPC_PORT: int = 50051

    # Supabase Storage (upload thumbnails)
    SUPABASE_URL: Optional[str] = "https://vaupfgylzvanpxeekytm.supabase.co"
    SUPABASE_SERVICE_KEY: Optional[str] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZhdXBmZ3lsenZhbnB4ZWVreXRtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5NDcwNjg0OSwiZXhwIjoyMTEwMjgyODQ5fQ.rZyB5jqazJVkmDM058f_JriSxKImxFj_TKZY0eoAUzI"
    SUPABASE_BUCKET_NAME: str = "public-media"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

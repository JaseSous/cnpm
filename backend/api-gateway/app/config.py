from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Port Gateway
    PORT: int = 8000

    # Downstream Microservices
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    POI_SERVICE_URL: str = "http://localhost:8002"
    CHATBOT_SERVICE_URL: str = "http://localhost:8003"

    # JWT Authentication
    JWT_SECRET_KEY: str = "change-this-to-a-super-secret-random-key-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Redis Rate Limiting (DB 0 cho Gateway & Auth)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    RATE_LIMIT_IP_MAX: int = 5000
    RATE_LIMIT_IP_WINDOW_SECONDS: int = 3600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Cấu hình JWT
    JWT_SECRET_KEY: str = "change-this-to-a-super-secret-random-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_CUSTOMER_EXPIRE_MINUTES: int = 480  # 8 tiếng cho du khách
    JWT_ADMIN_EXPIRE_MINUTES: int = 60      # 1 tiếng cho Staff/Admin

    # Cơ sở dữ liệu Auth & Payment DB
    AUTH_DB_URL: str = "sqlite+aiosqlite:///./data/auth_payment.db"

    # Redis Cache (Logical DB 0 cho Auth)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Cấu hình mã vé (shorted_code)
    SHORTED_CODE_TTL_SECONDS: int = 1800    # 30 phút hiệu lực
    SHORTED_CODE_LENGTH: int = 10

    # Giới hạn tốc độ gọi (Rate Limiting)
    RATE_LIMIT_IP_MAX: int = 100
    RATE_LIMIT_IP_WINDOW_SECONDS: int = 3600

    # Chống Brute-force LoginAttempts
    MAX_LOGIN_FAILURES: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

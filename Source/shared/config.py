# Cấu hình dùng chung cho toàn bộ hệ thống
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Chế độ lưu trữ: "local" (SQLite + in-memory cache/queue cho demo không docker) hoặc "docker" (Postgres + Redis + RabbitMQ + Qdrant)
STORAGE_MODE = os.getenv("STORAGE_MODE", "local")

# Thư mục lưu dữ liệu local
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# URL dịch vụ nội bộ
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
POI_SERVICE_URL = os.getenv("POI_SERVICE_URL", "http://localhost:8002")
CHATBOT_SERVICE_URL = os.getenv("CHATBOT_SERVICE_URL", "http://localhost:8003")
DATA_PIPELINE_SERVICE_URL = os.getenv("DATA_PIPELINE_SERVICE_URL", "http://localhost:8004")

# Cấu hình JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretjwtkey_linhung_mvp_2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Chế độ Mock
TRANSLATION_MODE = os.getenv("TRANSLATION_MODE", "mock")
TTS_MODE = os.getenv("TTS_MODE", "mock")
LLM_MODE = os.getenv("LLM_MODE", "mock")
EMBEDDING_MODE = os.getenv("EMBEDDING_MODE", "mock")
PAYMENT_MODE = os.getenv("PAYMENT_MODE", "mock")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Danh sách 15 ngôn ngữ
SUPPORTED_LANGUAGES = [
    "vi", "en", "zh", "ja", "ko",
    "fr", "de", "es", "ru", "th",
    "id", "ms", "it", "pt", "ar"
]

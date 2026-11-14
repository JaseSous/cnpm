from sqlalchemy import Column, String, Boolean
from app.database import Base

class SupportedLanguage(Base):
    """
    Bảng SupportedLanguages: Danh mục ngôn ngữ được hỗ trợ (PRD 2.1)
    """
    __tablename__ = "SupportedLanguages"

    language_code = Column(String(10), primary_key=True)
    language_name = Column(String(100), nullable=False)
    native_name = Column(String(100), nullable=False)
    is_fallback = Column(Boolean, default=False, nullable=False)
    tts_supported = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

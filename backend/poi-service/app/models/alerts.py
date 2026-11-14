from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class PipelineAlert(Base):
    """
    Bảng PipelineAlerts: Cảnh báo lỗi tiến trình xử lý dữ liệu và hỗ trợ Retry (PRD 2.7)
    """
    __tablename__ = "PipelineAlerts"

    alert_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    poi_id = Column(Integer, ForeignKey("POIs.poi_id", ondelete="CASCADE"), nullable=True)
    language_code = Column(String(10), ForeignKey("SupportedLanguages.language_code"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # 'TRANSLATION_FAILED' | 'TTS_FAILED' | 'VECTOR_FAILED' | 'DLQ_EXCEEDED'
    error_message = Column(Text, nullable=False)
    triggered_by_user_id = Column(Integer, nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    poi = relationship("POI", back_populates="alerts")

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class ProcessedEvent(Base):
    """
    Bảng ProcessedEvents: Đảm bảo tính Idempotency tránh xử lý sự kiện trùng lặp (PRD 2.6)
    """
    __tablename__ = "ProcessedEvents"

    event_id = Column(String(36), primary_key=True, index=True)
    poi_id = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

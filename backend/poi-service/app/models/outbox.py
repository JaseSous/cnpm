from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from app.database import Base

class OutboxEvent(Base):
    """
    Bảng OutboxEvents: Lưu trữ sự kiện Transactional Outbox (PRD 2.5)
    """
    __tablename__ = "OutboxEvents"

    event_id = Column(String(36), primary_key=True, index=True)  # UUID4
    poi_id = Column(Integer, ForeignKey("POIs.poi_id", ondelete="CASCADE"), nullable=True)
    event_type = Column(String(50), nullable=False)  # 'poi.upserted' | 'poi.deleted' | 'poi.retry'
    revision = Column(Integer, default=1, nullable=False)
    payload_json = Column(Text, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

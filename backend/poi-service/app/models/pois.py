from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class POI(Base):
    """
    Bảng POIs: Thông tin điểm tham quan tại Chùa Linh Ứng (PRD 2.3)
    """
    __tablename__ = "POIs"

    poi_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    original_language_code = Column(String(10), ForeignKey("SupportedLanguages.language_code"), nullable=False)
    original_title = Column(String(255), nullable=False)
    original_description = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    trigger_radius = Column(Float, default=30.0, nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    revision = Column(Integer, default=1, nullable=False)
    vector_status = Column(String(20), default="Pending", nullable=False)  # 'Pending' | 'Synced' | 'Failed'
    vector_last_error = Column(Text, nullable=True)
    vector_attempt_count = Column(Integer, default=0, nullable=False)
    vector_failed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    localizations = relationship("POILocalization", back_populates="poi", cascade="all, delete-orphan")
    alerts = relationship("PipelineAlert", back_populates="poi", cascade="all, delete-orphan")

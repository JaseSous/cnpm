from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class POILocalization(Base):
    """
    Bảng POILocalizations: Bản dịch và audio thuyết minh theo từng ngôn ngữ (PRD 2.4)
    """
    __tablename__ = "POILocalizations"
    __table_args__ = (
        UniqueConstraint("poi_id", "language_code", name="uq_poi_language"),
    )

    localization_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    poi_id = Column(Integer, ForeignKey("POIs.poi_id", ondelete="CASCADE"), nullable=False, index=True)
    language_code = Column(String(10), ForeignKey("SupportedLanguages.language_code"), nullable=False, index=True)
    translated_title = Column(String(255), nullable=True)
    translated_description = Column(Text, nullable=True)
    audio_url = Column(String(500), nullable=True)
    applied_revision = Column(Integer, default=1, nullable=False)
    status = Column(String(20), default="Pending", nullable=False)  # 'Pending' | 'Done' | 'Failed'
    last_error = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=0, nullable=False)
    failed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    poi = relationship("POI", back_populates="localizations")

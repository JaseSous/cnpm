from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime
from app.database import Base

class SystemMetadata(Base):
    """
    Bảng SystemMetadata: Phiên bản dữ liệu toàn cục cho HTTP 304 Not Modified (PRD 2.2)
    """
    __tablename__ = "SystemMetadata"

    config_key = Column(String(50), primary_key=True)
    data_version = Column(BigInteger, default=1, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class LoginAttempt(Base):
    """
    Bảng LoginAttempts: Theo dõi số lần đăng nhập thất bại và khóa tạm thời (PRD 1.3 - UC07-E3)
    """
    __tablename__ = "LoginAttempts"

    username = Column(String(50), primary_key=True, index=True)
    failed_count = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_attempt_at = Column(DateTime, default=datetime.utcnow, nullable=False)

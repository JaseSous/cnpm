from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database import Base

class User(Base):
    """
    Bảng Users: Lưu trữ tài khoản Admin và Staff (PRD 1.1)
    """
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'admin' hoặc 'staff'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    password_changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

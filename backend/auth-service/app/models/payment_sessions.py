from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from app.database import Base

class PaymentSession(Base):
    """
    Bảng PaymentSessions: Lưu thông tin phiên thanh toán vé tiền mặt và trạng thái cấp token (PRD 1.4 - UC01, UC08)
    """
    __tablename__ = "PaymentSessions"

    session_id = Column(String(36), primary_key=True, index=True)  # UUID4
    package_id = Column(Integer, ForeignKey("TicketPackages.package_id"), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    payment_method = Column(String(20), default="cash", nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default="Pending", nullable=False)  # 'Pending' -> 'Success' | 'Expired'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    activated_at = Column(DateTime, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

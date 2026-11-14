from sqlalchemy import Column, Integer, String, Numeric, Boolean
from app.database import Base

class TicketPackage(Base):
    """
    Bảng TicketPackages: Danh mục gói vé tham quan cấu hình sẵn (PRD 1.2)
    """
    __tablename__ = "TicketPackages"

    package_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    package_name = Column(String(100), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

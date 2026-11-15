from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class RecentSessionItem(BaseModel):
    session_id: str
    amount: float
    payment_method: str
    status: str
    created_at: datetime
    activated_at: Optional[datetime] = None
    token_expires_at: Optional[datetime] = None

class DashboardStatsResponse(BaseModel):
    codes_created_today: int = Field(..., description="Số mã được tạo hôm nay")
    total_codes_created: int = Field(..., description="Số mã được tạo toàn thời gian")
    pending_codes: int = Field(..., description="Số mã còn chờ kích hoạt")
    active_sessions: int = Field(..., description="Số phiên người dùng đang hoạt động (chưa hết hạn token)")
    server_time: datetime = Field(..., description="Thời gian máy chủ tại thời điểm truy vấn")
    recent_sessions: List[RecentSessionItem] = Field(default_factory=list, description="Danh sách các phiên thanh toán / kích hoạt gần nhất")

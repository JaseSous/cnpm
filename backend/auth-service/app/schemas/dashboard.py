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
    users_today: int = Field(..., description="Số lượng người dùng đã vào hệ thống trong ngày hôm nay")
    total_users: int = Field(..., description="Tổng số lượng người dùng đã từng vào hệ thống")
    active_users: int = Field(..., description="Số người đang dùng hệ thống (phiên truy cập còn hiệu lực)")
    server_time: datetime = Field(..., description="Thời gian máy chủ tại thời điểm truy vấn")
    recent_sessions: List[RecentSessionItem] = Field(default_factory=list, description="Danh sách các phiên kích hoạt gần nhất")

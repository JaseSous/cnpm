from datetime import datetime, timezone, timedelta
from typing import List
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import PaymentSession
from app.schemas.dashboard import DashboardStatsResponse, RecentSessionItem

def get_start_of_today_utc(tz_offset_hours: int = 7) -> datetime:
    """
    Tính thời điểm 00:00:00 của ngày hôm nay theo giờ Việt Nam (UTC+7)
    và chuyển về naive UTC datetime để so sánh trong database.
    """
    local_tz = timezone(timedelta(hours=tz_offset_hours))
    now_local = datetime.now(local_tz)
    start_of_today_local = datetime(now_local.year, now_local.month, now_local.day, 0, 0, 0, tzinfo=local_tz)
    return start_of_today_local.astimezone(timezone.utc).replace(tzinfo=None)

async def get_dashboard_stats(db: AsyncSession) -> DashboardStatsResponse:
    """
    Truy vấn số liệu thực tế từ bảng PaymentSessions:
    1. Số lượng người dùng đã vào hệ thống hôm nay (status = 'Success' và activated_at >= đầu ngày hôm nay GMT+7)
    2. Tổng số lượng người dùng đã từng vào hệ thống (status = 'Success')
    3. Số người đang dùng hệ thống (status = 'Success' và token_expires_at > thời điểm hiện tại UTC)
    """
    start_of_today_utc = get_start_of_today_utc(tz_offset_hours=7)
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    local_tz = timezone(timedelta(hours=7))
    server_time = datetime.now(local_tz)

    # 1. Số lượng người dùng đã vào hệ thống trong ngày hôm nay
    today_res = await db.execute(
        select(func.count(PaymentSession.session_id)).where(
            PaymentSession.status == "Success",
            PaymentSession.activated_at >= start_of_today_utc
        )
    )
    users_today = today_res.scalar() or 0

    # 2. Tổng số lượng người dùng đã từng vào hệ thống
    total_res = await db.execute(
        select(func.count(PaymentSession.session_id)).where(
            PaymentSession.status == "Success"
        )
    )
    total_users = total_res.scalar() or 0

    # 3. Số người đang dùng hệ thống (phiên còn hiệu lực: token_expires_at > now)
    active_res = await db.execute(
        select(func.count(PaymentSession.session_id)).where(
            PaymentSession.status == "Success",
            PaymentSession.token_expires_at > now_utc
        )
    )
    active_users = active_res.scalar() or 0

    # Lấy danh sách phiên gần đây để hiển thị trực quan trong Dashboard
    recent_res = await db.execute(
        select(PaymentSession)
        .order_by(desc(PaymentSession.created_at))
        .limit(10)
    )
    sessions = recent_res.scalars().all()
    recent_items = [
        RecentSessionItem(
            session_id=s.session_id,
            amount=float(s.amount),
            payment_method=s.payment_method,
            status=s.status,
            created_at=s.created_at,
            activated_at=s.activated_at,
            token_expires_at=s.token_expires_at
        )
        for s in sessions
    ]

    return DashboardStatsResponse(
        users_today=users_today,
        total_users=total_users,
        active_users=active_users,
        server_time=server_time,
        recent_sessions=recent_items
    )

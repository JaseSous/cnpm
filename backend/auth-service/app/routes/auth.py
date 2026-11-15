from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User, TicketPackage
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    VerifyCodeRequest,
    CustomerTokenResponse
)
from app.schemas.ticket import CreateTicketRequest, TicketResponse, TicketPackageResponse
from app.schemas.dashboard import DashboardStatsResponse
from app.services.auth_service import login_user
from app.services.ticket_service import create_cash_ticket, verify_and_activate_ticket
from app.services.dashboard_service import get_dashboard_stats
from app.services.security import get_current_user_payload, require_roles
from app.services.redis_client import get_redis

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="UC07: Đăng nhập Staff / Admin",
    description="Xác thực thông tin tài khoản và phát hành JWT access token kèm chống brute-force qua LoginAttempts."
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    return await login_user(db, login_data)

@router.get(
    "/me",
    summary="Lấy thông tin tài khoản đang đăng nhập",
    description="Trả về thông tin user dựa trên JWT Bearer token."
)
async def get_current_user(
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db)
):
    user_id = payload.get("user_id")
    res = await db.execute(select(User).where(User.user_id == user_id))
    user = res.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "USER_NOT_FOUND", "message": "Không tìm thấy người dùng"}
        )
    return {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at
    }

@router.get(
    "/packages",
    response_model=List[TicketPackageResponse],
    summary="Danh sách các gói vé đang mở bán",
    description="Lấy danh mục các gói vé để Staff lựa chọn khi phát hành vé cho du khách."
)
async def list_packages(
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(TicketPackage).where(TicketPackage.is_active == True)
    )
    return res.scalars().all()

@router.post(
    "/tickets",
    response_model=TicketResponse,
    summary="UC08: Bán vé tại quầy (Tạo mã vé tiền mặt)",
    description="Nhân viên quầy tạo mã vé ngắn 10 ký tự lưu vào Redis DB 0 với TTL 30 phút và phiên thanh toán Pending."
)
async def create_ticket(
    ticket_data: CreateTicketRequest,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis),
    current_user_payload: dict = Depends(require_roles(["staff", "admin"]))
):
    return await create_cash_ticket(db, redis_client, ticket_data, current_user_payload)

@router.post(
    "/verify-code",
    response_model=CustomerTokenResponse,
    summary="UC01: Du khách đổi mã vé lấy JWT Token",
    description="Kiểm tra mã vé 10 ký tự, thực hiện xóa nguyên tử GETDEL trên Redis DB 0 và cấp JWT access_token cho du khách."
)
async def verify_code(
    body: VerifyCodeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
):
    # Trích xuất địa chỉ IP của Client (hỗ trợ X-Forwarded-For nếu qua proxy)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"

    return await verify_and_activate_ticket(db, redis_client, body.shorted_code, client_ip)

@router.get(
    "/dashboard-stats",
    response_model=DashboardStatsResponse,
    summary="Thống kê người dùng cho Dashboard",
    description="Truy vấn dữ liệu thực tế từ database: số người vào hôm nay, tổng số người từng vào và số người đang dùng hệ thống."
)
async def get_dashboard_statistics(
    db: AsyncSession = Depends(get_db),
    current_user_payload: dict = Depends(require_roles(["admin", "staff"]))
):
    return await get_dashboard_stats(db)

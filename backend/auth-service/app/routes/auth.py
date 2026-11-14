from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import login_user
from app.services.security import get_current_user_payload
from app.models import User
from sqlalchemy import select

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="UC07: Đăng nhập Staff / Admin",
    description="Xác thực thông tin tài khoản và phát hành JWT access token kèm chống tấn công dò mật khẩu qua LoginAttempts."
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

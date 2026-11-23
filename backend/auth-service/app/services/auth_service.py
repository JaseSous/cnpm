from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.config import settings
from app.models import User, LoginAttempt
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.security import verify_password, create_access_token, hash_password

async def change_password(db: AsyncSession, user_id: int, current_user_role: str, old_password: str, new_password: str):
    """
    Đổi mật khẩu tài khoản và cập nhật password_changed_at
    """
    res = await db.execute(select(User).where(User.user_id == user_id))
    user = res.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "USER_NOT_FOUND", "message": "Không tìm thấy người dùng"}
        )
    
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_PASSWORD", "message": "Mật khẩu hiện tại không chính xác"}
        )
        
    user.password_hash = hash_password(new_password)
    user.password_changed_at = datetime.utcnow()
    await db.commit()
    return {"message": "Đổi mật khẩu thành công"}

async def login_user(db: AsyncSession, login_data: LoginRequest) -> TokenResponse:
    """
    UC07: Đăng nhập Staff / Admin kèm cơ chế chống Brute-force qua LoginAttempts
    """
    username = login_data.username.strip()
    now = datetime.utcnow()

    # 1. Kiểm tra tài khoản trong bảng LoginAttempts
    attempt_res = await db.execute(select(LoginAttempt).where(LoginAttempt.username == username))
    attempt = attempt_res.scalars().first()

    if attempt and attempt.failed_count >= settings.MAX_LOGIN_FAILURES and attempt.locked_until:
        if attempt.locked_until > now:
            remaining_seconds = int((attempt.locked_until - now).total_seconds())
            remaining_minutes = max(1, remaining_seconds // 60 + 1)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={
                    "error_code": "ACCOUNT_LOCKED",
                    "message": f"Tài khoản đang bị khóa tạm thời do nhập sai quá {settings.MAX_LOGIN_FAILURES} lần. Vui lòng thử lại sau {remaining_minutes} phút."
                }
            )
        else:
            # Hết thời gian khóa -> tự động reset
            attempt.failed_count = 0
            attempt.locked_until = None

    # 2. Truy vấn tài khoản người dùng
    user_res = await db.execute(
        select(User).where(User.username == username, User.is_active == True)
    )
    user = user_res.scalars().first()

    # 3. Kiểm tra tính hợp lệ của mật khẩu
    is_valid_password = False
    if user:
        is_valid_password = verify_password(login_data.password, user.password_hash)

        # Kiểm tra quy tắc đối với tài khoản admin:
        # Nếu không đổi mật khẩu trong vòng 1 ngày (24 giờ), tài khoản admin sẽ bị khóa (is_active = False)
        if user.role == "admin":
            last_changed = user.password_changed_at or user.created_at
            if last_changed and (now - last_changed) > timedelta(days=1):
                user.is_active = False
                await db.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error_code": "ADMIN_PASSWORD_EXPIRED",
                        "message": "Tài khoản admin đã bị khóa do không đổi mật khẩu trong vòng 1 ngày. Vui lòng liên hệ quản trị hệ thống."
                    }
                )

    # 4. Xử lý khi đăng nhập thất bại
    if not user or not is_valid_password:
        if not attempt:
            attempt = LoginAttempt(
                username=username,
                failed_count=1,
                last_attempt_at=now
            )
            db.add(attempt)
        else:
            attempt.failed_count += 1
            attempt.last_attempt_at = now

        if attempt.failed_count >= settings.MAX_LOGIN_FAILURES:
            attempt.locked_until = now + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={
                    "error_code": "ACCOUNT_LOCKED",
                    "message": f"Tài khoản đã bị khóa trong {settings.LOCKOUT_DURATION_MINUTES} phút do đăng nhập sai {settings.MAX_LOGIN_FAILURES} lần liên tiếp."
                }
            )

        await db.commit()
        remaining_tries = settings.MAX_LOGIN_FAILURES - attempt.failed_count
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_CREDENTIALS",
                "message": f"Tên đăng nhập hoặc mật khẩu không đúng. Còn {remaining_tries} lần thử trước khi bị khóa."
            }
        )

    # 5. Đăng nhập thành công -> Reset LoginAttempts
    if attempt:
        attempt.failed_count = 0
        attempt.locked_until = None
        attempt.last_attempt_at = now
    await db.commit()

    # 6. Sinh JWT Token
    expires_delta = timedelta(minutes=settings.JWT_ADMIN_EXPIRE_MINUTES)
    expires_at = now + expires_delta
    token_payload = {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role
    }
    access_token = create_access_token(token_payload, expires_delta=expires_delta)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.user_id,
        username=user.username,
        expires_at=expires_at
    )

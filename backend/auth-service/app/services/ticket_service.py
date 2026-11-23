import uuid
import secrets
import string
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.config import settings
from app.models import PaymentSession, TicketPackage
from app.schemas.ticket import CreateTicketRequest, TicketResponse
from app.schemas.auth import CustomerTokenResponse
from app.services.security import create_access_token

logger = logging.getLogger("auth-ticket-service")

def generate_shorted_code(length: int = 10) -> str:
    """Sinh chuỗi mã vé ngẫu nhiên gồm chữ in hoa và chữ số (PRD UC08)"""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

async def create_cash_ticket(
    db: AsyncSession,
    redis_client,
    ticket_data: CreateTicketRequest,
    current_user_payload: dict
) -> TicketResponse:
    """
    UC08: Bán vé tại quầy (Tạo mã vé tiền mặt shorted_code và phiên thanh toán)
    """
    # 1. Kiểm tra gói vé nếu có truyền package_id
    if ticket_data.package_id is not None:
        pkg_res = await db.execute(
            select(TicketPackage).where(
                TicketPackage.package_id == ticket_data.package_id,
                TicketPackage.is_active == True
            )
        )
        package = pkg_res.scalars().first()
        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "PACKAGE_NOT_FOUND", "message": "Gói vé không tồn tại hoặc đã ngừng mở bán"}
            )

    # 2. Sinh session_id UUID
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    staff_user_id = current_user_payload.get("user_id")

    # 3. Sinh mã vé shorted_code và kiểm tra trùng lặp trên Redis DB 0
    shorted_code = None
    max_retries = 5
    for attempt in range(max_retries):
        candidate_code = generate_shorted_code(settings.SHORTED_CODE_LENGTH)
        key = f"ticket:{candidate_code}"
        if not await redis_client.exists(key):
            shorted_code = candidate_code
            break

    if not shorted_code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "CODE_GENERATION_FAILED", "message": "Không thể sinh mã vé duy nhất sau nhiều lần thử"}
        )

    # 4. Lưu mã vé vào Redis DB 0 với TTL (mặc định 1800 giây = 30 phút)
    await redis_client.set(
        f"ticket:{shorted_code}",
        session_id,
        ex=settings.SHORTED_CODE_TTL_SECONDS
    )

    # 5. Lưu phiên thanh toán vào cơ sở dữ liệu PaymentSessions
    payment_session = PaymentSession(
        session_id=session_id,
        package_id=ticket_data.package_id,
        created_by_user_id=staff_user_id,
        payment_method=ticket_data.payment_method,
        amount=ticket_data.amount,
        status="Pending",
        created_at=now
    )
    db.add(payment_session)
    await db.commit()

    return TicketResponse(
        shorted_code=shorted_code,
        session_id=session_id,
        amount=ticket_data.amount,
        package_id=ticket_data.package_id,
        expires_in=settings.SHORTED_CODE_TTL_SECONDS,
        created_at=now
    )

async def verify_and_activate_ticket(
    db: AsyncSession,
    redis_client,
    raw_code: str,
    client_ip: str
) -> CustomerTokenResponse:
    """
    UC01: Du khách đổi mã nhận diện (shorted_code) lấy JWT access_token.
    Sử dụng thao tác nguyên tử GETDEL trên Redis DB 0.
    """
    # 1. Rate Limiting theo địa chỉ IP trên Redis
    rate_limit_key = f"ratelimit:ip:{client_ip}"
    attempt_count = await redis_client.incr(rate_limit_key)
    if attempt_count == 1:
        await redis_client.expire(rate_limit_key, settings.RATE_LIMIT_IP_WINDOW_SECONDS)

    if attempt_count > settings.RATE_LIMIT_IP_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": "Bạn đã thử quá số lần cho phép. Vui lòng thử lại sau."
            }
        )

    # 2. Kiểm tra định dạng mã vé (10 ký tự chữ số)
    clean_code = raw_code.strip().upper()
    if len(clean_code) != settings.SHORTED_CODE_LENGTH or not clean_code.isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_CODE_FORMAT",
                "message": f"Mã vé phải đúng {settings.SHORTED_CODE_LENGTH} ký tự chữ và số."
            }
        )

    # 3. Thao tác nguyên tử GETDEL trên Redis DB 0 (Lấy ra và xóa ngay lập tức)
    redis_ticket_key = f"ticket:{clean_code}"
    session_id = await redis_client.getdel(redis_ticket_key)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "CODE_INVALID_OR_EXPIRED",
                "message": "Mã vé không tồn tại, đã được kích hoạt trước đó hoặc đã hết hạn hiệu lực."
            }
        )

    # 4. Cập nhật PaymentSessions trong cơ sở dữ liệu (Kèm cơ chế Rollback an toàn)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_delta = timedelta(seconds=getattr(settings, "JWT_CUSTOMER_EXPIRE_SECONDS", 60))
    expires_at = now + expires_delta

    try:
        session_res = await db.execute(
            select(PaymentSession).where(PaymentSession.session_id == session_id)
        )
        payment_session = session_res.scalars().first()
        if not payment_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "SESSION_NOT_FOUND", "message": "Không tìm thấy dữ liệu phiên thanh toán"}
            )

        payment_session.status = "Success"
        payment_session.activated_at = now
        payment_session.token_expires_at = expires_at
        await db.commit()
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật PaymentSessions sau khi GETDEL: {e}. Đang khôi phục mã vé vào Redis...")
        # Khôi phục mã vé trên Redis nếu cập nhật DB gặp sự cố bất ngờ
        await redis_client.set(redis_ticket_key, session_id, ex=settings.SHORTED_CODE_TTL_SECONDS)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "ACTIVATION_FAILED", "message": "Có lỗi xảy ra khi kích hoạt vé, mã vé đã được hoàn lại."}
        )

    # 5. Sinh JWT access_token cho du khách (role="customer")
    customer_payload = {
        "session_id": session_id,
        "role": "customer"
    }
    access_token = create_access_token(customer_payload, expires_delta=expires_delta)

    return CustomerTokenResponse(
        access_token=access_token,
        token_type="bearer",
        role="customer",
        session_id=session_id,
        expires_at=expires_at
    )

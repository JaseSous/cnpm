import uuid
import secrets
import string
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.config import settings
from app.models import PaymentSession, TicketPackage
from app.schemas.ticket import CreateTicketRequest, TicketResponse

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
    now = datetime.utcnow()
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

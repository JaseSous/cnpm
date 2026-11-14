from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import SupportedLanguage
from app.schemas.poi import LanguageResponse

router = APIRouter(prefix="/api/languages", tags=["Languages"])

@router.get(
    "",
    response_model=List[LanguageResponse],
    summary="UC05: Danh sách các ngôn ngữ được hỗ trợ",
    description="Lấy danh mục 15+ ngôn ngữ hỗ trợ đang kích hoạt (bao gồm cờ is_fallback và tts_supported) phục vụ màn hình chọn ngôn ngữ của du khách và admin."
)
async def list_supported_languages(
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(SupportedLanguage)
        .where(SupportedLanguage.is_active == True)
        .order_by(SupportedLanguage.is_fallback.desc(), SupportedLanguage.language_code.asc())
    )
    return res.scalars().all()

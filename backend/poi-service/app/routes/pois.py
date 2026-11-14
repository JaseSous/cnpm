from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.poi import CreatePOIRequest, POIResponse
from app.services.poi_service import create_poi
from app.services.storage import upload_thumbnail
from app.services.security import require_roles

router = APIRouter(prefix="/api/pois", tags=["POI Management"])

@router.post(
    "",
    response_model=POIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="UC10: Admin tạo điểm tham quan mới (Transactional Outbox)",
    description="Tạo POI, khởi tạo các bản dịch ngôn ngữ trạng thái Pending, ghi sự kiện poi.upserted vào Outbox và tăng data_version trong cùng 1 transaction."
)
async def create_new_poi(
    request_data: CreatePOIRequest,
    db: AsyncSession = Depends(get_db),
    admin_payload: dict = Depends(require_roles(["admin"]))
):
    return await create_poi(db, request_data)

@router.post(
    "/upload-thumbnail",
    summary="Upload ảnh thumbnail điểm tham quan",
    description="Tải ảnh thumbnail lên Supabase Storage hoặc lưu trữ cục bộ, trả về URL của ảnh."
)
async def upload_poi_thumbnail(
    file: UploadFile = File(...),
    admin_payload: dict = Depends(require_roles(["admin"]))
):
    url = await upload_thumbnail(file)
    return {"thumbnail_url": url}

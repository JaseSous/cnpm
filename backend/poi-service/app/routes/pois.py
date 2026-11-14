from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import POI
from app.schemas.poi import CreatePOIRequest, UpdatePOIRequest, POIResponse
from app.services.poi_service import create_poi, update_poi, delete_poi
from app.services.storage import upload_thumbnail
from app.services.security import require_roles, get_current_user_payload

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

@router.put(
    "/{poi_id}",
    response_model=POIResponse,
    summary="UC10: Admin cập nhật điểm tham quan",
    description="Sửa POI. Nếu đổi tiêu đề/mô tả -> tăng revision, reset bản địa hóa sang Pending, ghi sự kiện poi.upserted vào Outbox."
)
async def update_existing_poi(
    poi_id: int,
    request_data: UpdatePOIRequest,
    db: AsyncSession = Depends(get_db),
    admin_payload: dict = Depends(require_roles(["admin"]))
):
    return await update_poi(db, poi_id, request_data)

@router.delete(
    "/{poi_id}",
    summary="UC10: Admin xóa điểm tham quan",
    description="Xóa POI và các bản địa hóa liên kết, ghi sự kiện poi.deleted vào OutboxEvents."
)
async def delete_existing_poi(
    poi_id: int,
    db: AsyncSession = Depends(get_db),
    admin_payload: dict = Depends(require_roles(["admin"]))
):
    return await delete_poi(db, poi_id)

@router.get(
    "/{poi_id}",
    response_model=POIResponse,
    summary="Lấy chi tiết một điểm tham quan (Admin)",
    description="Xem đầy đủ thông tin POI kèm trạng thái các bản địa hóa."
)
async def get_poi_detail(
    poi_id: int,
    db: AsyncSession = Depends(get_db),
    user_payload: dict = Depends(require_roles(["admin", "staff"]))
):
    res = await db.execute(
        select(POI).options(selectinload(POI.localizations)).where(POI.poi_id == poi_id)
    )
    poi = res.scalars().first()
    if not poi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "POI_NOT_FOUND", "message": "Không tìm thấy điểm tham quan"}
        )
    return poi

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

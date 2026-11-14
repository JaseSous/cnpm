import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models import (
    POI, 
    POILocalization, 
    SupportedLanguage, 
    SystemMetadata, 
    OutboxEvent, 
    PipelineAlert
)
from app.schemas.poi import CreatePOIRequest, UpdatePOIRequest

async def increment_data_version(db: AsyncSession) -> int:
    """Tăng số phiên bản dữ liệu toàn cục poi_data_version trong SystemMetadata"""
    res = await db.execute(
        select(SystemMetadata).where(SystemMetadata.config_key == "poi_data_version")
    )
    meta = res.scalars().first()
    now = datetime.utcnow()
    if not meta:
        meta = SystemMetadata(config_key="poi_data_version", data_version=1, updated_at=now)
        db.add(meta)
        await db.flush()
        return 1
    else:
        meta.data_version += 1
        meta.updated_at = now
        await db.flush()
        return meta.data_version

async def create_poi(db: AsyncSession, request_data: CreatePOIRequest) -> POI:
    """
    UC10: Admin tạo điểm tham quan mới kèm Transactional Outbox pattern
    """
    lang_res = await db.execute(
        select(SupportedLanguage).where(
            SupportedLanguage.language_code == request_data.original_language_code,
            SupportedLanguage.is_active == True
        )
    )
    if not lang_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_LANGUAGE", "message": f"Ngôn ngữ '{request_data.original_language_code}' không hợp lệ hoặc chưa được kích hoạt"}
        )

    now = datetime.utcnow()

    new_poi = POI(
        original_language_code=request_data.original_language_code,
        original_title=request_data.original_title.strip(),
        original_description=request_data.original_description.strip(),
        latitude=request_data.latitude,
        longitude=request_data.longitude,
        trigger_radius=request_data.trigger_radius,
        thumbnail_url=request_data.thumbnail_url,
        revision=1,
        vector_status="Pending",
        created_at=now,
        updated_at=now
    )
    db.add(new_poi)
    await db.flush()

    all_langs_res = await db.execute(
        select(SupportedLanguage).where(SupportedLanguage.is_active == True)
    )
    all_langs = all_langs_res.scalars().all()

    for lang in all_langs:
        is_original = (lang.language_code == request_data.original_language_code)
        loc = POILocalization(
            poi_id=new_poi.poi_id,
            language_code=lang.language_code,
            translated_title=new_poi.original_title if is_original else None,
            translated_description=new_poi.original_description if is_original else None,
            audio_url=None,
            applied_revision=1,
            status="Done" if is_original else "Pending",
            updated_at=now
        )
        db.add(loc)

    event_payload = {
        "poi_id": new_poi.poi_id,
        "revision": 1,
        "original_language_code": new_poi.original_language_code,
        "original_title": new_poi.original_title,
        "original_description": new_poi.original_description,
        "latitude": new_poi.latitude,
        "longitude": new_poi.longitude,
        "trigger_radius": new_poi.trigger_radius,
        "thumbnail_url": new_poi.thumbnail_url,
        "languages_to_process": [l.language_code for l in all_langs if l.language_code != request_data.original_language_code]
    }

    outbox_event = OutboxEvent(
        event_id=str(uuid.uuid4()),
        poi_id=new_poi.poi_id,
        event_type="poi.upserted",
        revision=1,
        payload_json=json.dumps(event_payload, ensure_ascii=False),
        is_published=False,
        created_at=now
    )
    db.add(outbox_event)

    await increment_data_version(db)
    await db.commit()

    res_final = await db.execute(
        select(POI).options(selectinload(POI.localizations)).where(POI.poi_id == new_poi.poi_id)
    )
    return res_final.scalars().first()

async def update_poi(db: AsyncSession, poi_id: int, request_data: UpdatePOIRequest) -> POI:
    """
    UC10: Admin chỉnh sửa thông tin điểm tham quan (phân biệt sửa nội dung bài thuyết minh vs sửa tọa độ)
    """
    res = await db.execute(
        select(POI).options(selectinload(POI.localizations)).where(POI.poi_id == poi_id)
    )
    poi = res.scalars().first()
    if not poi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "POI_NOT_FOUND", "message": f"Không tìm thấy điểm tham quan có mã {poi_id}"}
        )

    now = datetime.utcnow()
    content_changed = False

    # Kiểm tra thay đổi nội dung (tiêu đề, mô tả hoặc ngôn ngữ gốc) -> Cần tăng revision và re-trigger pipeline
    if request_data.original_title and request_data.original_title.strip() != poi.original_title:
        poi.original_title = request_data.original_title.strip()
        content_changed = True

    if request_data.original_description and request_data.original_description.strip() != poi.original_description:
        poi.original_description = request_data.original_description.strip()
        content_changed = True

    if request_data.original_language_code and request_data.original_language_code != poi.original_language_code:
        poi.original_language_code = request_data.original_language_code
        content_changed = True

    # Cập nhật thông tin địa lý / hình ảnh
    if request_data.latitude is not None:
        poi.latitude = request_data.latitude
    if request_data.longitude is not None:
        poi.longitude = request_data.longitude
    if request_data.trigger_radius is not None:
        poi.trigger_radius = request_data.trigger_radius
    if request_data.thumbnail_url is not None:
        poi.thumbnail_url = request_data.thumbnail_url

    poi.updated_at = now

    if content_changed:
        poi.revision += 1
        poi.vector_status = "Pending"
        poi.vector_last_error = None

        # Reset các bản địa hóa sang Pending (trừ bản địa hóa ngôn ngữ gốc là Done)
        all_langs_res = await db.execute(
            select(SupportedLanguage).where(SupportedLanguage.is_active == True)
        )
        all_langs = all_langs_res.scalars().all()

        for loc in poi.localizations:
            if loc.language_code == poi.original_language_code:
                loc.translated_title = poi.original_title
                loc.translated_description = poi.original_description
                loc.applied_revision = poi.revision
                loc.status = "Done"
            else:
                loc.applied_revision = poi.revision
                loc.status = "Pending"
                loc.last_error = None
            loc.updated_at = now

        # Ghi sự kiện vào OutboxEvents
        event_payload = {
            "poi_id": poi.poi_id,
            "revision": poi.revision,
            "original_language_code": poi.original_language_code,
            "original_title": poi.original_title,
            "original_description": poi.original_description,
            "latitude": poi.latitude,
            "longitude": poi.longitude,
            "trigger_radius": poi.trigger_radius,
            "thumbnail_url": poi.thumbnail_url,
            "languages_to_process": [l.language_code for l in all_langs if l.language_code != poi.original_language_code]
        }

        outbox_event = OutboxEvent(
            event_id=str(uuid.uuid4()),
            poi_id=poi.poi_id,
            event_type="poi.upserted",
            revision=poi.revision,
            payload_json=json.dumps(event_payload, ensure_ascii=False),
            is_published=False,
            created_at=now
        )
        db.add(outbox_event)

    # Tăng data_version để Client cập nhật
    await increment_data_version(db)
    await db.commit()

    return poi

async def delete_poi(db: AsyncSession, poi_id: int) -> Dict[str, Any]:
    """
    UC10: Admin xóa điểm tham quan POI kèm Transactional Outbox poi.deleted
    """
    res = await db.execute(select(POI).where(POI.poi_id == poi_id))
    poi = res.scalars().first()
    if not poi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "POI_NOT_FOUND", "message": f"Không tìm thấy điểm tham quan có mã {poi_id}"}
        )

    now = datetime.utcnow()

    # Ghi sự kiện poi.deleted vào OutboxEvents trước khi xóa POI
    event_payload = {
        "poi_id": poi.poi_id,
        "revision": poi.revision
    }
    outbox_event = OutboxEvent(
        event_id=str(uuid.uuid4()),
        poi_id=None,  # Không FK để tránh lỗi khi POI bị xóa
        event_type="poi.deleted",
        revision=poi.revision,
        payload_json=json.dumps(event_payload, ensure_ascii=False),
        is_published=False,
        created_at=now
    )
    db.add(outbox_event)

    # Xóa POI (cascade xóa POILocalizations, PipelineAlerts)
    await db.delete(poi)
    await increment_data_version(db)
    await db.commit()

    return {"success": True, "message": f"Đã xóa điểm tham quan {poi_id} thành công"}

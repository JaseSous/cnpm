import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
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
    # 1. Kiểm tra ngôn ngữ gốc có được hỗ trợ và đang kích hoạt không
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

    # 2. Tạo bản ghi POI
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
    await db.flush()  # Sinh poi_id

    # 3. Lấy danh sách tất cả ngôn ngữ hỗ trợ đang kích hoạt
    all_langs_res = await db.execute(
        select(SupportedLanguage).where(SupportedLanguage.is_active == True)
    )
    all_langs = all_langs_res.scalars().all()

    # 4. Tạo POILocalizations cho từng ngôn ngữ
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

    # 5. Ghi sự kiện vào OutboxEvents (Transactional Outbox Pattern)
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

    # 6. Tăng data_version
    await increment_data_version(db)

    # 7. Commit toàn bộ thay đổi trong 1 Transaction
    await db.commit()

    # Nạp kèm quan hệ localizations để trả về
    res_final = await db.execute(
        select(POI).options(selectinload(POI.localizations)).where(POI.poi_id == new_poi.poi_id)
    )
    return res_final.scalars().first()

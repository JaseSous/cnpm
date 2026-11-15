import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, and_

from app.database import AsyncSessionLocal
from app.models import POI, POILocalization, ProcessedEvent, PipelineAlert
from app.services.poi_service import increment_data_version

logger = logging.getLogger("poi-internal-http")

router = APIRouter(prefix="/api/internal", tags=["Internal Pipeline"])

class UpdateLocalizationPayload(BaseModel):
    poi_id: int
    language_code: str
    status: str
    applied_revision: int = 1
    translated_title: Optional[str] = ""
    translated_description: Optional[str] = ""
    audio_url: Optional[str] = ""
    error_message: Optional[str] = ""
    event_id: Optional[str] = ""

class UpdateVectorPayload(BaseModel):
    poi_id: int
    vector_status: str
    error_message: Optional[str] = ""
    attempt_count: int = 0

class CheckEventPayload(BaseModel):
    event_id: str

class MarkEventPayload(BaseModel):
    event_id: str
    event_type: str = "poi.upserted"

class CreateAlertPayload(BaseModel):
    alert_type: str
    severity: str = "ERROR"
    message: str
    payload: str = ""

@router.post("/localization-status")
async def update_localization_status(data: UpdateLocalizationPayload):
    async with AsyncSessionLocal() as session:
        try:
            res = await session.execute(
                select(POILocalization).where(
                    and_(
                        POILocalization.poi_id == data.poi_id,
                        POILocalization.language_code == data.language_code
                    )
                )
            )
            loc = res.scalars().first()
            now = datetime.utcnow()

            if not loc:
                loc = POILocalization(
                    poi_id=data.poi_id,
                    language_code=data.language_code,
                    applied_revision=data.applied_revision or 1,
                    updated_at=now
                )
                session.add(loc)

            if data.status == "Done":
                loc.status = "Done"
                loc.translated_title = data.translated_title or ""
                loc.translated_description = data.translated_description or ""
                loc.audio_url = data.audio_url or ""
                loc.applied_revision = data.applied_revision
                loc.last_error = None
                loc.updated_at = now

                all_locs_res = await session.execute(
                    select(POILocalization).where(POILocalization.poi_id == data.poi_id)
                )
                all_locs = all_locs_res.scalars().all()
                if all_locs and all(l.status == "Done" for l in all_locs):
                    await increment_data_version(session)
                    logger.info(f"Tất cả các ngôn ngữ của POI {data.poi_id} đã hoàn tất. Tăng data_version.")
            elif data.status in ["Translating", "GeneratingAudio"]:
                loc.status = data.status
                loc.updated_at = now
            else:
                loc.status = "Failed"
                loc.last_error = data.error_message
                loc.attempt_count += 1
                loc.failed_at = now
                loc.updated_at = now

            await session.commit()
            return {"success": True, "message": "Updated"}
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating localization status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/vector-status")
async def update_vector_status(data: UpdateVectorPayload):
    async with AsyncSessionLocal() as session:
        try:
            res = await session.execute(select(POI).where(POI.poi_id == data.poi_id))
            poi = res.scalars().first()
            if poi:
                poi.vector_status = data.vector_status
                poi.vector_attempt_count = data.attempt_count
                if data.vector_status == "Failed":
                    poi.vector_last_error = data.error_message
                    poi.vector_failed_at = datetime.utcnow()
                else:
                    poi.vector_last_error = None
                await session.commit()
                return {"success": True}
            raise HTTPException(status_code=404, detail="POI not found")
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-event")
async def check_event(data: CheckEventPayload):
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(ProcessedEvent).where(ProcessedEvent.event_id == data.event_id)
        )
        return {"is_processed": bool(res.scalars().first())}

@router.post("/mark-event")
async def mark_event(data: MarkEventPayload):
    async with AsyncSessionLocal() as session:
        try:
            processed = ProcessedEvent(
                event_id=data.event_id,
                poi_id=0,
                event_type=data.event_type,
                processed_at=datetime.utcnow()
            )
            session.add(processed)
            await session.commit()
            return {"success": True}
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/alert")
async def create_alert(data: CreateAlertPayload):
    async with AsyncSessionLocal() as session:
        try:
            alert = PipelineAlert(
                alert_type=data.alert_type,
                error_message=f"[{data.severity}] {data.message} | Payload: {data.payload}",
                is_resolved=False,
                created_at=datetime.utcnow()
            )
            session.add(alert)
            await session.commit()
            return {"success": True, "alert_id": alert.alert_id}
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

import sys
import logging
from pathlib import Path
from datetime import datetime
from sqlalchemy import select, and_
import grpc
from grpc.aio import server as aio_server

# Đảm bảo import được các module pb2 tự sinh
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import poi_service_pb2
import poi_service_pb2_grpc

from app.database import AsyncSessionLocal
from app.models import POI, POILocalization, ProcessedEvent, PipelineAlert, SupportedLanguage
from app.services.poi_service import increment_data_version
from app.config import settings

logger = logging.getLogger("poi-grpc-server")

class POIInternalServiceImpl(poi_service_pb2_grpc.POIInternalServiceServicer):
    async def UpdateLocalizationStatus(self, request, context):
        """Cập nhật kết quả dịch thuật và audio của một ngôn ngữ cho POI"""
        async with AsyncSessionLocal() as session:
            try:
                res = await session.execute(
                    select(POILocalization).where(
                        and_(
                            POILocalization.poi_id == request.poi_id,
                            POILocalization.language_code == request.language_code
                        )
                    )
                )
                loc = res.scalars().first()
                now = datetime.utcnow()

                if not loc:
                    # Nếu chưa có bản ghi thì tạo mới
                    loc = POILocalization(
                        poi_id=request.poi_id,
                        language_code=request.language_code,
                        applied_revision=request.applied_revision or 1,
                        updated_at=now
                    )
                    session.add(loc)

                if request.status == "Done":
                    loc.status = "Done"
                    loc.translated_title = request.translated_title
                    loc.translated_description = request.translated_description
                    loc.audio_url = request.audio_url
                    loc.applied_revision = request.applied_revision
                    loc.last_error = None
                    loc.updated_at = now

                    # Kiểm tra xem tất cả các ngôn ngữ của POI đã Done chưa -> tăng data_version
                    all_locs_res = await session.execute(
                        select(POILocalization).where(POILocalization.poi_id == request.poi_id)
                    )
                    all_locs = all_locs_res.scalars().all()
                    if all_locs and all(l.status == "Done" for l in all_locs):
                        await increment_data_version(session)
                        logger.info(f"Tất cả các ngôn ngữ của POI {request.poi_id} đã hoàn tất. Tăng data_version.")
                else:
                    loc.status = "Failed"
                    loc.last_error = request.error_message
                    loc.attempt_count += 1
                    loc.failed_at = now
                    loc.updated_at = now

                await session.commit()
                return poi_service_pb2.UpdateLocalizationResponse(
                    success=True,
                    message="Cập nhật trạng thái bản địa hóa thành công"
                )
            except Exception as e:
                logger.error(f"Lỗi khi UpdateLocalizationStatus: {e}")
                await session.rollback()
                return poi_service_pb2.UpdateLocalizationResponse(
                    success=False,
                    message=str(e)
                )

    async def UpdateVectorStatus(self, request, context):
        """Cập nhật trạng thái đồng bộ Vector DB cho POI"""
        async with AsyncSessionLocal() as session:
            try:
                res = await session.execute(select(POI).where(POI.poi_id == request.poi_id))
                poi = res.scalars().first()
                if poi:
                    poi.vector_status = request.vector_status
                    poi.vector_attempt_count = request.attempt_count
                    if request.vector_status == "Failed":
                        poi.vector_last_error = request.error_message
                        poi.vector_failed_at = datetime.utcnow()
                    else:
                        poi.vector_last_error = None
                    await session.commit()
                    return poi_service_pb2.UpdateVectorResponse(success=True, message="Đã cập nhật vector status")
                return poi_service_pb2.UpdateVectorResponse(success=False, message="POI not found")
            except Exception as e:
                await session.rollback()
                return poi_service_pb2.UpdateVectorResponse(success=False, message=str(e))

    async def CreatePipelineAlert(self, request, context):
        """Ghi nhận cảnh báo lỗi xử lý dữ liệu vào PipelineAlerts"""
        async with AsyncSessionLocal() as session:
            try:
                alert = PipelineAlert(
                    alert_type=request.alert_type,
                    error_message=f"[{request.severity}] {request.message} | Payload: {request.payload}",
                    is_resolved=False,
                    created_at=datetime.utcnow()
                )
                session.add(alert)
                await session.commit()
                return poi_service_pb2.CreateAlertResponse(
                    success=True,
                    alert_id=alert.alert_id,
                    message="Alert created"
                )
            except Exception as e:
                await session.rollback()
                return poi_service_pb2.CreateAlertResponse(success=False, alert_id=0, message=str(e))

    async def CheckProcessedEvent(self, request, context):
        """Kiểm tra Idempotency: Sự kiện đã được xử lý thành công chưa"""
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(ProcessedEvent).where(ProcessedEvent.event_id == request.event_id)
            )
            exists = bool(res.scalars().first())
            return poi_service_pb2.CheckEventResponse(is_processed=exists)

    async def MarkEventProcessed(self, request, context):
        """Ghi nhận sự kiện đã xử lý thành công vào ProcessedEvents"""
        async with AsyncSessionLocal() as session:
            try:
                processed = ProcessedEvent(
                    event_id=request.event_id,
                    poi_id=0,
                    event_type=request.event_type,
                    processed_at=datetime.utcnow()
                )
                session.add(processed)
                await session.commit()
                return poi_service_pb2.MarkEventResponse(success=True, message="Event marked processed")
            except Exception as e:
                await session.rollback()
                return poi_service_pb2.MarkEventResponse(success=False, message=str(e))

class AsyncGRPCServer:
    def __init__(self):
        self.server = None

    async def start(self):
        self.server = aio_server()
        poi_service_pb2_grpc.add_POIInternalServiceServicer_to_server(
            POIInternalServiceImpl(), self.server
        )
        bind_address = f"0.0.0.0:{settings.GRPC_PORT}"
        self.server.add_insecure_port(bind_address)
        await self.server.start()
        logger.info(f"gRPC Server nội bộ đã khởi động trên cổng {settings.GRPC_PORT}!")

    async def stop(self):
        if self.server:
            logger.info("Đang dừng gRPC Server nội bộ...")
            await self.server.stop(grace=3)

grpc_server_manager = AsyncGRPCServer()

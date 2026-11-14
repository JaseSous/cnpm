import sys
import logging
from pathlib import Path
from typing import Optional
import grpc

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import poi_service_pb2
import poi_service_pb2_grpc
from app.config import settings

logger = logging.getLogger("poi-grpc-client")

class POIServiceClient:
    def __init__(self, target: Optional[str] = None):
        self.target = target or settings.POI_GRPC_TARGET

    async def check_processed_event(self, event_id: str) -> bool:
        """Kiểm tra Idempotency: Sự kiện đã được xử lý xong trước đó chưa"""
        try:
            async with grpc.aio.insecure_channel(self.target) as channel:
                stub = poi_service_pb2_grpc.POIInternalServiceStub(channel)
                res = await stub.CheckProcessedEvent(
                    poi_service_pb2.CheckEventRequest(event_id=event_id),
                    timeout=5
                )
                return res.is_processed
        except Exception as e:
            logger.warning(f"Lỗi khi gọi gRPC CheckProcessedEvent ({e}). Giả định chưa xử lý.")
            return False

    async def mark_event_processed(self, event_id: str, event_type: str = "poi.upserted") -> bool:
        """Đánh dấu sự kiện đã xử lý thành công"""
        try:
            async with grpc.aio.insecure_channel(self.target) as channel:
                stub = poi_service_pb2_grpc.POIInternalServiceStub(channel)
                res = await stub.MarkEventProcessed(
                    poi_service_pb2.MarkEventRequest(
                        event_id=event_id,
                        event_type=event_type,
                        source_service="data-pipeline-service"
                    ),
                    timeout=5
                )
                return res.success
        except Exception as e:
            logger.error(f"Lỗi khi gọi gRPC MarkEventProcessed ({e})")
            return False

    async def update_localization_status(
        self,
        poi_id: int,
        language_code: str,
        status: str,
        applied_revision: int,
        translated_title: str = "",
        translated_description: str = "",
        audio_url: str = "",
        error_message: str = "",
        event_id: str = ""
    ) -> bool:
        """Cập nhật trạng thái bản dịch/audio của ngôn ngữ về POI Service"""
        try:
            async with grpc.aio.insecure_channel(self.target) as channel:
                stub = poi_service_pb2_grpc.POIInternalServiceStub(channel)
                req = poi_service_pb2.UpdateLocalizationRequest(
                    event_id=event_id,
                    poi_id=poi_id,
                    language_code=language_code,
                    status=status,
                    translated_title=translated_title,
                    translated_description=translated_description,
                    audio_url=audio_url,
                    error_message=error_message,
                    applied_revision=applied_revision
                )
                res = await stub.UpdateLocalizationStatus(req, timeout=5)
                return res.success
        except Exception as e:
            logger.error(f"Lỗi khi gọi gRPC UpdateLocalizationStatus ({e})")
            return False

    async def update_vector_status(
        self,
        poi_id: int,
        status: str,
        error_message: str = "",
        attempt_count: int = 0
    ) -> bool:
        """Cập nhật trạng thái vector status về POI Service"""
        try:
            async with grpc.aio.insecure_channel(self.target) as channel:
                stub = poi_service_pb2_grpc.POIInternalServiceStub(channel)
                req = poi_service_pb2.UpdateVectorRequest(
                    poi_id=poi_id,
                    vector_status=status,
                    error_message=error_message,
                    attempt_count=attempt_count
                )
                res = await stub.UpdateVectorStatus(req, timeout=5)
                return res.success
        except Exception as e:
            logger.error(f"Lỗi khi gọi gRPC UpdateVectorStatus ({e})")
            return False

    async def create_pipeline_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        payload: str = ""
    ) -> int:
        """Ghi nhận cảnh báo lỗi đường ống xử lý dữ liệu"""
        try:
            async with grpc.aio.insecure_channel(self.target) as channel:
                stub = poi_service_pb2_grpc.POIInternalServiceStub(channel)
                req = poi_service_pb2.CreateAlertRequest(
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    payload=payload
                )
                res = await stub.CreatePipelineAlert(req, timeout=5)
                return res.alert_id if res.success else 0
        except Exception as e:
            logger.error(f"Lỗi khi gọi gRPC CreatePipelineAlert ({e})")
            return 0

poi_grpc_client = POIServiceClient()

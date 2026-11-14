import logging
from typing import Dict, Any
from app.grpc_clients import poi_grpc_client, chatbot_grpc_client
from app.services import storage_service

logger = logging.getLogger("consumer-poi-deleted")

async def handle_poi_deleted(payload: Dict[str, Any]) -> bool:
    """
    Xử lý sự kiện poi.deleted:
    1. Kiểm tra Idempotency qua CheckProcessedEvent
    2. Xóa các tệp âm thanh thuyết minh (Object Storage / Local)
    3. Gọi Chatbot Service gRPC để xóa vector chunks trong Qdrant
    4. Gọi Chatbot Service gRPC để invalidate FAQ cache trong Redis
    5. Đánh dấu sự kiện đã xử lý qua MarkEventProcessed
    """
    event_id = payload.get("event_id", "")
    poi_id = payload.get("poi_id")

    if not poi_id:
        logger.error(f"Sự kiện poi.deleted thiếu poi_id: {payload}")
        return False

    if event_id:
        is_processed = await poi_grpc_client.check_processed_event(event_id)
        if is_processed:
            logger.info(f"Sự kiện poi.deleted {event_id} đã được xử lý trước đó. Bỏ qua.")
            return True

    logger.info(f"Bắt đầu xử lý dọn dẹp tài nguyên cho POI #{poi_id} (event: {event_id})")

    # 1. Xóa các audio files cục bộ và trên Object Storage
    try:
        deleted_audios = await storage_service.delete_poi_audios(poi_id)
        logger.info(f"Đã xóa {deleted_audios} tệp âm thanh của POI #{poi_id}")
    except Exception as e:
        logger.warning(f"Lỗi khi xóa tệp âm thanh POI #{poi_id}: {e}")

    # 2. Xóa vectors trong Qdrant
    try:
        deleted_vectors = await chatbot_grpc_client.delete_vectors(poi_id)
        logger.info(f"Kết quả xóa vectors trong Chatbot Service: {deleted_vectors}")
    except Exception as e:
        logger.warning(f"Lỗi khi xóa vectors POI #{poi_id}: {e}")

    # 3. Invalidate FAQ Cache trên Redis
    try:
        cleared_cache = await chatbot_grpc_client.invalidate_faq_cache(poi_id=poi_id)
        logger.info(f"Kết quả xóa FAQ cache: {cleared_cache}")
    except Exception as e:
        logger.warning(f"Lỗi khi xóa cache FAQ: {e}")

    # 4. Đánh dấu sự kiện đã xử lý thành công
    if event_id:
        await poi_grpc_client.mark_event_processed(
            event_id=event_id,
            event_type="poi.deleted"
        )

    logger.info(f"Hoàn tất xử lý poi.deleted cho POI #{poi_id}")
    return True

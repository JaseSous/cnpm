import logging
from typing import Tuple, Optional
from app.grpc_clients import poi_grpc_client

logger = logging.getLogger("pipeline-guard")

async def check_idempotency_and_revision(
    event_id: str,
    poi_id: int,
    revision: int,
    client=None,
    current_revision: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Kiểm tra tính Idempotency và Revision Guard trước khi tiêu thụ message:
    1. Kiểm tra event_id đã có trong ProcessedEvents chưa qua gRPC.
    2. Chống lỗi out-of-order message khi mạng bị delay (revision < current_revision).
    3. Kiểm tra revision hợp lệ (revision >= 1).
    """
    grpc_client = client or poi_grpc_client

    # 1. Kiểm tra Idempotency
    is_processed = await grpc_client.check_processed_event(event_id)
    if is_processed:
        logger.info(f"Sự kiện {event_id} đã được xử lý thành công trước đó. Bỏ qua để đảm bảo Idempotency.")
        return False, "ALREADY_PROCESSED"

    # 2. Kiểm tra Revision hợp lệ
    if revision < 1:
        logger.warning(f"Sự kiện có revision không hợp lệ: {revision}. Bỏ qua.")
        return False, "INVALID_REVISION"

    # 3. Chống lỗi out-of-order message khi mạng bị delay (revision < current_revision)
    if current_revision is not None and revision < current_revision:
        logger.warning(
            f"Sự kiện POI #{poi_id} có revision={revision} cũ hơn revision hiện tại ({current_revision}). Bỏ qua."
        )
        return False, "OUTDATED_REVISION"

    return True, "PROCEED"

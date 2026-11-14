import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import aio_pika

from app.config import settings
from app.grpc_clients import poi_grpc_client, chatbot_grpc_client
from app.consumers.guard import check_idempotency_and_revision
from app.services import (
    translate_poi_content,
    generate_speech_audio,
    upload_audio_file,
    embedding_service
)

logger = logging.getLogger("consumer-poi-upserted")

DEFAULT_TARGET_LANGUAGES = [
    "vi", "en", "zh", "ja", "ko", "fr", "de", "es",
    "th", "ru", "pt", "it", "id", "ar", "hi"
]

async def process_poi_upserted(
    payload: Dict[str, Any],
    channel: aio_pika.RobustChannel = None
) -> bool:
    """
    Xử lý sự kiện poi.upserted hoặc poi.retry:
    1. Kiểm tra Idempotency & Revision Guard
    2. Cập nhật trạng thái bản địa hóa: Dịch thuật đa ngôn ngữ -> TTS sinh Audio -> Upload CDN
    3. Sinh Vector Embeddings qua Gemini -> Upsert vào Qdrant qua Chatbot Service
    4. Quản lý Retry với Exponential Backoff & Dead-Letter Queue (DLQ)
    """
    event_id = payload.get("event_id", "")
    poi_id = payload.get("poi_id")
    revision = payload.get("revision", 1)
    title = payload.get("title", "")
    description = payload.get("description", "")
    primary_language = payload.get("primary_language", "vi")
    target_languages = payload.get("target_languages") or DEFAULT_TARGET_LANGUAGES
    attempt_count = payload.get("attempt_count", 0)

    if not poi_id:
        logger.error(f"Sự kiện poi.upserted không có poi_id: {payload}")
        return False

    # 1. Guard check
    current_revision = payload.get("current_revision") or payload.get("applied_revision")
    can_proceed, reason = await check_idempotency_and_revision(
        event_id, poi_id, revision, current_revision=current_revision
    )
    if not can_proceed:
        logger.info(f"Bỏ qua xử lý POI #{poi_id} rev {revision} do: {reason}")
        return True

    logger.info(
        f"Bắt đầu xử lý POI #{poi_id} '{title}' (rev {revision}), attempt {attempt_count + 1}/{settings.MAX_RETRIES}"
    )

    try:
        # Cập nhật Vector status ban đầu: InProgress
        await poi_grpc_client.update_vector_status(
            poi_id=poi_id,
            status="InProgress",
            attempt_count=attempt_count + 1
        )

        temp_audio_dir = Path("./data/temp_audio")
        temp_audio_dir.mkdir(parents=True, exist_ok=True)

        # 2. Xử lý đa ngôn ngữ: Dịch thuật, TTS và Upload
        for lang in target_languages:
            try:
                # Đánh dấu trạng thái đang dịch
                await poi_grpc_client.update_localization_status(
                    poi_id=poi_id,
                    language_code=lang,
                    status="Translating",
                    applied_revision=revision,
                    event_id=event_id
                )

                # Dịch tiêu đề và mô tả
                translated = await translate_poi_content(
                    title=title,
                    description=description,
                    target_lang=lang,
                    source_lang=primary_language
                )
                t_title = translated.get("title", title)
                t_desc = translated.get("description", description)

                # Đánh dấu trạng thái đang sinh audio
                await poi_grpc_client.update_localization_status(
                    poi_id=poi_id,
                    language_code=lang,
                    status="GeneratingAudio",
                    applied_revision=revision,
                    translated_title=t_title,
                    translated_description=t_desc,
                    event_id=event_id
                )

                # Sinh Audio TTS
                audio_temp_file = temp_audio_dir / f"poi_{poi_id}_{lang}_rev{revision}.mp3"
                tts_text = f"{t_title}. {t_desc}"
                await generate_speech_audio(tts_text, lang, audio_temp_file)

                # Upload lên Storage (Supabase hoặc Local media)
                audio_url = await upload_audio_file(
                    file_path=audio_temp_file,
                    poi_id=poi_id,
                    language_code=lang,
                    revision=revision
                )

                # Xóa file tạm
                if audio_temp_file.exists():
                    try:
                        audio_temp_file.unlink()
                    except Exception:
                        pass

                # Cập nhật trạng thái Ready cho ngôn ngữ này
                await poi_grpc_client.update_localization_status(
                    poi_id=poi_id,
                    language_code=lang,
                    status="Ready",
                    applied_revision=revision,
                    translated_title=t_title,
                    translated_description=t_desc,
                    audio_url=audio_url,
                    event_id=event_id
                )
                logger.info(f"POI #{poi_id} ngôn ngữ '{lang}' đã Ready! Audio: {audio_url}")

            except Exception as lang_err:
                logger.error(f"Lỗi khi xử lý ngôn ngữ '{lang}' cho POI #{poi_id}: {lang_err}")
                await poi_grpc_client.update_localization_status(
                    poi_id=poi_id,
                    language_code=lang,
                    status="Failed",
                    applied_revision=revision,
                    error_message=str(lang_err),
                    event_id=event_id
                )

        # 3. Tạo Vector Embeddings và đồng bộ vào Chatbot Service (Qdrant)
        vector_success = await embedding_service.sync_poi_embeddings(
            poi_id=poi_id,
            revision=revision,
            language_code=primary_language,
            title=title,
            description=description
        )

        # 4. Invalidate FAQ Cache trên Chatbot Service để chatbot cập nhật tri thức mới
        await chatbot_grpc_client.invalidate_faq_cache(poi_id=poi_id)

        # 5. Đánh dấu sự kiện đã xử lý thành công vào ProcessedEvents
        if event_id:
            await poi_grpc_client.mark_event_processed(
                event_id=event_id,
                event_type="poi.upserted"
            )

        logger.info(f"Hoàn thành toàn bộ quy trình pipeline cho POI #{poi_id} (rev {revision})!")
        return True

    except Exception as exc:
        new_attempt = attempt_count + 1
        logger.error(
            f"Lỗi xảy ra trong quá trình pipeline POI #{poi_id}: {exc} (lần thử {new_attempt})"
        )

        # Quản lý Retry với Exponential Backoff
        if new_attempt < settings.MAX_RETRIES:
            backoff_delay = settings.BACKOFF_BASE_SECONDS ** new_attempt
            logger.info(
                f"Sẽ thử lại POI #{poi_id} sau {backoff_delay} giây (attempt {new_attempt})..."
            )
            payload["attempt_count"] = new_attempt

            if channel:
                # Đợi exponential backoff và publish vào queue poi.retry
                await asyncio.sleep(backoff_delay)
                try:
                    retry_body = json.dumps(payload).encode("utf-8")
                    await channel.default_exchange.publish(
                        aio_pika.Message(
                            body=retry_body,
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                        ),
                        routing_key="poi.retry"
                    )
                    logger.info(f"Đã đưa POI #{poi_id} vào hàng đợi poi.retry thành công")
                except Exception as pub_err:
                    logger.error(f"Không thể publish vào poi.retry: {pub_err}")
            return False

        # Nếu vượt quá số lần retry tối đa -> Gửi sang Dead-Letter Queue & Báo động Admin
        logger.error(f"POI #{poi_id} đã thất bại cả {new_attempt} lần. Chuyển vào Dead-Letter Queue!")
        if channel:
            try:
                dlq_body = json.dumps(payload).encode("utf-8")
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=dlq_body,
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                    ),
                    routing_key="poi.dlq"
                )
            except Exception as dlq_err:
                logger.error(f"Không thể gửi sang DLQ: {dlq_err}")

        # Ghi nhận cảnh báo hệ thống qua gRPC CreatePipelineAlert
        alert_id = await poi_grpc_client.create_pipeline_alert(
            alert_type="PIPELINE_FAILED",
            severity="HIGH",
            message=f"Đường ống xử lý POI #{poi_id} (rev {revision}) thất bại sau {new_attempt} lần: {exc}",
            payload=json.dumps(payload)
        )
        logger.warning(f"Đã tạo cảnh báo PipelineAlert ID #{alert_id} cho Admin")

        # Cập nhật Vector status là Failed
        await poi_grpc_client.update_vector_status(
            poi_id=poi_id,
            status="Failed",
            error_message=str(exc),
            attempt_count=new_attempt
        )
        return False

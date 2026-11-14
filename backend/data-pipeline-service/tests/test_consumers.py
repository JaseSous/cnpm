import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.consumers.guard import check_idempotency_and_revision
from app.consumers.poi_deleted import handle_poi_deleted
from app.consumers.poi_upserted import process_poi_upserted

@pytest.mark.asyncio
async def test_guard_already_processed(mock_poi_grpc):
    mock_poi_grpc.check_processed_event.return_value = True
    ok, reason = await check_idempotency_and_revision("evt_123", 1, 1, client=mock_poi_grpc)
    assert ok is False
    assert reason == "ALREADY_PROCESSED"

@pytest.mark.asyncio
async def test_guard_invalid_revision(mock_poi_grpc):
    mock_poi_grpc.check_processed_event.return_value = False
    ok, reason = await check_idempotency_and_revision("evt_124", 1, 0, client=mock_poi_grpc)
    assert ok is False
    assert reason == "INVALID_REVISION"

@pytest.mark.asyncio
async def test_guard_valid_proceed(mock_poi_grpc):
    mock_poi_grpc.check_processed_event.return_value = False
    ok, reason = await check_idempotency_and_revision("evt_125", 1, 2, client=mock_poi_grpc)
    assert ok is True
    assert reason == "PROCEED"

@pytest.mark.asyncio
async def test_guard_outdated_revision(mock_poi_grpc):
    mock_poi_grpc.check_processed_event.return_value = False
    ok, reason = await check_idempotency_and_revision("evt_126", 1, 1, client=mock_poi_grpc, current_revision=2)
    assert ok is False
    assert reason == "OUTDATED_REVISION"

@pytest.mark.asyncio
async def test_handle_poi_deleted_missing_id():
    res = await handle_poi_deleted({})
    assert res is False

@pytest.mark.asyncio
async def test_handle_poi_deleted_success(mock_poi_grpc, mock_chatbot_grpc):
    with patch("app.services.storage_service.delete_poi_audios", new_callable=AsyncMock) as mock_del_audios:
        mock_del_audios.return_value = 2
        payload = {"event_id": "evt_del_1", "poi_id": 10}
        res = await handle_poi_deleted(payload)
        assert res is True
        mock_del_audios.assert_called_with(10)
        mock_chatbot_grpc.delete_vectors.assert_called_with(10)
        mock_chatbot_grpc.invalidate_faq_cache.assert_called_with(poi_id=10)
        mock_poi_grpc.mark_event_processed.assert_called_with(
            event_id="evt_del_1",
            event_type="poi.deleted"
        )

@pytest.mark.asyncio
async def test_process_poi_upserted_success(mock_poi_grpc, mock_chatbot_grpc):
    payload = {
        "event_id": "evt_upsert_1",
        "poi_id": 5,
        "revision": 1,
        "title": "Cổng Tam Quan",
        "description": "Cổng vào chính của chùa Linh Ứng",
        "primary_language": "vi",
        "target_languages": ["en"]
    }
    
    with patch("app.services.translate_poi_content", new_callable=AsyncMock) as mock_trans:
        mock_trans.return_value = {"title": "Three-Entrance Gate", "description": "Main gate"}
        with patch("app.services.generate_speech_audio", new_callable=AsyncMock) as mock_tts:
            mock_tts.return_value = True
            with patch("app.services.upload_audio_file", new_callable=AsyncMock) as mock_up:
                mock_up.return_value = "https://cdn.example.com/audio.mp3"
                
                res = await process_poi_upserted(payload)
                assert res is True
                mock_poi_grpc.update_localization_status.assert_called()
                mock_chatbot_grpc.invalidate_faq_cache.assert_called_with(poi_id=5)
                mock_poi_grpc.mark_event_processed.assert_called_with(
                    event_id="evt_upsert_1",
                    event_type="poi.upserted"
                )

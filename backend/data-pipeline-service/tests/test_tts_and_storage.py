import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from app.services.tts_service import generate_speech_audio
from app.services.storage import upload_audio_file, delete_audio_files_for_poi, get_audio_storage_url

@pytest.mark.asyncio
async def test_generate_speech_audio_fallback(tmp_path):
    output_file = tmp_path / "test_audio.mp3"
    # Giả lập lỗi edge-tts và gTTS để kiểm tra dummy mp3 fallback an toàn
    with patch("edge_tts.Communicate.save", side_effect=Exception("Handshake error")):
        with patch("gtts.gTTS.save", side_effect=Exception("Network error")):
            success = await generate_speech_audio(
                text="Xin chào quý khách đến với Linh Ứng",
                language_code="vi",
                output_path=output_file
            )
            assert success is True
            assert output_file.exists()
            assert output_file.stat().st_size > 0

@pytest.mark.asyncio
async def test_upload_audio_file_local_fallback(tmp_path):
    # Tạo dummy audio file
    source_file = tmp_path / "sample.mp3"
    source_file.write_bytes(b"dummy mp3 data")

    # Upload không có supabase url -> local fallback
    url = await upload_audio_file(
        file_path=source_file,
        poi_id=99,
        language_code="en",
        revision=1
    )
    assert url.startswith("/media/audios/poi_99_en_rev1.mp3")

@pytest.mark.asyncio
async def test_delete_audio_files_for_poi(tmp_path):
    local_dir = Path("./data/uploads/audios")
    local_dir.mkdir(parents=True, exist_ok=True)
    test_file = local_dir / "poi_99_en_rev1.mp3"
    test_file.write_bytes(b"temp")

    deleted = await delete_audio_files_for_poi(poi_id=99)
    assert deleted >= 1
    assert not test_file.exists()

def test_get_audio_storage_url():
    url = get_audio_storage_url(poi_id=1, language_code="vi", revision=2)
    assert "poi_1_vi_rev2.mp3" in url

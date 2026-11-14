import os
import logging
from pathlib import Path
from app.config import settings

logger = logging.getLogger("pipeline-storage")

async def upload_audio_file(
    file_path: Path,
    poi_id: int,
    language_code: str,
    revision: int
) -> str:
    """
    Upload tệp âm thanh thuyết minh lên Object Storage theo quy chuẩn PRD 5:
    audios/poi_{poi_id}_{language_code}_rev{revision}.mp3
    """
    filename = f"poi_{poi_id}_{language_code}_rev{revision}.mp3"
    path_in_bucket = f"audios/{filename}"

    # 1. Thử upload lên Supabase Storage
    if settings.SUPABASE_URL and "your-project-id" not in settings.SUPABASE_URL:
        try:
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            with open(file_path, "rb") as f:
                content = f.read()

            supabase.storage.from_(settings.SUPABASE_BUCKET_NAME).upload(
                path=path_in_bucket,
                file=content,
                file_options={"content-type": "audio/mpeg", "upsert": "true"}
            )
            public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET_NAME}/{path_in_bucket}"
            logger.info(f"Đã upload audio lên Supabase: {public_url}")
            return public_url
        except Exception as e:
            logger.warning(f"Không thể upload lên Supabase Storage ({e}). Sử dụng local media fallback...")

    # 2. Local Fallback
    local_dir = Path("./data/uploads/audios")
    local_dir.mkdir(parents=True, exist_ok=True)
    dest_path = local_dir / filename
    
    with open(file_path, "rb") as src, open(dest_path, "wb") as dst:
        dst.write(src.read())

    return f"/media/audios/{filename}"

async def delete_audio_files_for_poi(poi_id: int) -> int:
    """
    Xóa tất cả các file âm thanh thuộc về POI khi có sự kiện poi.deleted
    """
    count = 0
    # Xóa file cục bộ
    local_dir = Path("./data/uploads/audios")
    if local_dir.exists():
        for f in local_dir.glob(f"poi_{poi_id}_*.mp3"):
            try:
                f.unlink()
                count += 1
            except Exception:
                pass

    # Xóa trên Supabase Storage nếu có kết nối
    if settings.SUPABASE_URL and "your-project-id" not in settings.SUPABASE_URL:
        try:
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            files = supabase.storage.from_(settings.SUPABASE_BUCKET_NAME).list(path="audios")
            matched = [item["name"] for item in files if item["name"].startswith(f"poi_{poi_id}_")]
            if matched:
                supabase.storage.from_(settings.SUPABASE_BUCKET_NAME).remove([f"audios/{name}" for name in matched])
                count += len(matched)
        except Exception as e:
            logger.warning(f"Lỗi khi xóa file audio trên Supabase ({e})")

    return count


class StorageService:
    async def upload(self, file_path: Path, poi_id: int, language_code: str, revision: int) -> str:
        return await upload_audio_file(file_path, poi_id, language_code, revision)
        
    async def delete_poi_audios(self, poi_id: int) -> int:
        return await delete_audio_files_for_poi(poi_id)

storage_service = StorageService()

def get_audio_storage_url(poi_id: int, language_code: str, revision: int) -> str:
    filename = f"poi_{poi_id}_{language_code}_rev{revision}.mp3"
    path_in_bucket = f"audios/{filename}"
    if settings.SUPABASE_URL and "your-project-id" not in settings.SUPABASE_URL:
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET_NAME}/{path_in_bucket}"
    return f"/media/audios/{filename}"

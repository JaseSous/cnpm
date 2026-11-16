import os
import uuid
import logging
from pathlib import Path
from fastapi import UploadFile
import httpx
from app.config import settings

logger = logging.getLogger("poi-storage")

async def upload_thumbnail(file: UploadFile) -> str:
    """
    Tải file ảnh thumbnail lên Object Storage (Supabase Storage qua REST API hoặc Local media fallback)
    """
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"poi_thumb_{uuid.uuid4().hex[:8]}.{ext}"
    content_type = file.content_type or f"image/{ext if ext != 'jpg' else 'jpeg'}"

    # 1. Đọc nội dung file
    file.file.seek(0)
    content = await file.read()

    # 2. Upload lên Supabase Storage qua REST API (không phụ thuộc SDK supabase)
    supabase_url = (settings.SUPABASE_URL or "").strip().rstrip("/")
    supabase_key = (settings.SUPABASE_SERVICE_KEY or "").strip()
    bucket = getattr(settings, "SUPABASE_BUCKET_NAME", "public-media")

    if supabase_url and "supabase.co" in supabase_url and supabase_key and "your-" not in supabase_key:
        try:
            path_in_bucket = f"thumbnails/{unique_filename}"
            upload_endpoint = f"{supabase_url}/storage/v1/object/{bucket}/{path_in_bucket}"
            headers = {
                "Authorization": f"Bearer {supabase_key}",
                "apikey": supabase_key,
                "Content-Type": content_type,
                "x-upsert": "true"
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(upload_endpoint, content=content, headers=headers)
                if resp.status_code in (200, 201):
                    public_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{path_in_bucket}"
                    logger.info(f"Đã upload ảnh thành công lên Supabase Storage: {public_url}")
                    return public_url
                else:
                    logger.warning(f"Lỗi HTTP từ Supabase Storage ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.warning(f"Không thể upload lên Supabase Storage qua REST ({e}). Sử dụng local fallback...")

    # 3. Fallback lưu trữ cục bộ khi chưa cấu hình Supabase hoặc lỗi mạng
    upload_dir = Path("./data/uploads/thumbnails")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / unique_filename

    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"Lưu ảnh cục bộ tại: {file_path}")
    return f"/media/thumbnails/{unique_filename}"

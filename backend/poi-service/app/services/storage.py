import os
import uuid
import logging
from pathlib import Path
from fastapi import UploadFile
from app.config import settings

logger = logging.getLogger("poi-storage")

async def upload_thumbnail(file: UploadFile) -> str:
    """
    Tải file ảnh thumbnail lên Object Storage (Supabase Storage hoặc Local media)
    """
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"poi_thumb_{uuid.uuid4().hex[:8]}.{ext}"
    
    # Kiểm tra cấu hình Supabase hợp lệ
    if settings.SUPABASE_URL and not "your-project-id" in settings.SUPABASE_URL:
        try:
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            content = await file.read()
            path_in_bucket = f"thumbnails/{unique_filename}"
            
            supabase.storage.from_(settings.SUPABASE_BUCKET_NAME).upload(
                path=path_in_bucket,
                file=content,
                file_options={"content-type": file.content_type or "image/jpeg"}
            )
            public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET_NAME}/{path_in_bucket}"
            logger.info(f"Đã upload ảnh lên Supabase Storage: {public_url}")
            return public_url
        except Exception as e:
            logger.warning(f"Không thể upload lên Supabase ({e}). Sử dụng local fallback...")

    # Fallback lưu trữ cục bộ khi chưa cấu hình Supabase
    upload_dir = Path("./data/uploads/thumbnails")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / unique_filename
    
    file.file.seek(0)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
        
    return f"/media/thumbnails/{unique_filename}"

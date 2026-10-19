# Data Pipeline Service - Dịch thuật đa ngôn ngữ (15+ ngôn ngữ), TTS và cập nhật Vector DB (UC04)
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import time
import sqlite3
import httpx
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from shared.config import (
    DATA_DIR, SUPPORTED_LANGUAGES, POI_SERVICE_URL, CHATBOT_SERVICE_URL
)
from shared.adapters import shared_queue, AIAdapter, shared_vector_store

app = FastAPI(
    title="Data Pipeline Service",
    description="Consumer xử lý ngầm: dịch 15 ngôn ngữ, sinh audio, cập nhật POILocalizations và Vector DB (UC04)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def update_poi_status_and_localizations(poi_id: str, status_str: str, localizations: List[dict]):
    """Cập nhật tiến độ và danh sách bản dịch trực tiếp vào database của POI Service"""
    poi_db_path = DATA_DIR / "poi.db"
    try:
        with sqlite3.connect(poi_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE POIs SET pipeline_status = ? WHERE poi_id = ?", (status_str, poi_id))
            for loc in localizations:
                loc_id = f"loc_{poi_id}_{loc['language_code']}"
                cursor.execute("""
                    INSERT OR REPLACE INTO POILocalizations 
                    (localization_id, poi_id, language_code, translated_title, translated_description, audio_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    loc_id, poi_id, loc["language_code"],
                    loc["translated_title"], loc["translated_description"], loc.get("audio_url", "")
                ))
            conn.commit()
    except Exception as e:
        # UC04 E2: Lỗi ghi dữ liệu vào POI DB -> ghi nhận cảnh báo lên Monitoring
        shared_queue.log_error(f"Lỗi ghi POI DB cho {poi_id}: {str(e)}", {"poi_id": poi_id})

def process_poi_event(event_data: dict):
    """
    UC04 bước 4-7: Xử lý message 'poi.upserted' nhận từ Message Queue
    - Dịch sang 15 ngôn ngữ
    - Sinh Audio TTS
    - Cập nhật tiến độ từng bước
    - Đồng bộ sang Vector DB cho Chatbot RAG
    """
    poi_id = event_data.get("poi_id")
    name = event_data.get("name", "")
    original_description = event_data.get("original_description", "")
    languages = event_data.get("languages", SUPPORTED_LANGUAGES)

    total_langs = len(languages)
    completed_locs = []

    try:
        for idx, lang in enumerate(languages, 1):
            # Cập nhật tiến độ theo thời gian thực (vd: "Đang xử lý (3/15)", "Đang xử lý (7/15)")
            status_text = f"Đang xử lý ({idx}/{total_langs})"
            
            # UC04 bước 5: Dịch mô tả sang ngôn ngữ mục tiêu
            translated_desc = AIAdapter.translate(original_description, lang)
            translated_title = f"[{lang}] {name}" if lang != "vi" else name

            # Sinh audio TTS
            audio_url = AIAdapter.synthesize_speech(translated_desc, lang)

            completed_locs.append({
                "language_code": lang,
                "translated_title": translated_title,
                "translated_description": translated_desc,
                "audio_url": audio_url
            })

            # Cập nhật tiến độ sau mỗi ngôn ngữ
            update_poi_status_and_localizations(poi_id, status_text, completed_locs)
            
            # Nghỉ nhẹ 50ms để tạo hiệu ứng chuyển động tiến độ thực tế khi demo
            time.sleep(0.05)

        # Hoàn tất tiến trình dịch
        final_status = "Hoàn tất (15/15)"
        update_poi_status_and_localizations(poi_id, final_status, completed_locs)

        # UC04 bước 7: Cập nhật vector embeddings vào Vector DB cho Chatbot RAG
        chunk_text = f"{name}. {original_description}"
        vec = AIAdapter.get_embedding(chunk_text)
        shared_vector_store.add_vector(
            vector_id=f"vec_{poi_id}",
            poi_id=poi_id,
            chunk_text=chunk_text,
            embedding=vec,
            metadata={"name": name, "category": "poi_updated"}
        )

    except Exception as e:
        # UC04 E1: Lỗi API -> Ném lỗi để Message Queue thực hiện Retry hoặc đưa vào Dead-Letter Queue
        update_poi_status_and_localizations(poi_id, "Lỗi xử lý", completed_locs)
        raise e

# Đăng ký consumer lắng nghe Message Queue
shared_queue.subscribe(process_poi_event)


# --- Endpoints ---

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "data-pipeline-service"}


@app.get("/monitoring", tags=["Monitoring"])
async def get_monitoring_dashboard():
    """UC04 E2: Monitoring Dashboard hiển thị cảnh báo lỗi và số message trong Dead-Letter Queue"""
    data = shared_queue.get_monitoring_data()
    return {
        "status": "healthy",
        "dlq_count": data["dlq_count"],
        "dlq_messages": data["dlq_messages"],
        "recent_errors": data["error_logs"]
    }

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
import threading
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

from shared.pipeline_worker import run_poi_pipeline, update_poi_status_and_localizations

# Đăng ký consumer lắng nghe Message Queue
shared_queue.subscribe(run_poi_pipeline)


# --- Endpoints ---

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "data-pipeline-service"}


@app.post("/pipeline/process-poi", tags=["Pipeline Processing"])
async def trigger_process_poi(payload: dict):
    """UC04: Tiếp nhận event 'poi.upserted' từ poi-service (multi-process) và xử lý bất đồng bộ"""
    thread = threading.Thread(target=run_poi_pipeline, args=(payload,), daemon=True)
    thread.start()
    return {"status": "accepted", "message": "Tiến trình dịch thuật đang chạy ngầm"}


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

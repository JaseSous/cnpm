# POI Service - Navigation & POI Service (UC02, UC04)
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import time
import uuid
import sqlite3
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from shared.config import DATA_DIR, SUPPORTED_LANGUAGES
from shared.seed_data import INITIAL_POIS, INITIAL_ROUTES
from shared.adapters import shared_queue, AIAdapter

app = FastAPI(
    title="Navigation & POI Service",
    description="Quản lý POIs, Tour Routes và xuất toàn bộ dữ liệu 1 lần duy nhất cho Client (UC02, UC04)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = DATA_DIR / "poi.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Khởi tạo các bảng theo đúng ERD trong PRD: POIs, POILocalizations, TourRoutes, RoutePOIs"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS POIs (
                poi_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                trigger_radius INTEGER NOT NULL,
                thumbnail_url TEXT,
                original_description TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pipeline_status TEXT DEFAULT 'done'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS POILocalizations (
                localization_id TEXT PRIMARY KEY,
                poi_id TEXT NOT NULL,
                language_code TEXT NOT NULL,
                translated_title TEXT NOT NULL,
                translated_description TEXT NOT NULL,
                audio_url TEXT,
                FOREIGN KEY (poi_id) REFERENCES POIs(poi_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TourRoutes (
                route_id TEXT PRIMARY KEY,
                route_name TEXT NOT NULL,
                description TEXT,
                estimated_duration INTEGER NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RoutePOIs (
                route_id TEXT NOT NULL,
                poi_id TEXT NOT NULL,
                step_order INTEGER NOT NULL,
                PRIMARY KEY (route_id, poi_id),
                FOREIGN KEY (route_id) REFERENCES TourRoutes(route_id),
                FOREIGN KEY (poi_id) REFERENCES POIs(poi_id)
            )
        """)
        conn.commit()

        # Seed 6 POIs và các ngôn ngữ nếu DB trống
        cursor.execute("SELECT COUNT(*) as cnt FROM POIs")
        if cursor.fetchone()["cnt"] == 0:
            for p in INITIAL_POIS:
                cursor.execute("""
                    INSERT INTO POIs (poi_id, name, latitude, longitude, trigger_radius, thumbnail_url, original_description, pipeline_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (p["poi_id"], p["name"], p["latitude"], p["longitude"], p["trigger_radius"], p["thumbnail_url"], p["original_description"], "done"))

                # Seed 15 ngôn ngữ cho mỗi POI
                for lang in SUPPORTED_LANGUAGES:
                    loc_id = f"loc_{p['poi_id']}_{lang}"
                    trans_desc = AIAdapter.translate(p["original_description"], lang)
                    cursor.execute("""
                        INSERT INTO POILocalizations (localization_id, poi_id, language_code, translated_title, translated_description, audio_url)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (loc_id, p["poi_id"], lang, f"[{lang}] {p['name']}" if lang != "vi" else p["name"], trans_desc, ""))

            # Seed TourRoute
            for r in INITIAL_ROUTES:
                cursor.execute("""
                    INSERT INTO TourRoutes (route_id, route_name, description, estimated_duration)
                    VALUES (?, ?, ?, ?)
                """, (r["route_id"], r["route_name"], r["description"], 45))
                for step, poi_id in enumerate(r["poi_ids"], 1):
                    cursor.execute("""
                        INSERT INTO RoutePOIs (route_id, poi_id, step_order)
                        VALUES (?, ?, ?)
                    """, (r["route_id"], poi_id, step))
            conn.commit()

init_db()

# --- Pydantic Schemas ---
class POICreateRequest(BaseModel):
    name: str
    latitude: float
    longitude: float
    trigger_radius: int = 30
    thumbnail_url: Optional[str] = None
    original_description: str

class POIUpdateRequest(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    trigger_radius: Optional[int] = None
    thumbnail_url: Optional[str] = None
    original_description: Optional[str] = None

class LocalizationItem(BaseModel):
    language_code: str
    translated_title: str
    translated_description: str
    audio_url: Optional[str] = ""

class InternalLocalizationUpdateRequest(BaseModel):
    poi_id: str
    pipeline_status: str
    localizations: List[LocalizationItem]


# --- Endpoints ---

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "poi-service"}


@app.get("/pois/all", tags=["UC02 - Fetch POIs"])
async def get_all_pois():
    """
    UC02: Tải MỘT LẦN toàn bộ POIs (tọa độ, bán kính, thumbnail, mô tả gốc),
    tuyến tham quan gợi ý, và toàn bộ localizations 15+ ngôn ngữ.
    - E1: Lỗi kết nối DB -> 500 'Không thể tải dữ liệu bản đồ, vui lòng thử lại'
    - E2: Dữ liệu DB trống -> trả [] kèm message 'Dữ liệu điểm tham quan đang được cập nhật'
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM POIs ORDER BY poi_id")
            poi_rows = [dict(r) for r in cursor.fetchall()]

            # UC02 E2: Dữ liệu POI trong Database đang trống
            if not poi_rows:
                return {
                    "pois": [],
                    "tour_routes": [],
                    "message": "Dữ liệu điểm tham quan đang được cập nhật"
                }

            # Lấy toàn bộ localizations
            cursor.execute("SELECT * FROM POILocalizations")
            loc_rows = [dict(r) for r in cursor.fetchall()]

            # Nhóm localizations theo poi_id
            loc_map = {}
            for loc in loc_rows:
                pid = loc["poi_id"]
                if pid not in loc_map:
                    loc_map[pid] = {}
                loc_map[pid][loc["language_code"]] = {
                    "title": loc["translated_title"],
                    "description": loc["translated_description"],
                    "audio_url": loc["audio_url"] or ""
                }

            # Ghép localizations vào từng POI
            pois_result = []
            for p in poi_rows:
                pid = p["poi_id"]
                p_copy = dict(p)
                p_copy["localizations"] = loc_map.get(pid, {})
                pois_result.append(p_copy)

            # Lấy toàn bộ TourRoutes kèm các POI trong tuyến
            cursor.execute("SELECT * FROM TourRoutes")
            routes = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT route_id, poi_id, step_order FROM RoutePOIs ORDER BY route_id, step_order")
            route_poi_rows = [dict(r) for r in cursor.fetchall()]
            
            route_poi_map = {}
            for rp in route_poi_rows:
                rid = rp["route_id"]
                if rid not in route_poi_map:
                    route_poi_map[rid] = []
                route_poi_map[rid].append(rp["poi_id"])

            for r in routes:
                r["poi_ids"] = route_poi_map.get(r["route_id"], [])

            return {
                "pois": pois_result,
                "tour_routes": routes,
                "total_pois": len(pois_result),
                "message": "Tải toàn bộ dữ liệu POI thành công"
            }
    except Exception as e:
        # UC02 E1: Mất kết nối giữa Navigation & POI Service và POI DB
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tải dữ liệu bản đồ, vui lòng thử lại"
        )


@app.get("/pois", tags=["POIs CRUD"])
async def list_pois():
    """Lấy danh sách POI phục vụ Admin Dashboard"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM POIs ORDER BY updated_at DESC")
        return [dict(r) for r in cursor.fetchall()]


@app.get("/pois/{poi_id}", tags=["POIs CRUD"])
async def get_poi(poi_id: str):
    """Lấy chi tiết 1 POI kèm localizations"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM POIs WHERE poi_id = ?", (poi_id,))
        poi = cursor.fetchone()
        if not poi:
            raise HTTPException(status_code=404, detail="Không tìm thấy điểm tham quan")

        cursor.execute("SELECT * FROM POILocalizations WHERE poi_id = ?", (poi_id,))
        localizations = [dict(r) for r in cursor.fetchall()]

        res = dict(poi)
        res["localizations"] = localizations
        return res


@app.post("/pois", tags=["UC04 - Admin POI"])
async def create_poi(payload: POICreateRequest):
    """
    UC04: Admin thêm POI mới
    - Lưu vào POI DB với trạng thái ban đầu 'Đang xử lý (0/15)'
    - Trả phản hồi thành công NGAY LẬP TỨC cho Admin
    - Đồng thời Publish event 'poi.upserted' vào Message Queue để dịch 15 ngôn ngữ ngầm
    """
    poi_id = f"poi_{int(time.time() * 1000)}"
    initial_status = "Đang xử lý (0/15)"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO POIs (poi_id, name, latitude, longitude, trigger_radius, thumbnail_url, original_description, pipeline_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            poi_id, payload.name, payload.latitude, payload.longitude,
            payload.trigger_radius, payload.thumbnail_url or "", payload.original_description, initial_status
        ))
        
        # Thêm bản dịch tiếng Việt cơ bản ngay lập tức
        cursor.execute("""
            INSERT INTO POILocalizations (localization_id, poi_id, language_code, translated_title, translated_description, audio_url)
            VALUES (?, ?, 'vi', ?, ?, '')
        """, (f"loc_{poi_id}_vi", poi_id, payload.name, payload.original_description))
        conn.commit()

    # UC04 bước 3: Publish event lên Message Queue
    event_data = {
        "event_type": "poi.upserted",
        "poi_id": poi_id,
        "name": payload.name,
        "original_description": payload.original_description,
        "languages": SUPPORTED_LANGUAGES
    }
    shared_queue.publish("poi.exchange", "poi.upserted", event_data)

    return {
        "poi_id": poi_id,
        "name": payload.name,
        "status": "success",
        "pipeline_status": initial_status,
        "message": "Đã lưu điểm tham quan, tiến trình dịch thuật và tổng hợp âm thanh đang chạy ngầm"
    }


@app.put("/pois/{poi_id}", tags=["UC04 - Admin POI"])
async def update_poi(poi_id: str, payload: POIUpdateRequest):
    """
    UC04 & A1: Admin sửa POI
    - UC04 A1: Nếu CHỈ sửa tọa độ/bán kính (mô tả gốc không đổi) -> KHÔNG publish event lên Message Queue!
    - Nếu thay đổi mô tả gốc -> publish event 'poi.upserted' để dịch lại 15 ngôn ngữ ngầm
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM POIs WHERE poi_id = ?", (poi_id,))
        old_poi = cursor.fetchone()
        if not old_poi:
            raise HTTPException(status_code=404, detail="Không tìm thấy điểm tham quan")

        old_poi = dict(old_poi)

        name = payload.name if payload.name is not None else old_poi["name"]
        lat = payload.latitude if payload.latitude is not None else old_poi["latitude"]
        lng = payload.longitude if payload.longitude is not None else old_poi["longitude"]
        radius = payload.trigger_radius if payload.trigger_radius is not None else old_poi["trigger_radius"]
        thumb = payload.thumbnail_url if payload.thumbnail_url is not None else old_poi["thumbnail_url"]
        desc = payload.original_description if payload.original_description is not None else old_poi["original_description"]

        # Kiểm tra xem mô tả gốc có thay đổi không
        description_changed = (desc != old_poi["original_description"])

        new_status = old_poi["pipeline_status"]
        if description_changed:
            new_status = "Đang xử lý (0/15)"

        cursor.execute("""
            UPDATE POIs 
            SET name = ?, latitude = ?, longitude = ?, trigger_radius = ?, thumbnail_url = ?, original_description = ?, pipeline_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE poi_id = ?
        """, (name, lat, lng, radius, thumb, desc, new_status, poi_id))
        conn.commit()

    if description_changed:
        # UC04 bước 3: Publish event dịch thuật khi đổi mô tả
        event_data = {
            "event_type": "poi.upserted",
            "poi_id": poi_id,
            "name": name,
            "original_description": desc,
            "languages": SUPPORTED_LANGUAGES
        }
        shared_queue.publish("poi.exchange", "poi.upserted", event_data)
        msg = "Cập nhật POI thành công. Tiến trình dịch thuật tự động đã được kích hoạt"
    else:
        # UC04 A1: Chỉ sửa tọa độ/bán kính -> BỎ QUA dịch thuật, không publish event
        msg = "Cập nhật tọa độ/bán kính thành công (bỏ qua dịch thuật vì mô tả không đổi)"

    return {
        "poi_id": poi_id,
        "description_changed": description_changed,
        "pipeline_status": new_status,
        "message": msg
    }


@app.delete("/pois/{poi_id}", tags=["POIs CRUD"])
async def delete_poi(poi_id: str):
    """Admin xóa POI"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM POILocalizations WHERE poi_id = ?", (poi_id,))
        cursor.execute("DELETE FROM RoutePOIs WHERE poi_id = ?", (poi_id,))
        cursor.execute("DELETE FROM POIs WHERE poi_id = ?", (poi_id,))
        conn.commit()
    return {"message": "Đã xóa điểm tham quan"}


@app.get("/pois/{poi_id}/pipeline-status", tags=["UC04 - Pipeline Status"])
async def get_poi_pipeline_status(poi_id: str):
    """Admin Dashboard polling mỗi 2 giây để theo dõi tiến độ dịch thuật"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT poi_id, name, pipeline_status, updated_at FROM POIs WHERE poi_id = ?", (poi_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Không tìm thấy POI")
        return dict(row)


@app.post("/pois/internal/update-localizations", tags=["Internal Pipeline"])
async def internal_update_localizations(payload: InternalLocalizationUpdateRequest):
    """Endpoint nội bộ cho data-pipeline-service cập nhật bản dịch vào POI DB"""
    with get_db() as conn:
        cursor = conn.cursor()
        for loc in payload.localizations:
            loc_id = f"loc_{payload.poi_id}_{loc.language_code}"
            cursor.execute("""
                INSERT OR REPLACE INTO POILocalizations (localization_id, poi_id, language_code, translated_title, translated_description, audio_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (loc_id, payload.poi_id, loc.language_code, loc.translated_title, loc.translated_description, loc.audio_url or ""))

        cursor.execute(
            "UPDATE POIs SET pipeline_status = ? WHERE poi_id = ?",
            (payload.pipeline_status, payload.poi_id)
        )
        conn.commit()
    return {"success": True}

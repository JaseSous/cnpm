# Worker xử lý Pipeline Dịch thuật, TTS và RAG Vector (UC04)
import time
import sqlite3
import logging
from typing import List
from shared.config import DATA_DIR, SUPPORTED_LANGUAGES
from shared.adapters import AIAdapter, shared_vector_store, shared_queue

logger = logging.getLogger("pipeline_worker")

def update_poi_status_and_localizations(poi_id: str, status_str: str, localizations: List[dict]):
    """Cập nhật tiến độ và danh sách bản dịch trực tiếp vào database với retry chống database locked"""
    poi_db_path = DATA_DIR / "poi.db"
    for attempt in range(5):
        try:
            with sqlite3.connect(poi_db_path, timeout=30.0) as conn:
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
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < 4:
                time.sleep(0.2 * (attempt + 1))
                continue
            shared_queue.log_error(f"Lỗi SQLite ghi POI DB cho {poi_id}: {str(e)}", {"poi_id": poi_id})
        except Exception as e:
            shared_queue.log_error(f"Lỗi ghi POI DB cho {poi_id}: {str(e)}", {"poi_id": poi_id})
            break


def run_poi_pipeline(event_data: dict):
    """
    Hàm thực thi pipeline dịch thuật và sinh vector:
    - Chạy được cả trên Data Pipeline Service lẫn Fallback Worker của POI Service
    - Dịch chuẩn 15 ngôn ngữ
    - Đảm bảo không bao giờ bị kẹt ở trạng thái dở dang
    """
    poi_id = event_data.get("poi_id")
    name = event_data.get("name", "")
    original_description = event_data.get("original_description", "")
    languages = event_data.get("languages") or SUPPORTED_LANGUAGES

    if not poi_id or not original_description:
        return

    total_langs = len(languages)
    completed_locs = []

    try:
        for idx, lang in enumerate(languages, 1):
            status_text = f"Đang xử lý ({idx}/{total_langs})"
            
            # Dịch mô tả và tên
            translated_desc = AIAdapter.translate(original_description, lang)
            translated_title = AIAdapter.translate(name, lang) if lang != "vi" else name
            audio_url = AIAdapter.synthesize_speech(translated_desc, lang)

            completed_locs.append({
                "language_code": lang,
                "translated_title": translated_title,
                "translated_description": translated_desc,
                "audio_url": audio_url
            })

            # Cập nhật tiến độ sau mỗi ngôn ngữ
            update_poi_status_and_localizations(poi_id, status_text, completed_locs)
            time.sleep(0.04)

        # Hoàn tất 100%
        final_status = "Hoàn tất (15/15)"
        update_poi_status_and_localizations(poi_id, final_status, completed_locs)

        # Cập nhật Vector DB cho Chatbot RAG
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
        err_msg = f"Lỗi pipeline cho POI {poi_id}: {str(e)}"
        shared_queue.log_error(err_msg, {"poi_id": poi_id})
        update_poi_status_and_localizations(poi_id, "Lỗi xử lý", completed_locs)
        raise e

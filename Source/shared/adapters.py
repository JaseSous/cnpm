# Các lớp Adapter trừu tượng (Interface) cho Cache, Queue, VectorStore và AI
import time
import json
import math
import threading
import sqlite3
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from shared.config import (
    DATA_DIR, TRANSLATION_MODE, TTS_MODE, LLM_MODE, EMBEDDING_MODE, GEMINI_API_KEY
)

# ===============================================================
# 1. CACHE ADAPTER (Redis / In-Memory TTL & Single-Use)
# ===============================================================

class MemoryCacheAdapter:
    """Lớp cache in-memory giả lập Redis với TTL và cơ chế dùng 1 lần (ShortCodeCache, FAQCache)"""
    def __init__(self):
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        with self._lock:
            expire_at = time.time() + ttl_seconds
            self._store[key] = (value, expire_at)

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._store:
                return None
            val, expire_at = self._store[key]
            if time.time() > expire_at:
                del self._store[key]
                return None
            return val

    def pop_once(self, key: str) -> Optional[Any]:
        """UC01: Tiền mặt tra shorted_code ở Redis, có TTL, dùng 1 lần rồi xóa"""
        with self._lock:
            if key not in self._store:
                return None
            val, expire_at = self._store[key]
            del self._store[key] # Xóa ngay lập tức
            if time.time() > expire_at:
                return None # Đã hết hạn
            return val

    def delete(self, key: str):
        with self._lock:
            self._store.pop(key, None)

# Global cache instance dùng chung cho các service chạy cùng máy local
shared_cache = MemoryCacheAdapter()


# ===============================================================
# 2. MESSAGE QUEUE ADAPTER (RabbitMQ / Local Queue với Retry & DLQ)
# ===============================================================

class LocalEventQueue:
    """Lớp hàng đợi Message Queue nội bộ hỗ trợ Publish/Subscribe, Retry và Dead-Letter Queue"""
    def __init__(self):
        self._queue = []
        self._dead_letter_queue = []
        self._error_logs = []
        self._subscribers = []
        self._lock = threading.Lock()

    def publish(self, exchange: str, routing_key: str, message: dict):
        """UC04: Publish event New/Updated POI lên Message Queue"""
        payload = {
            "exchange": exchange,
            "routing_key": routing_key,
            "message": message,
            "retries": 0,
            "timestamp": time.time()
        }
        with self._lock:
            self._queue.append(payload)
        # Kích hoạt worker xử lý
        self._dispatch()

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def _dispatch(self):
        def worker():
            with self._lock:
                if not self._queue:
                    return
                item = self._queue.pop(0)

            # 1. Nếu có subscriber cục bộ trong cùng process (ví dụ trong unit tests)
            if self._subscribers:
                for sub in self._subscribers:
                    try:
                        sub(item["message"])
                    except Exception as e:
                        item["retries"] += 1
                        err_msg = f"Lỗi xử lý event: {str(e)}"
                        self.log_error(err_msg, item["message"])
                        if item["retries"] < 3:
                            with self._lock:
                                self._queue.append(item)
                        else:
                            with self._lock:
                                self._dead_letter_queue.append(item)
            else:
                # 2. Nếu không có subscriber trong process này (khi poi-service chạy độc lập đa tiến trình)
                # Ưu tiên gửi sự kiện sang data-pipeline-service qua HTTP
                dispatched = False
                try:
                    import httpx
                    from shared.config import DATA_PIPELINE_SERVICE_URL
                    url = f"{DATA_PIPELINE_SERVICE_URL}/pipeline/process-poi"
                    resp = httpx.post(url, json=item["message"], timeout=4.0)
                    if resp.status_code in (200, 202):
                        dispatched = True
                    else:
                        raise Exception(f"HTTP {resp.status_code}: {resp.text}")
                except Exception as e:
                    self.log_error(f"Data Pipeline Service không phản hồi ({str(e)}). Tự động kích hoạt luồng fallback xử lý tại chỗ...", item["message"])

                # 3. Resilient Fallback: Tự động chạy worker xử lý ngầm cục bộ nếu remote service lỗi
                if not dispatched:
                    try:
                        from shared.pipeline_worker import run_poi_pipeline
                        run_poi_pipeline(item["message"])
                    except Exception as fallback_err:
                        item["retries"] += 1
                        self.log_error(f"Lỗi xử lý fallback: {str(fallback_err)}", item["message"])
                        if item["retries"] < 3:
                            with self._lock:
                                self._queue.append(item)
                        else:
                            with self._lock:
                                self._dead_letter_queue.append(item)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def log_error(self, message: str, context: dict = None):
        with self._lock:
            self._error_logs.append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": message,
                "context": context or {}
            })

    def get_monitoring_data(self) -> dict:
        """UC04 E2: Dữ liệu hiển thị lên Monitoring Dashboard"""
        with self._lock:
            return {
                "dlq_count": len(self._dead_letter_queue),
                "dlq_messages": list(self._dead_letter_queue),
                "error_logs": list(self._error_logs[-20:])
            }

shared_queue = LocalEventQueue()


# ===============================================================
# 3. VECTOR STORE ADAPTER (Qdrant / Local SQLite Cosine Similarity)
# ===============================================================

class LocalVectorStore:
    """Vector DB lưu trữ tri thức Chùa Linh Ứng và tính Cosine Similarity (UC03)"""
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or (DATA_DIR / "chatbot_vectors.db")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS KnowledgeVectors (
                    vector_id TEXT PRIMARY KEY,
                    poi_id TEXT,
                    chunk_text TEXT,
                    embedding_vector TEXT,
                    metadata_json TEXT
                )
            """)

    def add_vector(self, vector_id: str, poi_id: str, chunk_text: str, embedding: List[float], metadata: dict = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO KnowledgeVectors (vector_id, poi_id, chunk_text, embedding_vector, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            """, (vector_id, poi_id, chunk_text, json.dumps(embedding), json.dumps(metadata or {})))

    def search_top_k(self, query_vector: List[float], top_k: int = 3, threshold: float = 0.35) -> List[dict]:
        """UC03 bước 5: Tìm kiếm top-k và lọc theo ngưỡng tương đồng threshold"""
        results = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT vector_id, poi_id, chunk_text, embedding_vector, metadata_json FROM KnowledgeVectors")
            rows = cursor.fetchall()

        for vid, poi_id, text, vec_str, meta_str in rows:
            vec = json.loads(vec_str)
            sim = self._cosine_similarity(query_vector, vec)
            if sim >= threshold:
                results.append({
                    "vector_id": vid,
                    "poi_id": poi_id,
                    "chunk_text": text,
                    "similarity": sim,
                    "metadata": json.loads(meta_str)
                })

        # Sắp xếp giảm dần theo similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

shared_vector_store = LocalVectorStore()


# ===============================================================
# 4. AI & EMBEDDING ADAPTER (Mock / Gemini)
# ===============================================================

import re

def create_deterministic_embedding(text: str, dim: int = 256) -> List[float]:
    """Tạo vector embedding bằng Random Projection có dấu (signed hashing) để câu hỏi ngoài lề có độ tương đồng gần 0"""
    clean_text = text.lower().strip()
    words = [w for w in re.findall(r'\w+', clean_text) if len(w) > 1]
    if not words:
        return [0.0] * dim

    vec = [0.0] * dim
    for word in words:
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 8) & 1) else -1.0
        vec[idx] += sign * (1.0 + (len(word) * 0.1))

    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec

class AIAdapter:
    """Adapter xử lý Dịch thuật, TTS, Embedding và LLM RAG theo chế độ Mock hoặc Real (Gemini)"""

    @staticmethod
    def translate(text: str, target_lang: str) -> str:
        """UC04 bước 5: Dịch sang 15 ngôn ngữ (Google Translate / Gemini / Fallback)"""
        if not text or not text.strip() or target_lang == "vi":
            return text

        # Map target_lang sang chuẩn mã Google Translate
        gt_lang_map = {
            "zh": "zh-CN",
        }
        tl = gt_lang_map.get(target_lang, target_lang)

        # 1. Google Translate (GTX) - Tự động dịch miễn phí, tốc độ cao, hỗ trợ 100% 15 ngôn ngữ
        try:
            import httpx
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "vi",
                "tl": tl,
                "dt": "t",
                "q": text
            }
            resp = httpx.get(url, params=params, timeout=6.0)
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    translated_parts = [segment[0] for segment in data[0] if segment and len(segment) > 0 and segment[0]]
                    if translated_parts:
                        return "".join(translated_parts).strip()
        except Exception:
            pass

        # 2. Gemini Generative AI (nếu được cấu hình)
        if TRANSLATION_MODE == "gemini" and GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"Translate the following Vietnamese text into language code '{target_lang}'. Output ONLY the translated text:\n\n{text}"
                resp = model.generate_content(prompt)
                if resp.text:
                    return resp.text.strip()
            except Exception:
                pass

        # 3. Fallback an toàn nếu mất mạng
        return f"[{target_lang}] {text}"

    @staticmethod
    def synthesize_speech(text: str, lang: str) -> str:
        """UC04: Sinh file âm thanh TTS (Mock = để trống audio_url để client dùng Web Speech API)"""
        if TTS_MODE == "gtts":
            try:
                # Nếu có gtts và muốn tạo file thật
                return f"/audio/{lang}_audio.mp3"
            except Exception:
                pass
        # Mặc định Mock: audio_url = "" (Client sẽ dùng SpeechSynthesis Web API)
        return ""

    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """UC03 bước 4: Tạo embedding câu hỏi (Mock = deterministic embedding)"""
        if EMBEDDING_MODE == "gemini" and GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                res = genai.embed_content(model="models/embedding-001", content=text)
                return res["embedding"]
            except Exception:
                pass
        return create_deterministic_embedding(text)

    @staticmethod
    def generate_rag_answer(question: str, context: str) -> str:
        """UC03 bước 6: Ghép prompt và sinh câu trả lời RAG"""
        if LLM_MODE == "gemini" and GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                system_instruction = (
                    "Bạn là trợ lý ảo chính thức của Chùa Linh Ứng Bãi Bụt (Đà Nẵng). "
                    "CHỈ trả lời dựa trên ngữ cảnh được cung cấp dưới đây. "
                    "Nếu không có trong ngữ cảnh, hãy từ chối lịch sự. Giọng điệu tôn kính, thanh tịnh.\n\n"
                    f"NGỮ CẢNH:\n{context}\n\n"
                    f"CÂU HỎI:\n{question}"
                )
                resp = model.generate_content(system_instruction)
                return resp.text.strip()
            except Exception:
                pass

        # Mặc định Mock mode: Trả lời thông minh bám sát ngữ cảnh chùa Linh Ứng
        return f"Dựa trên thông tin khu di tích Chùa Linh Ứng: {context}"

# Chatbot Service - Trợ lý ảo RAG hỏi đáp tri thức Chùa Linh Ứng (UC03)
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import hashlib
import time
from typing import Optional, List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from shared.config import DATA_DIR
from shared.seed_data import INITIAL_POIS
from shared.adapters import shared_cache, shared_vector_store, AIAdapter

app = FastAPI(
    title="Chatbot AI Service (RAG)",
    description="Hỏi đáp ngôn ngữ tự nhiên về Chùa Linh Ứng với Redis Cache và Vector DB (UC03)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SIMILARITY_THRESHOLD = 0.35  # Ngưỡng tương đồng tối thiểu

def seed_knowledge_base():
    """Nạp sẵn tri thức ban đầu của 6 POI và thông tin Chùa Linh Ứng vào Vector DB"""
    # 6 POIs
    for poi in INITIAL_POIS:
        text = f"{poi['name']}. {poi['original_description']}"
        vec = AIAdapter.get_embedding(text)
        shared_vector_store.add_vector(
            vector_id=f"vec_{poi['poi_id']}",
            poi_id=poi["poi_id"],
            chunk_text=text,
            embedding=vec,
            metadata={"name": poi["name"], "category": "poi"}
        )

    # Tri thức bổ sung về Chùa Linh Ứng
    extra_chunks = [
        ("chua_linh_ung_tong_quan", "Chùa Linh Ứng Bãi Bụt nằm trên bán đảo Sơn Trà, thành phố Đà Nẵng, được xây dựng từ năm 2004 và khánh thành năm 2010. Đây là ngôi chùa lớn nhất trong 3 ngôi chùa mang tên Linh Ứng tại Đà Nẵng."),
        ("gio_mo_cua_le_phi", "Chùa Linh Ứng mở cửa đón du khách miễn phí tham quan từ 6 giờ sáng đến 21 giờ tối hàng ngày. Du khách khi vào chùa cần mặc trang phục lịch sự, kín đáo."),
        ("lich_su_linh_ung", "Chùa Linh Ứng Bãi Bụt gắn liền với truyền thuyết thời vua Minh Mạng khi một pho tượng Phật trôi dạt vào bãi cát, ngư dân đã lập am thờ phụng và từ đó sóng yên biển lặng.")
    ]
    for cid, text in extra_chunks:
        vec = AIAdapter.get_embedding(text)
        shared_vector_store.add_vector(
            vector_id=f"vec_{cid}",
            poi_id="general",
            chunk_text=text,
            embedding=vec,
            metadata={"name": "Thông tin chung", "category": "general"}
        )

seed_knowledge_base()

# --- Pydantic Schemas ---
class ChatRequest(BaseModel):
    question: str

class SyncKnowledgeRequest(BaseModel):
    poi_id: str
    chunk_text: str
    metadata: Optional[dict] = None


# --- Endpoints UC03 ---

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "chatbot-service"}


@app.post("/chat/ask", tags=["UC03 - Chatbot RAG"])
async def ask_chatbot(payload: ChatRequest):
    """
    UC03: Hỏi đáp qua Chatbot AI (RAG)
    - Bước 1 & A1: Chuẩn hóa câu hỏi + băm SHA256 -> Kiểm tra Redis Cache (from_cache=true nếu trùng)
    - Bước 2: Tạo vector embedding câu hỏi
    - Bước 3 & 4: Tìm kiếm Vector DB top-k. Nếu dưới ngưỡng tương đồng (E2) -> Trả đúng câu từ chối lịch sự
    - Bước 5 & 6: Ghép prompt ngữ cảnh và gọi LLM RAG
    - Bước 7: Lưu vào Redis Cache và trả về cho Client
    - E1: Bắt lỗi / timeout -> Trả thông báo 'Hệ thống trợ lý ảo đang bận, vui lòng thử lại sau giây lát'
    """
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống")

    # UC03 bước 1: Chuẩn hóa câu hỏi
    normalized_q = question.lower().strip(" ?.!,")
    q_hash = hashlib.sha256(normalized_q.encode("utf-8")).hexdigest()
    cache_key = f"faq:{q_hash}"

    # UC03 A1: Kiểm tra trong Redis Cache
    cached_entry = shared_cache.get(cache_key)
    if cached_entry:
        return {
            "question": question,
            "answer": cached_entry["answer"],
            "from_cache": True,
            "sources": cached_entry.get("sources", []),
            "message": "Câu trả lời từ bộ nhớ đệm (Redis Cache)"
        }

    try:
        # UC03 bước 4: Gọi Embedding Model chuyển câu hỏi thành vector
        q_vec = AIAdapter.get_embedding(normalized_q)

        # UC03 bước 5: Truy vấn Vector DB tìm kiếm ngữ cảnh liên quan
        top_matches = shared_vector_store.search_top_k(
            query_vector=q_vec,
            top_k=3,
            threshold=SIMILARITY_THRESHOLD
        )

        # UC03 E2: Câu hỏi nằm ngoài phạm vi dữ liệu kiến thức tại điểm tham quan
        if not top_matches:
            out_of_scope_reply = "Xin lỗi, tôi chỉ có thể giải đáp các thông tin liên quan đến khu di tích Chùa Linh Ứng"
            return {
                "question": question,
                "answer": out_of_scope_reply,
                "from_cache": False,
                "sources": [],
                "in_scope": False
            }

        # UC03 bước 6: Ghép câu hỏi gốc và ngữ cảnh tìm được thành Prompt
        context_text = " ".join([m["chunk_text"] for m in top_matches])
        answer = AIAdapter.generate_rag_answer(question=question, context=context_text)

        sources = [{"poi_id": m["poi_id"], "similarity": round(m["similarity"], 3)} for m in top_matches]

        # UC03 bước 7: Lưu cặp câu hỏi - trả lời mới vào Redis Cache
        cache_data = {
            "question": question,
            "answer": answer,
            "sources": sources,
            "cached_at": time.time()
        }
        shared_cache.set(cache_key, cache_data, ttl_seconds=86400)  # Cache 24 giờ

        return {
            "question": question,
            "answer": answer,
            "from_cache": False,
            "sources": sources,
            "in_scope": True
        }

    except Exception as e:
        # UC03 E1: Dịch vụ AI hoặc Vector DB phản hồi quá thời gian chờ / lỗi kết nối
        return {
            "question": question,
            "answer": "Hệ thống trợ lý ảo đang bận, vui lòng thử lại sau giây lát",
            "from_cache": False,
            "error": True
        }


@app.post("/chat/sync-knowledge", tags=["Knowledge Sync"])
async def sync_knowledge(payload: SyncKnowledgeRequest):
    """UC04 bước 7: Nhận tri thức mới từ Data Pipeline Service cập nhật vào Vector DB"""
    vec = AIAdapter.get_embedding(payload.chunk_text)
    vector_id = f"vec_{payload.poi_id}_{int(time.time())}"
    shared_vector_store.add_vector(
        vector_id=vector_id,
        poi_id=payload.poi_id,
        chunk_text=payload.chunk_text,
        embedding=vec,
        metadata=payload.metadata or {}
    )
    return {"success": True, "vector_id": vector_id}

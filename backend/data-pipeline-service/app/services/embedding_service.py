import logging
import hashlib
import math
import random
from typing import List, Dict, Any, Optional
from app.config import settings
from app.grpc_clients import chatbot_grpc_client, poi_grpc_client

logger = logging.getLogger("embedding-service")

def generate_mock_embedding(text: str, dim: int = 768) -> List[float]:
    """
    Sinh embedding giả định xác định (deterministic) 768 chiều dựa trên hash của text.
    Dùng khi offline hoặc không có API key hợp lệ của Gemini.
    Được chuẩn hóa L2 (norm = 1.0) cho Vector Search / Cosine Similarity.
    """
    # Dùng sha256 sinh seed
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)
    
    vec = [rng.gauss(0.0, 1.0) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [round(x / norm, 6) for x in vec]
    return vec


def chunk_text(text: str, max_chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Phân mảnh văn bản thành các đoạn nhỏ ~500 ký tự với độ gối đầu overlap ~50 ký tự.
    Ưu tiên ngắt tại dấu chấm câu hoặc xuống dòng.
    """
    text = (text or "").strip()
    if not text:
        return []
    
    if len(text) <= max_chunk_size:
        return [text]
    
    # Chia theo đoạn hoặc câu
    paragraphs = text.split("\n\n")
    chunks: List[str] = []
    current_chunk = ""
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
            
        if len(current_chunk) + len(p) + 2 <= max_chunk_size:
            current_chunk = f"{current_chunk}\n\n{p}" if current_chunk else p
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # Nếu bản thân paragraph dài hơn max_chunk_size, chia nhỏ tiếp theo ký tự
            if len(p) > max_chunk_size:
                start = 0
                while start < len(p):
                    end = start + max_chunk_size
                    chunks.append(p[start:end])
                    start = end - overlap
                current_chunk = ""
            else:
                current_chunk = p
                
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks


class EmbeddingService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.EMBEDDING_MODEL
        self._client = None
        
        # Kiểm tra nếu API key có vẻ hợp lệ (không phải dummy default)
        if self.api_key and self.api_key not in ("your-gemini-api-key", "dummy", ""):
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Không thể khởi tạo Google GenAI Client: {e}. Sử dụng mock embedding.")

    async def get_embedding(self, text: str) -> List[float]:
        """Tạo vector embedding cho một đoạn văn bản (768 chiều)"""
        if self._client:
            try:
                response = await self._client.aio.models.embed_content(
                    model=self.model,
                    contents=text
                )
                if hasattr(response, "embedding") and hasattr(response.embedding, "values"):
                    return list(response.embedding.values)
                elif hasattr(response, "embeddings") and len(response.embeddings) > 0:
                    return list(response.embeddings[0].values)
            except Exception as e:
                logger.warning(f"Lỗi khi gọi Gemini embed_content API: {e}. Fallback mock embedding.")
        
        return generate_mock_embedding(text)

    async def generate_poi_chunks(
        self,
        poi_id: int,
        revision: int,
        language_code: str,
        title: str,
        description: str
    ) -> List[Dict[str, Any]]:
        """Tạo danh sách các chunks và embeddings cho một POI theo ngôn ngữ cụ thể"""
        full_text = f"{title}\n\n{description}".strip()
        text_chunks = chunk_text(full_text, max_chunk_size=500, overlap=50)
        
        chunks = []
        for idx, chunk_str in enumerate(text_chunks):
            embedding = await self.get_embedding(chunk_str)
            chunk_dict = {
                "chunk_id": f"poi_{poi_id}_{language_code}_rev{revision}_{idx}",
                "chunk_text": chunk_str,
                "embedding": embedding,
                "metadata": {
                    "poi_id": str(poi_id),
                    "language_code": language_code,
                    "revision": str(revision),
                    "chunk_index": str(idx),
                    "title": title
                }
            }
            chunks.append(chunk_dict)
            
        return chunks

    async def sync_poi_embeddings(
        self,
        poi_id: int,
        revision: int,
        language_code: str,
        title: str,
        description: str
    ) -> bool:
        """Sinh embeddings và đồng bộ sang Chatbot AI Service (Vector DB Qdrant)"""
        logger.info(f"Bắt đầu tạo embeddings cho POI {poi_id} ({language_code}) rev {revision}")
        try:
            chunks = await self.generate_poi_chunks(
                poi_id=poi_id,
                revision=revision,
                language_code=language_code,
                title=title,
                description=description
            )
            
            # Gửi gRPC sang Chatbot Service
            success = await chatbot_grpc_client.upsert_vectors(
                poi_id=poi_id,
                revision=revision,
                language_code=language_code,
                chunks=chunks
            )
            
            # Cập nhật trạng thái về POI Service
            status = "Synced" if success else "Failed"
            await poi_grpc_client.update_vector_status(
                poi_id=poi_id,
                status=status,
                error_message="" if success else "Không thể đồng bộ tới Chatbot Service"
            )
            
            logger.info(f"Đồng bộ vector cho POI {poi_id} ({language_code}): {status}")
            return success
        except Exception as e:
            logger.error(f"Lỗi ngoại lệ khi tạo và đồng bộ embeddings cho POI {poi_id}: {e}")
            await poi_grpc_client.update_vector_status(
                poi_id=poi_id,
                status="Failed",
                error_message=str(e)
            )
            return False

embedding_service = EmbeddingService()

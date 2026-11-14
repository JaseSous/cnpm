import uuid
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from app.config import settings

logger = logging.getLogger("chatbot-qdrant")

class QdrantService:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION
        self.client: Optional[QdrantClient] = None
        self._init_client()

    def _init_client(self):
        """Khởi tạo kết nối tới Qdrant Cloud hoặc Local Qdrant, fallback sang :memory:"""
        if settings.QDRANT_URL and "localhost" not in settings.QDRANT_URL and "xxxxx" not in settings.QDRANT_URL:
            try:
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                    timeout=5
                )
                logger.info(f"Đã kết nối Qdrant Cloud: {settings.QDRANT_URL}")
            except Exception as e:
                logger.warning(f"Không thể kết nối tới Qdrant Cloud ({e}). Fallback :memory:")
                self.client = QdrantClient(":memory:")
        else:
            # Local dev hoặc test
            try:
                # Thử kết nối URL local
                test_client = QdrantClient(url=settings.QDRANT_URL, timeout=1)
                test_client.get_collections()
                self.client = test_client
                logger.info("Kết nối Qdrant Local thành công")
            except Exception:
                logger.info("Sử dụng In-memory Qdrant Client (offline mode)")
                self.client = QdrantClient(":memory:")

    def ensure_collection_exists(self):
        """Đảm bảo Collection poi_embeddings tồn tại với kích thước vector 768 chiều"""
        try:
            if not self.client.collection_exists(self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=768,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Đã tạo Qdrant collection mới: '{self.collection_name}' (dim=768, Cosine)")
            else:
                logger.info(f"Qdrant collection '{self.collection_name}' đã tồn tại sẵn")
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra/tạo collection Qdrant: {e}")

    def upsert_poi_vectors(
        self,
        poi_id: int,
        revision: int,
        language_code: str,
        chunks: List[Dict[str, Any]]
    ) -> int:
        """
        Lưu các vector chunks của POI vào Qdrant:
        - Xóa các vector cũ của POI cùng ngôn ngữ để tránh trùng lặp
        - Chuyển đổi chunks thành PointStruct và upsert
        """
        self.ensure_collection_exists()

        # 1. Xóa vectors cũ của poi_id này
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(key="poi_id", match=MatchValue(value=poi_id)),
                        FieldCondition(key="language_code", match=MatchValue(value=language_code))
                    ]
                )
            )
        except Exception as e:
            logger.warning(f"Lỗi khi xóa vector cũ POI #{poi_id} ({e})")

        if not chunks:
            return 0

        # 2. Tạo points mới
        points: List[PointStruct] = []
        for c in chunks:
            chunk_id = c.get("chunk_id", "")
            chunk_text = c.get("chunk_text", "")
            embedding = c.get("embedding", [])
            metadata = c.get("metadata", {})

            if not embedding or len(embedding) != 768:
                continue

            # Sinh deterministic UUID từ chunk_id
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{poi_id}_{language_code}_{chunk_id}"))

            payload = {
                "chunk_id": chunk_id,
                "chunk_text": chunk_text,
                "poi_id": poi_id,
                "revision": revision,
                "language_code": language_code,
                "title": metadata.get("title", "")
            }
            payload.update(metadata)

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
            )

        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Đã upsert {len(points)} vector chunks cho POI #{poi_id} ({language_code}) vào Qdrant")

        return len(points)

    def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.35,
        language_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm các đoạn văn bản gần nhất với câu hỏi:
        - Cosine similarity >= score_threshold
        - Lọc theo ngôn ngữ nếu được chỉ định
        """
        self.ensure_collection_exists()

        if not query_vector or len(query_vector) != 768:
            return []

        query_filter = None
        if language_code:
            query_filter = Filter(
                must=[FieldCondition(key="language_code", match=MatchValue(value=language_code))]
            )

        try:
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True
            )

            hits = []
            for pt in results.points:
                payload = pt.payload or {}
                hits.append({
                    "score": round(pt.score, 4),
                    "chunk_id": payload.get("chunk_id", ""),
                    "chunk_text": payload.get("chunk_text", ""),
                    "poi_id": payload.get("poi_id"),
                    "language_code": payload.get("language_code", ""),
                    "title": payload.get("title", ""),
                    "revision": payload.get("revision")
                })
            return hits
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm vector trong Qdrant: {e}")
            return []

    def delete_poi_vectors(self, poi_id: int) -> int:
        """Xóa toàn bộ vector chunks của POI khỏi Qdrant"""
        self.ensure_collection_exists()
        try:
            res = self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="poi_id", match=MatchValue(value=poi_id))]
                )
            )
            logger.info(f"Đã xóa toàn bộ vector của POI #{poi_id} khỏi Qdrant")
            return 1
        except Exception as e:
            logger.error(f"Lỗi khi xóa vector của POI #{poi_id}: {e}")
            return 0

qdrant_service = QdrantService()

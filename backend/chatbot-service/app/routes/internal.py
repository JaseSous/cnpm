import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.qdrant_service import qdrant_service
from app.services.redis_service import redis_service

logger = logging.getLogger("chatbot-internal-http")

router = APIRouter(prefix="/api/internal", tags=["Internal Chatbot"])

class VectorChunk(BaseModel):
    chunk_id: str
    chunk_text: str
    embedding: List[float]
    metadata: Dict[str, Any]

class UpsertVectorsPayload(BaseModel):
    poi_id: int
    revision: int
    language_code: str
    chunks: List[VectorChunk]

class DeleteVectorsPayload(BaseModel):
    poi_id: int

class InvalidateFaqPayload(BaseModel):
    pattern: Optional[str] = "faq:*"

@router.post("/upsert-vectors")
async def upsert_vectors(data: UpsertVectorsPayload):
    try:
        chunks_data = [
            {
                "chunk_id": c.chunk_id,
                "chunk_text": c.chunk_text,
                "embedding": c.embedding,
                "metadata": c.metadata
            }
            for c in data.chunks
        ]
        upserted = qdrant_service.upsert_poi_vectors(
            poi_id=data.poi_id,
            revision=data.revision,
            language_code=data.language_code,
            chunks=chunks_data
        )
        return {"success": True, "upserted_count": upserted}
    except Exception as e:
        logger.error(f"Error in upsert_vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete-vectors")
async def delete_vectors(data: DeleteVectorsPayload):
    try:
        deleted = qdrant_service.delete_poi_vectors(poi_id=data.poi_id)
        return {"success": True, "deleted_count": deleted}
    except Exception as e:
        logger.error(f"Error in delete_vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invalidate-faq-cache")
async def invalidate_faq_cache(data: InvalidateFaqPayload):
    try:
        cleared = await redis_service.invalidate_faq_cache(pattern=data.pattern)
        return {"success": True, "cleared_count": cleared}
    except Exception as e:
        logger.error(f"Error in invalidate_faq_cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

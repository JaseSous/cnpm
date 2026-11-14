import math
import random
import hashlib
import logging
from typing import List, Optional
from app.config import settings

logger = logging.getLogger("chatbot-gemini")

def generate_mock_embedding(text: str, dim: int = 768) -> List[float]:
    """
    Sinh vector giả định xác định (deterministic) 768 chiều theo chuẩn L2 norm.
    Đồng bộ thuật toán với data-pipeline-service để câu hỏi và dữ liệu giả lập có độ tương đồng phù hợp khi offline.
    """
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)
    
    vec = [rng.gauss(0.0, 1.0) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [round(x / norm, 6) for x in vec]
    return vec

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.embedding_model = settings.EMBEDDING_MODEL
        self.llm_model = settings.LLM_MODEL
        self._client = None

        if self.api_key and self.api_key not in ("your-gemini-api-key", "dummy", ""):
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"Đã khởi tạo Google GenAI Client (LLM: {self.llm_model})")
            except Exception as e:
                logger.warning(f"Không thể khởi tạo Gemini Client: {e}. Sử dụng fallback.")

    async def get_embedding(self, text: str) -> List[float]:
        """Tạo embedding 768 chiều cho câu hỏi"""
        if self._client:
            try:
                response = await self._client.aio.models.embed_content(
                    model=self.embedding_model,
                    contents=text
                )
                if hasattr(response, "embedding") and hasattr(response.embedding, "values"):
                    return list(response.embedding.values)
                elif hasattr(response, "embeddings") and len(response.embeddings) > 0:
                    return list(response.embeddings[0].values)
            except Exception as e:
                logger.warning(f"Lỗi khi gọi Gemini embed_content API: {e}. Fallback mock embedding.")

        return generate_mock_embedding(text)

    async def generate_response(self, prompt: str, system_instruction: str = "") -> str:
        """Gọi Gemini LLM để sinh câu trả lời RAG"""
        if self._client:
            try:
                from google.genai import types
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3
                )
                response = await self._client.aio.models.generate_content(
                    model=self.llm_model,
                    contents=prompt,
                    config=config
                )
                if response and hasattr(response, "text") and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Lỗi khi gọi Gemini generate_content: {e}. Fallback câu trả lời dự phòng.")

        # Fallback offline
        return ""

gemini_service = GeminiService()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Chùa Linh Ứng - Chatbot AI Service",
    description="Dịch vụ hỏi đáp thông minh RAG kết hợp Google Gemini Flash và Qdrant Vector DB",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "chatbot-service",
        "version": "1.0.0"
    }

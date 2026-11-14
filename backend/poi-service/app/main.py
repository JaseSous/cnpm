from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Chùa Linh Ứng - Navigation & POI Service",
    description="Dịch vụ quản lý điểm tham quan POI, bản dịch đa ngôn ngữ và định vị GPS",
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
        "service": "poi-service",
        "version": "1.0.0"
    }

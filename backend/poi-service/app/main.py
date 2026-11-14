from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes.pois import router as poi_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo bảng database nếu chưa có
    await init_db()
    yield

app = FastAPI(
    title="Chùa Linh Ứng - Navigation & POI Service",
    description="Dịch vụ quản lý điểm tham quan POI, bản dịch đa ngôn ngữ và định vị GPS",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(poi_router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "poi-service",
        "version": "1.0.0"
    }

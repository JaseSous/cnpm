from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes.pois import router as poi_router
from app.routes.languages import router as language_router
from app.routes.internal import router as internal_router
from app.services.outbox_publisher import outbox_publisher
from app.grpc_server import grpc_server_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo bảng database nếu chưa có
    await init_db()
    # Tự động seed dữ liệu mẫu thực tế Chùa Linh Ứng nếu chưa có
    from app.seed_data import seed_real_pois
    await seed_real_pois()
    # Khởi động Outbox Publisher background worker
    outbox_publisher.start()
    # Khởi động gRPC Server nội bộ (chế độ an toàn)
    try:
        await grpc_server_manager.start()
    except Exception as e:
        print(f"Warning: Không thể khởi động gRPC Server nội bộ: {e}")
    yield
    # Dừng gRPC Server và Outbox Publisher
    try:
        await grpc_server_manager.stop()
    except Exception:
        pass
    await outbox_publisher.stop()

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
app.include_router(language_router)
app.include_router(internal_router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "poi-service",
        "version": "1.0.0"
    }

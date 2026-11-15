from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo bảng database nếu chưa có
    await init_db()
    # Tự động seed tài khoản admin/staff và gói vé nếu chưa có
    try:
        from app.seed_data import seed_data
        await seed_data()
    except Exception as e:
        print(f"Warning: Seed auth data error: {e}")
    yield

app = FastAPI(
    title="Chùa Linh Ứng - Authorization Service",
    description="Dịch vụ xác thực tài khoản Staff/Admin và phát hành vé/JWT cho du khách",
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

app.include_router(auth_router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "auth-service",
        "version": "1.0.0"
    }

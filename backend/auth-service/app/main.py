from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Chùa Linh Ứng - Authorization Service",
    description="Dịch vụ xác thực tài khoản Staff/Admin và phát hành vé/JWT cho du khách",
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
        "service": "auth-service",
        "version": "1.0.0"
    }

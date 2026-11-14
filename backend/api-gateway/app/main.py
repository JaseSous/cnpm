from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Chùa Linh Ứng - API Gateway",
    description="API Gateway định tuyến và xác thực trung tâm cho hệ thống Microservices Chùa Linh Ứng",
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
        "service": "api-gateway",
        "version": "1.0.0"
    }

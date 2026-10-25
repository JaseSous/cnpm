# API Gateway - Điểm vào duy nhất, kiểm tra access_token và định tuyến Microservices
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import httpx
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError

from shared.config import (
    AUTH_SERVICE_URL, POI_SERVICE_URL, CHATBOT_SERVICE_URL, DATA_PIPELINE_SERVICE_URL,
    JWT_SECRET_KEY, JWT_ALGORITHM
)

app = FastAPI(
    title="API Gateway - Linh Ung Pagoda Audio Guide",
    description="Gateway trung tâm điều phối, xác thực access_token và tổng hợp sức khỏe các service",
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
@app.get("/api/health", tags=["Health"])
async def aggregated_health_check():
    """Nâng cấp /health của gateway thành tổng hợp trạng thái các service"""
    services = {
        "auth-service": f"{AUTH_SERVICE_URL}/health",
        "poi-service": f"{POI_SERVICE_URL}/health",
        "chatbot-service": f"{CHATBOT_SERVICE_URL}/health",
        "data-pipeline-service": f"{DATA_PIPELINE_SERVICE_URL}/health",
    }
    details = {"api-gateway": "ok"}
    all_healthy = True

    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, url in services.items():
            try:
                res = await client.get(url)
                if res.status_code == 200:
                    details[name] = "ok"
                else:
                    details[name] = f"unhealthy ({res.status_code})"
                    all_healthy = False
            except Exception:
                details[name] = "unreachable (local/in-process)"

    return {
        "status": "ok" if all_healthy else "degraded",
        "services": details
    }


def verify_jwt_token(token: str) -> dict:
    """Kiểm tra token bằng JWT secret key nội bộ (tương thích gRPC / Direct Auth)"""
    try:
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return decoded
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mã xác thực không hợp lệ hoặc đã hết hạn"
        )


async def authenticate_request(request: Request) -> dict:
    """Xác thực access_token trong Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mã xác thực không hợp lệ hoặc đã hết hạn"
        )
    token = auth_header.split(" ")[1]
    return verify_jwt_token(token)


async def forward_request(target_url: str, request: Request):
    """Chuyển tiếp HTTP Request tới service nội bộ"""
    method = request.method
    headers = dict(request.headers)
    headers.pop("host", None)
    content = await request.body()
    params = dict(request.query_params)

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                params=params,
                content=content
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Dịch vụ nội bộ đang tạm thời không khả dụng, vui lòng thử lại sau."
            )


# --- ROUTING RULES ---

# 1. /auth/* & /api/auth/*
@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Auth"])
@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Auth"])
async def route_auth(path: str, request: Request):
    url = f"{AUTH_SERVICE_URL}/auth/{path}"
    return await forward_request(url, request)


# 2. /pois/* & /api/pois/*
@app.api_route("/pois/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["POIs"])
@app.api_route("/api/pois/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["POIs"])
async def route_pois(path: str, request: Request):
    await authenticate_request(request)
    url = f"{POI_SERVICE_URL}/pois/{path}"
    return await forward_request(url, request)


# 3. /chat/* & /api/chat/*
@app.api_route("/chat/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Chatbot"])
@app.api_route("/api/chat/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Chatbot"])
async def route_chat(path: str, request: Request):
    await authenticate_request(request)
    url = f"{CHATBOT_SERVICE_URL}/chat/{path}"
    return await forward_request(url, request)


# 4. /admin/* & /api/admin/*
@app.api_route("/admin/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Admin"])
@app.api_route("/api/admin/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Admin"])
async def route_admin(path: str, request: Request):
    user = await authenticate_request(request)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập chức năng quản trị viên"
        )

    # Định tuyến tùy tính năng Admin
    if path.startswith("cash-code") or path.startswith("sessions") or path.startswith("active-visitors"):
        url = f"{AUTH_SERVICE_URL}/auth/admin/{path.replace('admin/', '')}"
    elif path.startswith("monitoring"):
        url = f"{DATA_PIPELINE_SERVICE_URL}/monitoring"
    else:
        url = f"{POI_SERVICE_URL}/{path}"
    return await forward_request(url, request)


# 5. /monitoring & /api/monitoring
@app.get("/monitoring", tags=["Monitoring"])
@app.get("/api/monitoring", tags=["Monitoring"])
async def route_monitoring(request: Request):
    user = await authenticate_request(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Yêu cầu quyền quản trị viên")
    url = f"{DATA_PIPELINE_SERVICE_URL}/monitoring"
    return await forward_request(url, request)

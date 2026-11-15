import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

from app.config import settings
from app.services.rate_limiter import rate_limiter
from app.services.auth_validator import is_public_route, verify_token, check_rbac_permission

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api-gateway")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Khởi động API Gateway...")
    await rate_limiter.connect()
    yield
    logger.info("Tắt API Gateway...")
    await rate_limiter.disconnect()

app = FastAPI(
    title="Chùa Linh Ứng - API Gateway",
    description="Cổng giao tiếp tập trung: Reverse Proxy, Xác thực JWT, Phân quyền RBAC & Giới hạn tần suất IP",
    version="1.0.0",
    lifespan=lifespan
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Rate Limiting Middleware (áp dụng toàn bộ endpoint)
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "127.0.0.1")
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    allowed, current_count = await rate_limiter.is_allowed(client_ip)
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": {
                    "error_code": "IP_RATE_LIMIT_EXCEEDED",
                    "message": "Quá nhiều yêu cầu từ địa chỉ IP của bạn. Vui lòng thử lại sau.",
                    "current_count": current_count
                }
            }
        )
    return await call_next(request)

def get_downstream_url(path: str) -> Optional[str]:
    """Ánh xạ đường dẫn tới URL của microservice tương ứng"""
    if path.startswith("/api/auth"):
        return settings.AUTH_SERVICE_URL
    elif path.startswith("/api/pois") or path.startswith("/api/languages"):
        return settings.POI_SERVICE_URL
    elif path.startswith("/api/chatbot"):
        return settings.CHATBOT_SERVICE_URL
    return None

@app.get("/health", tags=["System"])
@app.get("/api/gateway/health", tags=["System"])
async def gateway_health():
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0"
    }

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def reverse_proxy(request: Request, path: str):
    full_path = f"/{path}"

    # 1. Kiểm tra Authentication & RBAC (nếu không phải public route)
    if not is_public_route(full_path, request.method):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": {
                        "error_code": "MISSING_TOKEN",
                        "message": "Yêu cầu cung cấp Authorization Bearer Token hợp lệ"
                    }
                }
            )

        token = auth_header.split(" ")[1]
        payload = verify_token(token)
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": {
                        "error_code": "INVALID_TOKEN",
                        "message": "Token không hợp lệ hoặc đã hết hạn"
                    }
                }
            )

        user_role = payload.get("role", "")
        permitted, rbac_msg = check_rbac_permission(full_path, request.method, user_role)
        if not permitted:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": {
                        "error_code": "PERMISSION_DENIED",
                        "message": rbac_msg
                    }
                }
            )

    # 2. Tìm máy chủ microservice đích
    downstream_base = get_downstream_url(full_path)
    if not downstream_base:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": {
                    "error_code": "NOT_FOUND",
                    "message": f"Không tìm thấy dịch vụ tương ứng với đường dẫn: {full_path}"
                }
            }
        )

    # 3. Chuyển tiếp Request qua httpx
    if downstream_base.startswith("http://"):
        scheme = "http://"
        host_part = downstream_base[7:]
    elif downstream_base.startswith("https://"):
        scheme = "https://"
        host_part = downstream_base[8:]
    else:
        scheme = "http://"
        host_part = downstream_base

    # Tự động gắn port cho mạng nội bộ Render nếu thiếu port
    if ":" not in host_part and not any(host_part.endswith(tld) for tld in [".com", ".org", ".io", ".net", ".app"]):
        if "auth" in host_part:
            host_part = f"{host_part}:8001"
        elif "poi" in host_part:
            host_part = f"{host_part}:8002"
        elif "chatbot" in host_part:
            host_part = f"{host_part}:8003"

    downstream_base = f"{scheme}{host_part}"
    target_url = f"{downstream_base.rstrip('/')}{full_path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    try:
        body = await request.body()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                params=request.query_params,
                headers=headers,
                content=body
            )

            # Lọc bỏ headers hop-by-hop
            excluded_headers = {"content-encoding", "content-length", "transfer-encoding", "connection"}
            forward_headers = {
                k: v for k, v in resp.headers.items() if k.lower() not in excluded_headers
            }

            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=forward_headers,
                media_type=resp.headers.get("content-type")
            )
    except httpx.ConnectError:
        logger.error(f"Không thể kết nối tới microservice đích tại: {target_url}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": {
                    "error_code": "SERVICE_UNAVAILABLE",
                    "message": "Dịch vụ máy chủ đích đang tạm thời gián đoạn. Vui lòng thử lại sau ít phút."
                }
            }
        )
    except Exception as e:
        logger.error(f"Lỗi Gateway Proxy: {e}")
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "detail": {
                    "error_code": "BAD_GATEWAY",
                    "message": f"Lỗi cổng kết nối nội bộ: {str(e)}"
                }
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)

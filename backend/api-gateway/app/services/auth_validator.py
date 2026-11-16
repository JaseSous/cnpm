from typing import Optional, Dict, Any, Tuple
from jose import jwt, JWTError
from app.config import settings

PUBLIC_PATHS = [
    "/health",
    "/api/gateway/health",
    "/api/auth/login",
    "/api/auth/verify-code",
    "/api/auth/packages",
    "/docs",
    "/openapi.json",
    "/redoc"
]

def is_public_route(path: str, method: str) -> bool:
    """Kiểm tra đường dẫn có thuộc danh sách công khai không cần token không"""
    if path.startswith("/media") and method.upper() == "GET":
        return True
    for pub in PUBLIC_PATHS:
        if path.rstrip("/") == pub.rstrip("/"):
            return True
    return False

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Giải mã và xác thực chữ ký JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None

def check_rbac_permission(path: str, method: str, role: str) -> Tuple[bool, str]:
    """
    Kiểm tra phân quyền theo vai trò (RBAC):
    - admin: Toàn quyền truy cập mọi endpoint
    - staff: Được tạo vé (/api/auth/tickets), xem thông tin (/api/auth/me), đọc POI (/api/pois GET)
    - customer: Được đọc POI (/api/pois GET), đọc ngôn ngữ (/api/languages), chat AI (/api/chatbot/ask)
    """
    path = path.rstrip("/")
    method = method.upper()

    if role == "admin":
        return True, "ALLOWED"

    # Tuyến đường cho Staff
    if role == "staff":
        if (
            path.startswith("/api/auth/tickets")
            or path.startswith("/api/auth/packages")
            or path.startswith("/api/auth/me")
            or path.startswith("/api/auth/dashboard-stats")
        ):
            return True, "ALLOWED"
        if method == "GET" and (path.startswith("/api/pois") or path.startswith("/api/languages")):
            return True, "ALLOWED"
        return False, "Quyền Staff không được phép thực hiện thao tác này."

    # Tuyến đường cho Khách du lịch (Customer)
    if role == "customer":
        if method == "GET" and (path.startswith("/api/pois") or path.startswith("/api/languages")):
            return True, "ALLOWED"
        if path.startswith("/api/chatbot/ask"):
            return True, "ALLOWED"
        return False, "Khách du lịch chỉ có quyền tra cứu cẩm nang và hỏi đáp AI."

    return False, "Vai trò không hợp lệ."

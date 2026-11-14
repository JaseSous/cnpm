from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings

security_bearer = HTTPBearer(auto_error=False)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
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

async def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> Dict[str, Any]:
    """Dependency trích xuất thông tin người dùng từ Bearer Token"""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "MISSING_TOKEN", "message": "Yêu cầu Bearer Token để sử dụng Chatbot AI"}
        )
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_TOKEN", "message": "Token không hợp lệ hoặc đã hết hạn"}
        )
    return payload

async def require_customer_or_admin(
    payload: Dict[str, Any] = Depends(get_current_user_payload)
) -> Dict[str, Any]:
    """Kiểm tra role phải là customer hoặc admin"""
    role = payload.get("role")
    if role not in ("customer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "PERMISSION_DENIED", "message": "Chỉ khách du lịch hoặc quản trị viên mới có quyền sử dụng"}
        )
    return payload

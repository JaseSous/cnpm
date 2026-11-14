from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Tên đăng nhập Staff hoặc Admin")
    password: str = Field(..., min_length=4, max_length=100, description="Mật khẩu")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    username: str
    expires_at: datetime

class VerifyCodeRequest(BaseModel):
    shorted_code: str = Field(..., min_length=10, max_length=10, description="Mã vé 10 ký tự do Staff cấp")

class CustomerTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "customer"
    session_id: str
    expires_at: datetime

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None

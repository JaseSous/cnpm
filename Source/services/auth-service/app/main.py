# Auth Service - Xác thực và Cấp quyền truy cập (UC01)
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import uuid
import time
import sqlite3
import random
import string
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Response, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
import bcrypt

from shared.config import (
    DATA_DIR, JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
)
from shared.adapters import shared_cache

def hash_password(password: str) -> str:
    pwd_bytes = password[:72].encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password[:72].encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

app = FastAPI(
    title="Authorization Service",
    description="Xác thực người dùng, phiên thanh toán Payoo/tiền mặt và cấp JWT access_token (UC01)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = DATA_DIR / "auth.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Khởi tạo bảng Users và PaymentSessions theo đúng ERD trong PRD"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Bảng Users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'visitor',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Bảng PaymentSessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS PaymentSessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                auth_code TEXT UNIQUE,
                payment_method TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                access_token TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        """)
        # Seed tài khoản admin nếu chưa có
        cursor.execute("SELECT user_id FROM Users WHERE username = 'admin'")
        if not cursor.fetchone():
            hashed = hash_password("admin123")
            cursor.execute(
                "INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", hashed, "admin")
            )
        conn.commit()

init_db()

# --- Pydantic Schemas ---
class VerifyRequest(BaseModel):
    code: Optional[str] = None
    auth_code: Optional[str] = None
    shorted_code: Optional[str] = None

class TokenVerifyRequest(BaseModel):
    token: str

class LoginRequest(BaseModel):
    username: str
    password: str

class CreatePayooSessionRequest(BaseModel):
    amount: float = 50000.0
    payment_method: str = "online"

class WebhookRequest(BaseModel):
    auth_code: str
    status: str = "Success"  # Pending | Success | Failed

def generate_jwt_token(subject: str, role: str, session_id: Optional[str] = None) -> str:
    """Sinh access_token JWT có thời hạn"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": subject,
        "role": role,
        "session_id": session_id,
        "exp": expire
    }
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# --- Endpoints UC01 ---

@app.get("/health", tags=["Health"])
async def health_check():
    """Kiểm tra sức khỏe dịch vụ Auth"""
    return {"status": "ok", "service": "auth-service"}


@app.post("/auth/verify", tags=["UC01 - Authentication"])
async def verify_auth_code(payload: VerifyRequest):
    """
    UC01 Bước 3: Xác thực auth_code (online) hoặc shorted_code (tiền mặt).
    - E1: Mã rỗng hoặc sai định dạng -> 400 'Vui lòng nhập mã xác thực hợp lệ'
    - Tiền mặt: Tra Redis Cache -> cấp token, xóa ngay (dùng 1 lần)
    - Online: Tra PaymentSessions -> Success: cấp token, Pending (A1): trả 'đang chờ xử lý'
    - E2: Mã không tồn tại/hết hạn -> 401 'Mã xác thực không hợp lệ hoặc đã hết hạn'
    """
    raw_code = payload.code or payload.auth_code or payload.shorted_code

    # UC01 E1: Mã xác thực bị bỏ trống hoặc sai định dạng
    if not raw_code or not isinstance(raw_code, str) or len(raw_code.strip()) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng nhập mã xác thực hợp lệ"
        )

    code = raw_code.strip().upper()

    # 1. Kiểm tra luồng Tiền mặt trong Redis Cache (shorted_code dùng 1 lần)
    cache_key = f"cash:{code}"
    cached_session = shared_cache.pop_once(cache_key)
    if cached_session:
        # Mã tiền mặt hợp lệ và còn hạn TTL -> Sinh JWT access_token
        session_id = cached_session.get("session_id", str(uuid.uuid4()))
        token = generate_jwt_token(subject="cash_visitor", role="visitor", session_id=session_id)
        
        # Cập nhật session vào DB
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE PaymentSessions SET access_token = ?, status = 'Success' WHERE session_id = ?",
                (token, session_id)
            )
            conn.commit()

        # UC01 bước 5: Trả access_token về cho Client App
        return {
            "status": "Success",
            "access_token": token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "message": "Xác thực tiền mặt thành công"
        }

    # 2. Kiểm tra luồng Online trong DB (PaymentSessions)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM PaymentSessions WHERE auth_code = ?", (code,))
        row = cursor.fetchone()

        if not row:
            # UC01 E2: Mã không tồn tại, đã được sử dụng hoặc hết hạn
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Mã xác thực không hợp lệ hoặc đã hết hạn"
            )

        session = dict(row)

        # UC01 E2: Mã tiền mặt đã dùng 1 lần (đã xóa khỏi Cache) -> Không thể dùng lại
        if session.get("payment_method") == "cash":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Mã xác thực không hợp lệ hoặc đã hết hạn"
            )
        if session["status"] == "Pending":
            return {
                "status": "Pending",
                "message": "đang chờ xử lý",
                "auth_code": code
            }

        # Nếu giao dịch thanh toán thành công (Success)
        if session["status"] == "Success":
            token = generate_jwt_token(
                subject=f"user_{session['user_id'] or 'visitor'}",
                role="visitor",
                session_id=session["session_id"]
            )
            cursor.execute(
                "UPDATE PaymentSessions SET access_token = ? WHERE session_id = ?",
                (token, session["session_id"])
            )
            conn.commit()

            return {
                "status": "Success",
                "access_token": token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "message": "Xác thực thanh toán online thành công"
            }

        # Nếu giao dịch bị thất bại
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Giao dịch thanh toán không thành công"
        )


@app.post("/auth/payoo/create-session", tags=["UC01 - Payoo Mock"])
async def create_payoo_session(payload: CreatePayooSessionRequest):
    """Giả lập tạo phiên thanh toán Payoo (QR cổng tham quan)"""
    session_id = str(uuid.uuid4())
    # Sinh mã auth_code ngẫu nhiên 8 ký tự
    rand_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    auth_code = f"PAY-{rand_chars}"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO PaymentSessions (session_id, auth_code, payment_method, amount, status)
            VALUES (?, ?, ?, ?, 'Pending')
        """, (session_id, auth_code, payload.payment_method, payload.amount))
        conn.commit()

    return {
        "session_id": session_id,
        "auth_code": auth_code,
        "amount": payload.amount,
        "status": "Pending",
        "qr_data": f"https://payoo.mock/pay?code={auth_code}",
        "message": "Phiên thanh toán đã được tạo, trạng thái Pending"
    }


@app.post("/auth/payoo/webhook-mock", tags=["UC01 - Payoo Mock"])
async def payoo_webhook_mock(payload: WebhookRequest):
    """Giả lập Webhook Payoo chuyển trạng thái Pending -> Success/Failed"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, status FROM PaymentSessions WHERE auth_code = ?", (payload.auth_code,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên thanh toán")

        cursor.execute(
            "UPDATE PaymentSessions SET status = ? WHERE auth_code = ?",
            (payload.status, payload.auth_code)
        )
        conn.commit()

    return {
        "success": True,
        "auth_code": payload.auth_code,
        "new_status": payload.status,
        "message": f"Webhook cập nhật phiên sang '{payload.status}' thành công"
    }


@app.post("/auth/admin/cash-code", tags=["UC01 - Admin Cash Code"])
async def create_cash_short_code():
    """Admin tạo mã shorted_code tiền mặt (10 ký tự), lưu Redis Cache có TTL, dùng 1 lần"""
    # Tạo mã shorted_code đúng 10 ký tự gồm chữ hoa và số
    shorted_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    session_id = str(uuid.uuid4())

    # Lưu thông tin phiên vào DB
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO PaymentSessions (session_id, auth_code, payment_method, amount, status)
            VALUES (?, ?, 'cash', 50000.0, 'Pending')
        """, (session_id, shorted_code))
        conn.commit()

    # Lưu vào Cache với TTL 3600 giây (1 giờ)
    cache_data = {
        "session_id": session_id,
        "auth_code": shorted_code,
        "created_at": time.time()
    }
    shared_cache.set(f"cash:{shorted_code}", cache_data, ttl_seconds=3600)

    return {
        "shorted_code": shorted_code,
        "session_id": session_id,
        "ttl_seconds": 3600,
        "message": "Tạo mã tiền mặt thành công (có hiệu lực 1 giờ, dùng 1 lần duy nhất)"
    }


@app.post("/auth/verify-token", tags=["Token Verification"])
async def verify_token_endpoint(payload: TokenVerifyRequest):
    """API Gateway gọi để kiểm tra tính hợp lệ của access_token"""
    try:
        decoded = jwt.decode(payload.token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return {
            "valid": True,
            "user_id": decoded.get("sub"),
            "role": decoded.get("role", "visitor"),
            "session_id": decoded.get("session_id")
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mã xác thực không hợp lệ hoặc đã hết hạn"
        )


@app.post("/auth/login", tags=["Admin Login"])
async def login(payload: LoginRequest):
    """Đăng nhập Admin (admin / admin123) cấp token quản trị viên"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username = ?", (payload.username,))
        row = cursor.fetchone()

        if not row or not verify_password(payload.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Tài khoản hoặc mật khẩu không chính xác")

        token = generate_jwt_token(subject=row["username"], role=row["role"])
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": row["role"],
            "username": row["username"]
        }


@app.get("/auth/sessions", tags=["Admin Monitoring"])
async def list_sessions():
    """Lấy danh sách các phiên thanh toán phục vụ quản trị và kiểm thử"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, auth_code, payment_method, amount, status, created_at FROM PaymentSessions ORDER BY created_at DESC LIMIT 50")
        rows = [dict(r) for r in cursor.fetchall()]
        return {"sessions": rows}

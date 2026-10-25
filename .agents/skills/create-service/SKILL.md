---
name: create-service
description: Hướng dẫn quy chuẩn tạo mới một microservice độc lập trong hệ thống backend theo kiến trúc Hướng 3 của dự án.
---

# 🚀 SKILL: HƯỚNG DẪN TẠO MICROSERVICE MỚI

Skill này hướng dẫn các bước chuẩn hóa để tạo một microservice mới trong thư mục `Source/services/`, tích hợp vào `docker-compose.yml`, kết nối qua `api-gateway` và bổ sung unit test.

---

## Bước 1: Khởi Tạo Cấu Trúc Thư Mục Service

Tạo thư mục mới tại `Source/services/<tên-service>/` với cấu trúc chuẩn:

```
Source/services/<tên-service>/
├── Dockerfile
├── requirements.txt
└── app/
    ├── __init__.py
    ├── main.py          # FastAPI application entrypoint
    ├── config.py        # Đọc biến môi trường bằng Pydantic BaseSettings
    ├── models.py        # Pydantic schemas (Request/Response)
    └── routes.py        # Router phân tách các API endpoints
```

---

## Bước 2: Thiết Lập FastAPI Application (`app/main.py`)

Mọi service bắt buộc phải có endpoint kiểm tra sức khỏe `/health`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Tên Service API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "<tên-service>"}
```

---

## Bước 3: Viết Dockerfile

Tạo `Source/services/<tên-service>/Dockerfile` sử dụng base image Python nhẹ:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "<PORT>"]
```

---

## Bước 4: Đăng Ký Service Trong `docker-compose.yml`

Bổ sung service vào mạng `gps-network` trong file `Source/docker-compose.yml`:

```yaml
  <tên-service>:
    build:
      context: ./services/<tên-service>
      dockerfile: Dockerfile
    container_name: gps-<tên-service>
    restart: unless-stopped
    env_file: .env
    ports:
      - "<PORT>:<PORT>"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - gps-network
```

---

## Bước 5: Cấu Hình Reverse Proxy Tại `api-gateway`

Mở file `Source/api-gateway/app/main.py`:
1. Thêm biến URL của service mới đọc từ môi trường (ví dụ: `NEW_SERVICE_URL = os.getenv("NEW_SERVICE_URL", "http://localhost:<PORT>")`).
2. Thêm route chuyển tiếp yêu cầu với kiểm tra `access_token` nếu là route cần bảo mật.
3. Thêm service vào endpoint `/health` tổng thể của Gateway.

---

## Bước 6: Thêm Unit Test & Cập Nhật CI/CD

1. Thêm hàm test kiểm thử endpoint `/health` của service mới vào `Source/tests/test_backend.py`.
2. Bổ sung lệnh build Dockerfile vào `.github/workflows/ci.yml`.

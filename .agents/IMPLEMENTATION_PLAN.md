# 📋 KẾ HOẠCH THỰC HIỆN ĐỒ ÁN (IMPLEMENTATION PLAN)
## Ứng dụng Thuyết minh tự động đa ngôn ngữ cho Chùa Linh Ứng

> [!IMPORTANT]
> **Bản kế hoạch chính thức — ĐÃ ĐƯỢC DUYỆT.**
> - Toàn bộ nội dung bám sát PRD, DATABASE_SCHEMA, ARCHITECTURE trong thư mục `.agents/`.
> - **Backend Framework:** Python FastAPI (tất cả 4 microservices + API Gateway).
> - **Cloud Platform:** Render (backend containers) + Vercel (frontend).
> - AI Agent thực hiện **BẮT BUỘC** đọc toàn bộ thư mục `.agents/` trước khi bắt đầu bất kỳ Phase nào.

---

## QUYẾT ĐỊNH KỸ THUẬT ĐÃ DUYỆT

| Hạng mục | Quyết định | Ghi chú |
|:---|:---|:---|
| Backend framework | **Python FastAPI** | Tất cả 4 microservices + API Gateway |
| ORM / DB Driver | **SQLAlchemy** + `aiosqlite` (dev) / `asyncpg` (prod nếu cần) | Theo PRD: SQLite / PostgreSQL |
| Frontend framework | **React + Vite + TypeScript** | 2 SPA: customer-app, admin-dashboard |
| gRPC | **grpcio** + **grpcio-tools** (protobuf) | Giao tiếp nội bộ giữa services |
| Message Broker | **RabbitMQ** qua `aio-pika` | CloudAMQP Free Tier khi deploy |
| Redis client | **redis-py** (async) | Upstash Redis Free Tier khi deploy |
| Vector DB | **Qdrant** qua `qdrant-client` | Qdrant Cloud Free Tier 1GB |
| AI/Embedding | **Google Gemini API** (`text-embedding-004` + `gemini-2.5-flash`) | AI Studio Free Tier |
| TTS | **edge-tts** (Python) | Miễn phí, hỗ trợ 15+ ngôn ngữ |
| Translation | **deep-translator** hoặc **googletrans** | Miễn phí |
| Object Storage | **Supabase Storage** | Public bucket `public-media` |
| Cloud Deploy (Backend) | **Render** (Docker containers) | Free Tier |
| Cloud Deploy (Frontend) | **Vercel** | Free Tier, HTTPS cho GPS/Camera |
| CI/CD | **GitHub Actions** | Monorepo, matrix build |
| Bản đồ | **Leaflet + OpenStreetMap** | `react-leaflet` |
| QR Code | **qrcode.react** (sinh QR) + **html5-qrcode** (quét QR) | |

---

## TỔNG QUAN GIAI ĐOẠN

```mermaid
flowchart LR
    P0["Phase 0<br/>Monorepo &<br/>Hạ tầng cơ bản"]
    P1["Phase 1<br/>Auth Service<br/>UC07, UC08, UC01"]
    P2["Phase 2<br/>POI Service<br/>UC10, UC11, UC02, UC05"]
    P3["Phase 3<br/>Data Pipeline<br/>UC04"]
    P4["Phase 4<br/>Chatbot AI<br/>UC03"]
    P5["Phase 5<br/>Customer App<br/>UC09, UC12, UC06"]
    P6["Phase 6<br/>Gateway +<br/>CI/CD + Deploy"]
    P7["Phase 7<br/>Kiểm thử &<br/>Hoàn thiện"]

    P0 --> P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7
```

| Phase | Tên giai đoạn | Use Cases | Chủ trì commit |
|:---:|:---|:---|:---|
| **0** | Khởi tạo Monorepo & Hạ tầng | — | Luân phiên |
| **1** | Authorization Service + Admin Login/Ticket UI | UC07, UC08, UC01 | Nguyễn Mạnh Thắng |
| **2** | Navigation & POI Service + Admin CRUD/Monitor UI | UC10, UC11, UC02, UC05 | Phạm Minh Khôi |
| **3** | Data Pipeline Service (Background Worker) | UC04 | Trương Thuận Phú |
| **4** | Chatbot AI Service + RAG | UC03 | Trương Thuận Phú |
| **5** | Customer Client App (QR, Map, GPS, Chat) | UC09, UC12, UC06, UC05 | Thắng + Khôi |
| **6** | API Gateway + CI/CD + Deploy Render/Vercel | — | Nguyễn Mạnh Thắng |
| **7** | Kiểm thử tích hợp & Hoàn thiện | Tất cả | Luân phiên |

---

## PHASE 0 — KHỞI TẠO MONOREPO & HẠ TẦNG CƠ BẢN

### Mục tiêu
Thiết lập cấu trúc thư mục Monorepo, Docker Compose local dev, Protobuf definitions, file cấu hình chung.

### Task 0.1 — Cấu trúc thư mục Monorepo

```text
cnpm/
├── .agents/                              # (Đã có) Ngữ cảnh & quy tắc cho AI
├── .github/workflows/                    # GitHub Actions (Phase 6)
├── frontend/
│   ├── customer-app/                     # React + Vite SPA du khách
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   └── Dockerfile
│   └── admin-dashboard/                  # React + Vite SPA Admin/Staff
│       ├── src/
│       ├── public/
│       ├── package.json
│       ├── vite.config.ts
│       ├── tsconfig.json
│       └── Dockerfile
├── backend/
│   ├── api-gateway/                      # FastAPI API Gateway
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── middleware/               # jwt_auth.py, rate_limit.py
│   │   │   └── routes/                   # proxy routes
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── tests/
│   ├── auth-service/                     # Authorization Service (FastAPI)
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── models/                   # SQLAlchemy models (Users, TicketPackages, LoginAttempts, PaymentSessions)
│   │   │   ├── schemas/                  # Pydantic schemas
│   │   │   ├── routes/                   # login, tickets, verify_code
│   │   │   ├── services/                # auth_service.py, token_service.py
│   │   │   └── database.py              # SQLAlchemy engine + session
│   │   ├── data/                         # SQLite DB file (auth_payment.db) — gitignored
│   │   ├── seed.py                       # Seed Admin, Staff, TicketPackages
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── tests/
│   ├── poi-service/                      # Navigation & POI Service (FastAPI + gRPC server)
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── models/                   # SQLAlchemy models (7 bảng POI DB)
│   │   │   ├── schemas/
│   │   │   ├── routes/                   # pois, languages, pipeline_status
│   │   │   ├── services/                 # poi_service.py, outbox_publisher.py
│   │   │   ├── grpc_server/              # gRPC server cho Data Pipeline callback
│   │   │   └── database.py
│   │   ├── data/                         # SQLite DB file (poi.db) — gitignored
│   │   ├── seed.py                       # Seed SupportedLanguages, SystemMetadata
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── tests/
│   ├── chatbot-service/                  # Chatbot AI Service (FastAPI + gRPC server)
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routes/                   # chatbot
│   │   │   ├── services/                 # rag_service.py, gemini_client.py, qdrant_client.py
│   │   │   └── grpc_server/              # gRPC server cho Data Pipeline callback
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── tests/
│   └── data-pipeline-service/            # Data Pipeline Worker (FastAPI worker, không expose HTTP)
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py                   # Startup: kết nối RabbitMQ consumer
│       │   ├── config.py
│       │   ├── consumers/                # poi_upserted.py, poi_deleted.py, poi_retry.py
│       │   ├── services/                 # translator.py, tts_service.py, embedding_service.py
│       │   └── grpc_clients/             # poi_service_client.py, chatbot_service_client.py
│       ├── requirements.txt
│       ├── Dockerfile
│       └── tests/
├── proto/                                # Protobuf definitions
│   ├── poi_service.proto
│   └── chatbot_service.proto
├── docker-compose.yml                    # Local dev orchestration
├── .env.example                          # Mẫu biến môi trường
├── .gitignore
├── README.md
└── Product Requirements Document (PRD).docx
```

### Task 0.2 — `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/

# Node
node_modules/
dist/
build/

# Environment
.env
.env.local
.env.production

# Database files
*.db
*.sqlite3

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Generated protobuf
*_pb2.py
*_pb2_grpc.py
*_pb2.pyi
```

### Task 0.3 — `.env.example`

```env
# ========== CHUNG ==========
JWT_SECRET_KEY=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_CUSTOMER_EXPIRE_MINUTES=480
JWT_ADMIN_EXPIRE_MINUTES=60

# ========== AUTH SERVICE ==========
AUTH_DB_URL=sqlite+aiosqlite:///./data/auth_payment.db
# (Render deploy: dùng persistent disk hoặc PostgreSQL)

# ========== POI SERVICE ==========
POI_DB_URL=sqlite+aiosqlite:///./data/poi.db

# ========== REDIS (Upstash Free Tier) ==========
REDIS_URL=redis://default:xxxxx@xxxxx.upstash.io:6379
# DB 0: Auth Cache (shorted_code TTL, rate limit IP)
# DB 1: Chatbot Cache (FAQ cache, rate limit chat)

# ========== RABBITMQ (CloudAMQP Free Tier) ==========
AMQP_URL=amqps://user:pass@xxxxx.cloudamqp.com/vhost

# ========== GOOGLE GEMINI API (AI Studio Free Tier) ==========
GEMINI_API_KEY=your-gemini-api-key

# ========== QDRANT CLOUD (Free Tier) ==========
QDRANT_URL=https://xxxxx.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_COLLECTION_NAME=poi_embeddings

# ========== SUPABASE STORAGE (Free Tier) ==========
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-key
SUPABASE_BUCKET_NAME=public-media

# ========== SHORTED CODE ==========
SHORTED_CODE_TTL_SECONDS=1800
SHORTED_CODE_LENGTH=10

# ========== RATE LIMIT ==========
RATE_LIMIT_IP_MAX=100
RATE_LIMIT_IP_WINDOW_SECONDS=3600
RATE_LIMIT_CHAT_MAX_PER_SESSION=30

# ========== SERVICES INTERNAL (Docker Compose) ==========
AUTH_SERVICE_URL=http://auth-service:8001
POI_SERVICE_URL=http://poi-service:8002
CHATBOT_SERVICE_URL=http://chatbot-service:8003
POI_GRPC_TARGET=poi-service:50051
CHATBOT_GRPC_TARGET=chatbot-service:50052
```

### Task 0.4 — `docker-compose.yml`

```yaml
version: "3.9"
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    volumes: ["redis-data:/data"]

  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports: ["5672:5672", "15672:15672"]
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest

  auth-service:
    build: ./backend/auth-service
    ports: ["8001:8001"]
    volumes: ["auth-data:/app/data"]
    env_file: .env
    depends_on: [redis]

  poi-service:
    build: ./backend/poi-service
    ports: ["8002:8002", "50051:50051"]
    volumes: ["poi-data:/app/data"]
    env_file: .env
    depends_on: [redis, rabbitmq]

  chatbot-service:
    build: ./backend/chatbot-service
    ports: ["8003:8003", "50052:50052"]
    env_file: .env
    depends_on: [redis]

  data-pipeline:
    build: ./backend/data-pipeline-service
    env_file: .env
    depends_on: [rabbitmq, poi-service, chatbot-service]
    restart: on-failure

  api-gateway:
    build: ./backend/api-gateway
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [auth-service, poi-service, chatbot-service]

volumes:
  redis-data:
  auth-data:
  poi-data:
```

### Task 0.5 — Protobuf definitions (`proto/`)

**`proto/poi_service.proto`:**
```protobuf
syntax = "proto3";
package poi;

service POIInternalService {
  rpc UpdateLocalizationStatus(UpdateLocalizationRequest) returns (UpdateLocalizationResponse);
  rpc UpdateVectorStatus(UpdateVectorRequest) returns (UpdateVectorResponse);
  rpc CreatePipelineAlert(CreateAlertRequest) returns (CreateAlertResponse);
  rpc CheckProcessedEvent(CheckEventRequest) returns (CheckEventResponse);
  rpc MarkEventProcessed(MarkEventRequest) returns (MarkEventResponse);
}

message UpdateLocalizationRequest {
  string event_id = 1;
  int32 poi_id = 2;
  string language_code = 3;
  string status = 4;               // "Done" | "Failed"
  string translated_title = 5;
  string translated_description = 6;
  string audio_url = 7;
  string error_message = 8;
  int32 applied_revision = 9;
}
// ... (responses tương ứng)
```

**`proto/chatbot_service.proto`:**
```protobuf
syntax = "proto3";
package chatbot;

service ChatbotInternalService {
  rpc UpsertVectors(UpsertVectorsRequest) returns (UpsertVectorsResponse);
  rpc DeleteVectors(DeleteVectorsRequest) returns (DeleteVectorsResponse);
  rpc InvalidateFaqCache(InvalidateCacheRequest) returns (InvalidateCacheResponse);
}

message VectorChunk {
  string chunk_text = 1;
  repeated float embedding = 2;
}

message UpsertVectorsRequest {
  int32 poi_id = 1;
  int32 revision = 2;
  string language_code = 3;
  repeated VectorChunk chunks = 4;
}
// ... (responses tương ứng)
```

### Commit dự kiến Phase 0
| # | Message | Tác giả |
|:---:|:---|:---|
| 1 | `chore: khởi tạo cấu trúc monorepo, .gitignore, .env.example` | Nguyễn Mạnh Thắng |
| 2 | `chore: thêm docker-compose.yml cho môi trường dev` | Phạm Minh Khôi |
| 3 | `chore: thêm protobuf definitions gRPC nội bộ` | Trương Thuận Phú |

---

## PHASE 1 — AUTHORIZATION SERVICE (UC07 → UC08 → UC01)

### Mục tiêu
Hoàn thành Authorization Service (FastAPI): Admin/Staff đăng nhập (UC07), Staff tạo mã vé (UC08), du khách đổi mã lấy JWT (UC01). Kèm giao diện Admin Dashboard cho đăng nhập và tạo mã vé.

### Dịch vụ bên ngoài cần hướng dẫn setup
- **Upstash Redis**: Tạo database Free Tier → lấy `REDIS_URL` dán vào `.env`.

### Task 1.1 — Khởi tạo Auth Service (FastAPI)

**`backend/auth-service/requirements.txt`:**
```text
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0
aiosqlite>=0.19.0
redis[hiredis]>=5.0
python-jose[cryptography]>=3.3
passlib[bcrypt]>=1.7
pydantic-settings>=2.0
```

**Database Schema — Auth & Payment DB:**
Tạo đúng 4 bảng SQLAlchemy models theo [DATABASE_SCHEMA.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/DATABASE_SCHEMA.md) mục 1:
- `Users` (user_id, username, password_hash, role, is_active, created_at)
- `TicketPackages` (package_id, package_name, price, description, is_active)
- `LoginAttempts` (username PK, failed_count, locked_until, last_attempt_at)
- `PaymentSessions` (session_id UUID PK, package_id FK, created_by_user_id FK, payment_method, amount, status, created_at, activated_at, token_expires_at)

**`seed.py`:** Tạo dữ liệu ban đầu:
- 1 Admin: `admin` / `admin123` (role=`admin`)
- 1 Staff: `staff01` / `staff123` (role=`staff`)
- 2 TicketPackages: Vé tham quan 50,000 VNĐ, Vé VIP 100,000 VNĐ

### Task 1.2 — UC07: `POST /api/auth/login`

| Bước | Chi tiết |
|:---|:---|
| Input | `{ "username": "...", "password": "..." }` |
| 1 | Kiểm tra `LoginAttempts`: nếu `failed_count >= 5` và `locked_until > now()` → 423 Locked, trả `ACCOUNT_LOCKED` |
| 2 | Truy vấn `Users` theo `username` + `is_active = true` |
| 3 | So sánh `bcrypt.verify(password, password_hash)` |
| 4 | Thất bại → tăng `failed_count`, cập nhật `locked_until` nếu quá ngưỡng → 401 `INVALID_CREDENTIALS` |
| 5 | Thành công → reset `failed_count = 0`, xóa `locked_until` |
| 6 | Sinh JWT `access_token` chứa `{ user_id, username, role, exp }` → trả về token + expires_at |

### Task 1.3 — UC08: `POST /api/auth/tickets`

| Bước | Chi tiết |
|:---|:---|
| Input | `{ "package_id": ..., "amount": 50000 }` + Header `Authorization: Bearer <JWT staff/admin>` |
| 1 | Xác thực JWT, kiểm tra role = `staff` hoặc `admin` |
| 2 | Tạo `PaymentSession`: session_id=UUID4, status=`Pending`, created_by_user_id, amount, package_id |
| 3 | Sinh `shorted_code` 10 ký tự alphanumeric ngẫu nhiên |
| 4 | Kiểm tra Redis DB 0 `EXISTS ticket:<code>` — nếu trùng thì sinh lại (tối đa 5 lần, nếu vượt → 500 `CODE_GENERATION_FAILED`) |
| 5 | `SET ticket:<code> <session_id> EX <TTL>` vào Redis DB 0 |
| 6 | Trả `{ "shorted_code": "A9B8C7D6E5", "session_id": "...", "expires_in": <TTL> }` |

### Task 1.4 — UC01: `POST /api/auth/verify-code`

| Bước | Chi tiết |
|:---|:---|
| Input | `{ "shorted_code": "A9B8C7D6E5" }` |
| 1 | Rate Limit theo IP: `INCR ratelimit:ip:<IP>`, `EXPIRE <window>` → nếu vượt ngưỡng → 429 `RATE_LIMIT_EXCEEDED` |
| 2 | Validate: kiểm tra mã đúng 10 ký tự alphanumeric → 400 `INVALID_CODE_FORMAT` |
| 3 | `GETDEL ticket:<code>` trên Redis DB 0 → lấy `session_id`. Nếu nil → 401 `CODE_INVALID_OR_EXPIRED` |
| 4 | Cập nhật `PaymentSessions`: status=`Success`, activated_at=now(), token_expires_at=now()+TTL |
| 5 | Sinh JWT `access_token` chứa `{ session_id, role: "customer", exp }` |
| 6 | Trả `{ "access_token": "...", "expires_at": "..." }` |

**Xử lý lỗi ngoại lệ:** Nếu DB/Redis lỗi sau khi đã `GETDEL` → khôi phục mã bằng `SET ticket:<code> <session_id> EX <remaining_ttl>` trên Redis.

### Task 1.5 — Admin Dashboard: Login + Tạo mã vé

**`frontend/admin-dashboard/`** — React + Vite + TypeScript:
- **Thư viện cần cài:** `axios`, `react-router-dom`, `qrcode.react`, `@tanstack/react-query`
- **Màn hình Login:** Form username/password → gọi `/api/auth/login` → lưu JWT vào `sessionStorage` → redirect dashboard.
- **Màn hình Tạo mã vé (role Staff):** Dropdown chọn TicketPackage → nhập số tiền → gọi `/api/auth/tickets` → hiển thị `shorted_code` dạng text lớn + mã QR (nội dung QR: `https://<domain>/#code=<shorted_code>`) để Staff cho du khách quét.
- **Layout chung:** Sidebar điều hướng (Tạo mã vé, Quản lý POI, Pipeline Monitor), header hiển thị username/role, nút đăng xuất.

### Commit dự kiến Phase 1
| # | Message | Tác giả |
|:---:|:---|:---|
| 1 | `feat(auth): khởi tạo FastAPI project và schema Auth & Payment DB` | Nguyễn Mạnh Thắng |
| 2 | `feat(auth): seed dữ liệu Admin, Staff, TicketPackages` | Nguyễn Mạnh Thắng |
| 3 | `feat(auth): API đăng nhập Admin/Staff với LoginAttempts brute-force` | Nguyễn Mạnh Thắng |
| 4 | `feat(auth): API tạo mã vé shorted_code lưu Redis TTL` | Nguyễn Mạnh Thắng |
| 5 | `feat(auth): API xác thực mã vé GETDEL sinh JWT customer` | Nguyễn Mạnh Thắng |
| 6 | `feat(admin): khởi tạo admin-dashboard React Vite TypeScript` | Phạm Minh Khôi |
| 7 | `feat(admin): màn hình đăng nhập Admin/Staff` | Phạm Minh Khôi |
| 8 | `feat(admin): màn hình tạo mã vé hiển thị QR code` | Phạm Minh Khôi |
| 9 | `test(auth): unit tests cho auth-service` | Trương Thuận Phú |

---

## PHASE 2 — NAVIGATION & POI SERVICE (UC10 → UC11 → UC02 → UC05)

### Mục tiêu
CRUD điểm tham quan cho Admin (UC10), Outbox Publisher, gRPC server nội bộ, giám sát pipeline (UC11), API truy xuất POI cho du khách (UC02), API ngôn ngữ (UC05). Kèm giao diện Admin Dashboard cho quản lý POI và pipeline.

### Dịch vụ bên ngoài cần hướng dẫn setup
- **CloudAMQP** (RabbitMQ Free Tier): Tạo instance → lấy `AMQP_URL`.
- **Supabase Storage**: Tạo project → tạo bucket `public-media` (public) → tạo folders `thumbnails/` + `audios/` → lấy `SUPABASE_URL` + `SUPABASE_SERVICE_KEY`.

### Task 2.1 — Khởi tạo POI Service (FastAPI + gRPC)

**`backend/poi-service/requirements.txt`:**
```text
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0
aiosqlite>=0.19.0
redis[hiredis]>=5.0
aio-pika>=9.0
grpcio>=1.59.0
grpcio-tools>=1.59.0
python-jose[cryptography]>=3.3
pydantic-settings>=2.0
httpx>=0.25.0
python-multipart>=0.0.6
supabase>=2.0
```

**Database Schema — POI DB:**
Tạo đúng 7 bảng SQLAlchemy models theo [DATABASE_SCHEMA.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/DATABASE_SCHEMA.md) mục 2:
- `SupportedLanguages` (language_code PK, language_name, native_name, is_fallback, tts_supported, is_active)
- `SystemMetadata` (config_key PK, data_version, updated_at)
- `POIs` (poi_id PK, original_language_code FK, original_title, original_description, latitude, longitude, trigger_radius, thumbnail_url, revision, vector_status, vector_last_error, vector_attempt_count, vector_failed_at, created_at, updated_at)
- `POILocalizations` (localization_id PK, poi_id FK, language_code FK, translated_title, translated_description, audio_url, applied_revision, status, last_error, attempt_count, failed_at, updated_at — UNIQUE(poi_id, language_code))
- `OutboxEvents` (event_id UUID PK, poi_id FK, event_type, revision, payload_json, is_published, created_at)
- `ProcessedEvents` (event_id UUID PK, poi_id, event_type, processed_at)
- `PipelineAlerts` (alert_id PK, poi_id FK, language_code FK, alert_type, error_message, triggered_by_user_id, is_resolved, created_at)

**`seed.py`:**
- `SupportedLanguages`: 15 ngôn ngữ (vi ✓fallback, en, zh, ja, ko, fr, de, es, th, ru, pt, it, id, ar, hi).
- `SystemMetadata`: `{ config_key: "poi_data_version", data_version: 1 }`.

### Task 2.2 — UC10: API CRUD POI (Admin)

**`POST /api/pois`** — Tạo POI:
1. Xác thực JWT role=`admin`.
2. Validate: tọa độ hợp lệ, bán kính > 0, tiêu đề/mô tả không rỗng, ngôn ngữ gốc thuộc SupportedLanguages.
3. Upload thumbnail (nếu có) → Supabase Storage `thumbnails/` → nhận `thumbnail_url`.
4. INSERT POI (revision=1, vector_status=`Pending`).
5. Tạo `POILocalizations` trạng thái `Pending` cho mỗi ngôn ngữ hỗ trợ (trừ ngôn ngữ gốc — ngôn ngữ gốc copy trực tiếp original_title/description, status=`Done`).
6. Ghi `OutboxEvents`: event_type=`poi.upserted`, revision=1, payload chứa toàn bộ dữ liệu POI.
7. Tăng `data_version` trong `SystemMetadata`.
8. **Tất cả trong cùng 1 database transaction.**

**`PUT /api/pois/:id`** — Sửa POI:
- Nếu thay đổi tiêu đề/mô tả/ngôn ngữ gốc → tăng `revision`, reset `POILocalizations` status=`Pending` cho tất cả ngôn ngữ, ghi `OutboxEvents` poi.upserted.
- Nếu chỉ thay đổi tọa độ/bán kính/thumbnail → cập nhật trực tiếp, tăng `data_version`, **không** ghi Outbox.

**`DELETE /api/pois/:id`** — Xóa POI:
- Ghi `OutboxEvents` poi.deleted → xóa POI + POILocalizations.

### Task 2.3 — Outbox Publisher (Background task)

- Asyncio background task chạy cùng FastAPI startup.
- Mỗi 5 giây: query `OutboxEvents WHERE is_published = false ORDER BY created_at`.
- Publish mỗi event lên RabbitMQ exchange `poi_events` với routing key = `event_type`.
- Đánh dấu `is_published = true` sau khi publish thành công.
- Queue bindings: `poi.upserted`, `poi.deleted`, `poi.retry` + Dead-Letter Exchange → `poi.dlq`.

### Task 2.4 — gRPC Server (port 50051)

Implement `poi_service.proto`:
- `UpdateLocalizationStatus`: Cập nhật `POILocalizations` (translated_title, translated_description, audio_url, status, applied_revision, hoặc last_error + failed_at nếu Failed). Khi tất cả ngôn ngữ Done → tăng `data_version`.
- `UpdateVectorStatus`: Cập nhật `POIs.vector_status`, `vector_last_error`, `vector_attempt_count`, `vector_failed_at`.
- `CreatePipelineAlert`: Insert vào `PipelineAlerts`.
- `CheckProcessedEvent`: Kiểm tra `event_id` đã tồn tại trong `ProcessedEvents`.
- `MarkEventProcessed`: Insert `ProcessedEvents`.

### Task 2.5 — UC11: `GET /api/pois/pipeline-status` + `POST /api/pois/:id/retry`

- **GET:** Trả danh sách POI kèm mảng trạng thái từng ngôn ngữ + `vector_status` + alerts chưa resolved.
- **POST retry:** Nhận `{ "language_codes": ["en","zh"], "retry_vector": true }` → đặt lại status=`Pending`, ghi `poi.retry` vào OutboxEvents.

### Task 2.6 — UC02: `GET /api/pois?lang=vi&since_version=`

- Xác thực JWT (role=`customer` hoặc `admin`).
- Validate `lang` thuộc SupportedLanguages is_active.
- So sánh `since_version` với `data_version` hiện tại → nếu bằng nhau → 304 Not Modified.
- Query POIs + POILocalizations của ngôn ngữ yêu cầu (chỉ lấy status=`Done`).
- Nếu POI chưa có bản dịch Done → lấy bản dịch ngôn ngữ fallback kèm `fallback: true`.
- Trả JSON: `{ "pois": [...], "data_version": 5 }`.

### Task 2.7 — UC05: `GET /api/languages`

- Trả `SupportedLanguages WHERE is_active = true`.

### Task 2.8 — Admin Dashboard: CRUD POI + Pipeline Monitor

- **Trang Quản lý POI:**
  - Bảng danh sách POI (tiêu đề, ngôn ngữ gốc, tọa độ, revision, trạng thái).
  - Modal/form tạo+sửa POI: input text, textarea mô tả, dropdown ngôn ngữ gốc, input tọa độ lat/lng (hoặc click trên bản đồ nhỏ Leaflet), input bán kính (mét), upload ảnh thumbnail.
  - Nút xóa POI (có xác nhận).
- **Trang Pipeline Monitor (UC11):**
  - Bảng mỗi dòng = 1 POI, cột hiển thị trạng thái từng ngôn ngữ (badge Pending/Done/Failed) + vector_status.
  - Nhấn vào dòng → xem chi tiết lỗi (PipelineAlerts).
  - Checkbox chọn ngôn ngữ Failed + nút "Xử lý lại" gọi API retry.

### Commit dự kiến Phase 2
| # | Message | Tác giả |
|:---:|:---|:---|
| 1 | `feat(poi): khởi tạo FastAPI project và schema POI DB 7 bảng` | Phạm Minh Khôi |
| 2 | `feat(poi): seed SupportedLanguages 15 ngôn ngữ và SystemMetadata` | Phạm Minh Khôi |
| 3 | `feat(poi): API tạo POI với Transactional Outbox và upload thumbnail` | Phạm Minh Khôi |
| 4 | `feat(poi): API sửa và xóa POI với revision và Outbox` | Phạm Minh Khôi |
| 5 | `feat(poi): Outbox Publisher background task publish RabbitMQ` | Trương Thuận Phú |
| 6 | `feat(poi): gRPC server nội bộ cho Data Pipeline callback` | Trương Thuận Phú |
| 7 | `feat(poi): API pipeline-status và retry cho Admin UC11` | Phạm Minh Khôi |
| 8 | `feat(poi): API truy xuất POI với data_version 304 và fallback` | Phạm Minh Khôi |
| 9 | `feat(poi): API danh sách ngôn ngữ hỗ trợ UC05` | Phạm Minh Khôi |
| 10 | `feat(admin): màn hình CRUD POI với upload thumbnail và bản đồ` | Nguyễn Mạnh Thắng |
| 11 | `feat(admin): màn hình Pipeline Monitor trạng thái và Retry` | Nguyễn Mạnh Thắng |
| 12 | `test(poi): unit tests cho poi-service` | Trương Thuận Phú |

---

## PHASE 3 — DATA PIPELINE SERVICE (UC04)

### Mục tiêu
Worker ngầm lắng nghe RabbitMQ, tự động dịch 15+ ngôn ngữ, sinh audio TTS, tạo embeddings, báo cáo qua gRPC.

### Dịch vụ bên ngoài cần hướng dẫn setup
- **Google Gemini API**: Truy cập https://aistudio.google.com → tạo API Key → dán vào `GEMINI_API_KEY`.

### Task 3.1 — Khởi tạo Data Pipeline Service

**`backend/data-pipeline-service/requirements.txt`:**
```text
aio-pika>=9.0
grpcio>=1.59.0
grpcio-tools>=1.59.0
deep-translator>=1.11.0
edge-tts>=6.1.0
google-generativeai>=0.3.0
httpx>=0.25.0
supabase>=2.0
pydantic-settings>=2.0
```

**Startup flow:**
1. Kết nối RabbitMQ → declare exchange `poi_events` (topic).
2. Declare + bind 3 queues: `poi.upserted`, `poi.deleted`, `poi.retry` (+ DLX → `poi.dlq`).
3. Bắt đầu consume.

### Task 3.2 — Consumer: `poi.upserted` / `poi.retry`

```
Nhận message { event_id, poi_id, revision, original_title, original_description, original_language_code, languages_to_process[] }
│
├─ 1. gRPC CheckProcessedEvent(event_id) → nếu đã xử lý → ACK + skip
├─ 2. Kiểm tra revision >= revision hiện tại (chống sai thứ tự)
│
├─ 3. Với mỗi language_code trong languages_to_process (trừ original_language_code):
│   ├─ 3a. Gọi deep-translator dịch original_title → translated_title
│   ├─ 3b. Gọi deep-translator dịch original_description → translated_description
│   ├─ 3c. Nếu tts_supported: Gọi edge-tts tạo file .mp3 từ translated_description
│   ├─ 3d. Upload .mp3 → Supabase Storage audios/poi_{id}_{lang}_rev{rev}.mp3 → nhận audio_url
│   ├─ 3e. gRPC UpdateLocalizationStatus(Done, translated_title, translated_description, audio_url, applied_revision)
│   └─ 3f. Nếu lỗi bất kỳ bước nào → gRPC UpdateLocalizationStatus(Failed, error) + CreatePipelineAlert
│
├─ 4. Tạo embeddings từ original_description (tiếng gốc):
│   ├─ 4a. Gọi Gemini text-embedding-004 → vector FLOAT[768]
│   ├─ 4b. gRPC UpsertVectors(poi_id, revision, chunks[])
│   ├─ 4c. gRPC UpdateVectorStatus(poi_id, "Synced")
│   └─ 4d. Nếu lỗi → gRPC UpdateVectorStatus(poi_id, "Failed", error) + CreatePipelineAlert
│
├─ 5. gRPC MarkEventProcessed(event_id)
└─ 6. ACK message
```

### Task 3.3 — Consumer: `poi.deleted`

1. Xóa audio files trên Supabase Storage (pattern `audios/poi_{id}_*`).
2. gRPC `DeleteVectors(poi_id)` xóa embeddings khỏi Qdrant.
3. gRPC `InvalidateFaqCache(poi_id)` xóa FAQ cache liên quan.
4. ACK message.

### Task 3.4 — Retry & Dead-Letter Queue

- Mỗi message khi lỗi → `NACK` với `requeue=false` (RabbitMQ tự đẩy vào DLX sau `x-delivery-count` đạt `x-max-retries=3`).
- Hoặc tự xử lý retry trong code: đếm `attempt_count`, nếu < 3 → sleep exponential (2^attempt giây) → thử lại; nếu >= 3 → publish vào `poi.dlq`, ghi `PipelineAlerts`.

### Commit dự kiến Phase 3
| # | Message | Tác giả |
|:---:|:---|:---|
| 1 | `feat(pipeline): khởi tạo worker kết nối RabbitMQ consumer 3 queues` | Trương Thuận Phú |
| 2 | `feat(pipeline): gRPC clients kết nối POI Service và Chatbot Service` | Trương Thuận Phú |
| 3 | `feat(pipeline): idempotency check và revision guard` | Trương Thuận Phú |
| 4 | `feat(pipeline): tự động dịch thuật 15+ ngôn ngữ deep-translator` | Trương Thuận Phú |
| 5 | `feat(pipeline): sinh audio Edge-TTS và upload Supabase Storage` | Trương Thuận Phú |
| 6 | `feat(pipeline): tạo embeddings Gemini và đồng bộ Vector DB` | Nguyễn Mạnh Thắng |
| 7 | `feat(pipeline): xử lý poi.deleted xóa audio và vectors` | Nguyễn Mạnh Thắng |
| 8 | `feat(pipeline): retry exponential backoff và Dead-Letter Queue` | Phạm Minh Khôi |
| 9 | `test(pipeline): unit tests cho data-pipeline-service` | Phạm Minh Khôi |

---

## PHASE 4 — CHATBOT AI SERVICE (UC03)

### Mục tiêu
Chatbot hỏi đáp RAG: FAQ Cache trên Redis, Embedding + Qdrant + Gemini LLM, gRPC server cho Data Pipeline.

### Dịch vụ bên ngoài cần hướng dẫn setup
- **Qdrant Cloud**: Truy cập https://cloud.qdrant.io → tạo cluster Free Tier → tạo collection `poi_embeddings` (vector size=768, distance=Cosine) → lấy `QDRANT_URL` + `QDRANT_API_KEY`.

### Task 4.1 — Khởi tạo Chatbot Service (FastAPI + gRPC)

**`backend/chatbot-service/requirements.txt`:**
```text
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
redis[hiredis]>=5.0
grpcio>=1.59.0
grpcio-tools>=1.59.0
qdrant-client>=1.7.0
google-generativeai>=0.3.0
python-jose[cryptography]>=3.3
pydantic-settings>=2.0
```

### Task 4.2 — UC03: `POST /api/chatbot/ask`

| Bước | Chi tiết |
|:---|:---|
| Input | `{ "question": "...", "lang": "vi" }` + Header `Authorization: Bearer <JWT customer>` |
| 1 | Chuẩn hóa câu hỏi: strip, lowercase, loại bỏ khoảng trắng thừa → tạo hash SHA256 |
| 2 | Kiểm tra Redis DB 1 `GET faq:<lang>:<hash>` → nếu có → trả ngay (cache hit) |
| 3 | Rate Limit: `INCR ratelimit:chat:<session_id>` → nếu vượt 30 → 429 `CHAT_RATE_LIMIT` |
| 4 | Gọi Gemini `text-embedding-004` nhúng câu hỏi → vector 768 chiều |
| 5 | Truy vấn Qdrant `poi_embeddings`: tìm top-5 nearest vectors, filter `score >= 0.35` |
| 6 | Nếu không có kết quả → trả "Xin lỗi, tôi không tìm thấy thông tin liên quan" (theo ngôn ngữ `lang`) |
| 7 | Ghép prompt: system instruction + ngữ cảnh tìm được (chunk_text) + câu hỏi gốc + chỉ dẫn trả lời bằng ngôn ngữ `lang` |
| 8 | Gọi Gemini `gemini-2.5-flash` → nhận câu trả lời |
| 9 | Lưu `SET faq:<lang>:<hash> <answer> EX 86400` (TTL 24h) vào Redis DB 1 |
| 10 | Trả `{ "answer": "...", "sources": [...poi_ids liên quan] }` |

### Task 4.3 — gRPC Server (port 50052)

Implement `chatbot_service.proto`:
- `UpsertVectors`: Upsert points vào Qdrant collection `poi_embeddings` (xóa vectors cũ cùng poi_id trước, rồi insert mới).
- `DeleteVectors`: Xóa tất cả vectors có `poi_id` tương ứng khỏi Qdrant.
- `InvalidateFaqCache`: Scan Redis DB 1 keys `faq:*` và xóa (hoặc xóa toàn bộ FAQ cache khi không xác định được POI nào ảnh hưởng).

### Commit dự kiến Phase 4
| # | Message | Tác giả |
|:---:|:---|:---|
| 1 | `feat(chatbot): khởi tạo FastAPI project kết nối Redis DB 1 và Qdrant` | Trương Thuận Phú |
| 2 | `feat(chatbot): API hỏi đáp RAG với FAQ Cache và Rate Limit` | Trương Thuận Phú |
| 3 | `feat(chatbot): tích hợp Gemini Embedding và LLM generation` | Trương Thuận Phú |
| 4 | `feat(chatbot): gRPC server upsert/delete vectors và invalidate cache` | Nguyễn Mạnh Thắng |
| 5 | `test(chatbot): unit tests cho chatbot-service` | Phạm Minh Khôi |

---

## PHASE 5 — CUSTOMER CLIENT APP (UC09, UC12, UC06, UC05)

### Mục tiêu
Ứng dụng Mobile Web cho du khách: chọn ngôn ngữ, quét QR, xem bản đồ/danh sách POI, thuyết minh tự động GPS, chatbot.

### Task 5.1 — Khởi tạo Customer App

**`frontend/customer-app/`** — React + Vite + TypeScript.

**Dependencies:**
```json
{
  "axios": "^1.6",
  "react-router-dom": "^6.0",
  "react-leaflet": "^4.2",
  "leaflet": "^1.9",
  "html5-qrcode": "^2.3",
  "idb": "^7.1",
  "@tanstack/react-query": "^5.0"
}
```

**Cấu trúc pages/routes:**
- `/` → Màn hình chọn ngôn ngữ (UC05) → redirect `/auth`
- `/auth` → Màn hình quét QR / nhập mã (UC09 + UC01) → redirect `/map`
- `/map` → Bản đồ + Danh sách POI (UC12) + GPS Engine (UC06)
- `/poi/:id` → Chi tiết POI + phát audio
- `/chat` → Chatbot AI (UC03)

### Task 5.2 — UC05: Màn hình chọn ngôn ngữ

- Gọi `GET /api/languages` → hiển thị danh sách (native_name + language_name).
- Lưu `language_code` vào `localStorage`.
- Nếu đã có ngôn ngữ trong `localStorage` → skip, vào `/auth` luôn.

### Task 5.3 — UC09 + UC01: Quét QR & Xác thực

- Kiểm tra URL hash: nếu `#code=XXXXXXXXXX` → tự động trích `shorted_code`, xóa hash khỏi URL.
- Nút "Quét mã QR" → mở camera bằng `html5-qrcode` → quét QR → trích `shorted_code` từ URL trong QR.
- Ô nhập mã thủ công (10 ký tự) — fallback.
- Tự động gọi `POST /api/auth/verify-code { shorted_code }` → lưu `access_token` + `expires_at` vào `localStorage`.
- Redirect → `/map`.

### Task 5.4 — UC02: Tải dữ liệu POI & lưu IndexedDB

- Sau khi có `access_token` + `language_code`:
- Đọc `data_version` từ IndexedDB (key: `poi_data_version_<lang>`) → gọi `GET /api/pois?lang=<lang>&since_version=<version>`.
- Nếu 304 → dùng dữ liệu IndexedDB hiện có.
- Nếu 200 → lưu danh sách POIs + `data_version` mới vào IndexedDB theo ngôn ngữ.
- Khi đổi ngôn ngữ: kiểm tra IndexedDB trước, nếu chưa có → gọi API.

### Task 5.5 — UC12: Bản đồ & Danh sách POI

- **Bản đồ:** `react-leaflet` + OpenStreetMap tiles, center tại Chùa Linh Ứng (16.1005, 108.2772).
- Marker cho mỗi POI (icon tùy chỉnh), popup hiển thị tiêu đề.
- Marker vị trí hiện tại (nếu GPS được cấp quyền).
- **Danh sách:** Card mỗi POI (thumbnail, tiêu đề, khoảng cách nếu có GPS), sắp xếp theo khoảng cách hoặc mặc định.
- Nhấn vào POI → navigate `/poi/:id`.
- **Chi tiết POI:** Tiêu đề, mô tả đầy đủ, thumbnail lớn, nút Phát audio.
  - POI có `fallback = true`: Badge "Nội dung dự phòng", ẩn nút Phát.
  - POI không có `audio_url`: Ẩn nút Phát.

### Task 5.6 — UC06: GPS Haversine Engine thuyết minh tự động

```
Geolocation.watchPosition() → callback mỗi khi vị trí thay đổi
│
├─ Với mỗi POI trong danh sách IndexedDB:
│   ├─ Tính distance = haversine(currentPos, poiPos)
│   ├─ Nếu distance <= poi.trigger_radius VÀ poi CHƯA được phát trong session này:
│   │   ├─ Preload audio file từ audio_url (hoặc từ Cache API nếu đã tải)
│   │   ├─ Hiển thị notification "Bạn đang ở gần: <tiêu đề POI>"
│   │   └─ Tự động phát audio (HTML5 Audio API)
│   └─ Nếu distance > trigger_radius * 1.5: Reset trạng thái "đã phát" cho POI đó
│
└─ Preload: Với 3 POI gần nhất chưa tải audio → tải trước vào Cache API
```

**Công thức Haversine (tất cả tính toán trên Client, KHÔNG gửi GPS lên server):**
```javascript
function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371e3; // meters
  const φ1 = lat1 * Math.PI / 180;
  const φ2 = lat2 * Math.PI / 180;
  const Δφ = (lat2 - lat1) * Math.PI / 180;
  const Δλ = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(Δφ/2)**2 + Math.cos(φ1)*Math.cos(φ2)*Math.sin(Δλ/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}
```

### Task 5.7 — UC03: Giao diện Chatbot

- Màn hình chat kiểu tin nhắn (bubble user + bot).
- Ô nhập câu hỏi + nút gửi.
- Gọi `POST /api/chatbot/ask { question, lang }` kèm `Authorization: Bearer <token>`.
- Hiển thị câu trả lời, loading indicator khi đang chờ.
- Giữ lịch sử chat trong session (state React, không persist).

### Commit dự kiến Phase 5
| # | Message | Tác giả |
|:---:|:---|:---|
| 1 | `feat(client): khởi tạo customer-app React Vite TypeScript` | Nguyễn Mạnh Thắng |
| 2 | `feat(client): màn hình chọn ngôn ngữ lưu localStorage UC05` | Phạm Minh Khôi |
| 3 | `feat(client): quét QR html5-qrcode và xác thực mã vé UC09 UC01` | Nguyễn Mạnh Thắng |
| 4 | `feat(client): tải POI lưu IndexedDB theo ngôn ngữ UC02` | Phạm Minh Khôi |
| 5 | `feat(client): bản đồ Leaflet OSM và danh sách POI UC12` | Phạm Minh Khôi |
| 6 | `feat(client): chi tiết POI và phát audio thuyết minh` | Nguyễn Mạnh Thắng |
| 7 | `feat(client): GPS Haversine engine tự động phát audio UC06` | Nguyễn Mạnh Thắng |
| 8 | `feat(client): giao diện Chatbot AI hỏi đáp UC03` | Trương Thuận Phú |

---

## PHASE 6 — API GATEWAY + CI/CD + DEPLOY

### Mục tiêu
Cấu hình API Gateway (FastAPI), GitHub Actions CI/CD, deploy backend lên Render và frontend lên Vercel.

### Dịch vụ bên ngoài cần hướng dẫn setup
- **Render**: Tạo 5 Web Services (Docker) cho api-gateway, auth-service, poi-service, chatbot-service, data-pipeline. Mỗi service cấu hình Environment Variables từ `.env`. Tạo Persistent Disks cho SQLite files.
- **Vercel**: Tạo 2 projects liên kết GitHub repo, cấu hình Root Directory = `frontend/customer-app` và `frontend/admin-dashboard`, cấu hình `VITE_API_BASE` trỏ tới API Gateway URL trên Render.
- **GitHub Secrets**: Thêm `RENDER_API_KEY`, `VERCEL_TOKEN`, và tất cả biến môi trường production.

### Task 6.1 — API Gateway (FastAPI)

**`backend/api-gateway/`:**

```python
# Reverse proxy routing
ROUTES = {
    "/api/auth":    "http://auth-service:8001",
    "/api/pois":    "http://poi-service:8002",
    "/api/languages": "http://poi-service:8002",
    "/api/chatbot": "http://chatbot-service:8003",
}
```

**Middleware stack:**
1. **CORS**: Cho phép origins từ Vercel domains.
2. **Rate Limiting**: Theo IP, dùng Redis DB 0 (key `ratelimit:ip:<ip>`).
3. **JWT Authentication**: Verify signature + expiry. Extract `role` từ payload.
4. **Role-based Access Control**:
   - `/api/auth/login` → Public
   - `/api/auth/verify-code` → Public (có rate limit)
   - `/api/auth/tickets` → role `staff` hoặc `admin`
   - `/api/pois` POST/PUT/DELETE → role `admin`
   - `/api/pois` GET, `/api/languages` → role `customer` hoặc `admin`
   - `/api/pois/pipeline-status`, `/api/pois/:id/retry` → role `admin`
   - `/api/chatbot/ask` → role `customer`
5. **Reverse Proxy**: Forward request tới service tương ứng, trả response.

### Task 6.2 — Dockerfile cho mỗi service

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Hỗ trợ dynamic PORT trên Render
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
```

### Task 6.3 — GitHub Actions CI

**`.github/workflows/ci.yml`:**
```yaml
name: CI
on: [push, pull_request]
jobs:
  test-backend:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [auth-service, poi-service, chatbot-service, data-pipeline-service, api-gateway]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: |
          cd backend/${{ matrix.service }}
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx
          python -m pytest tests/ -v

  test-frontend:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app: [customer-app, admin-dashboard]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: |
          cd frontend/${{ matrix.app }}
          npm ci
          npm run lint
          npm run build
```

### Task 6.4 — GitHub Actions CD

**`.github/workflows/cd.yml`:**
- Trigger: Push vào `main` (sau CI pass).
- Build Docker images cho 5 backend services.
- Push lên GHCR (`ghcr.io/<owner>/cnpm-<service>:latest`).
- Trigger Render Deploy Hook cho mỗi service.

**`.github/workflows/frontend-deploy.yml`:**
- Trigger: Push vào `main` thay đổi `frontend/`.
- Vercel CLI deploy `customer-app` và `admin-dashboard`.

### Commit dự kiến Phase 6
| # | Message | Tác giả |
|:---:|:---|:---|
| 1 | `feat(gateway): FastAPI API Gateway reverse proxy JWT RBAC` | Nguyễn Mạnh Thắng |
| 2 | `chore: Dockerfiles production cho tất cả services` | Trương Thuận Phú |
| 3 | `ci: GitHub Actions workflow CI lint và test matrix` | Nguyễn Mạnh Thắng |
| 4 | `ci: GitHub Actions workflow CD build Docker push GHCR deploy Render` | Nguyễn Mạnh Thắng |
| 5 | `ci: GitHub Actions workflow deploy frontend Vercel` | Phạm Minh Khôi |

---

## PHASE 7 — KIỂM THỬ TÍCH HỢP & HOÀN THIỆN

### Mục tiêu
Seed dữ liệu thực tế Chùa Linh Ứng, kiểm thử end-to-end 3 luồng chính, sửa lỗi, polish UI, viết README.

### Task 7.1 — Seed dữ liệu thực tế

Thêm 5-10 POI thật của Chùa Linh Ứng với tọa độ GPS chính xác:

| POI | Tọa độ (xấp xỉ) | Bán kính |
|:---|:---|:---|
| Tượng Phật Bà Quan Âm | 16.1005, 108.2772 | 50m |
| Chánh Điện | 16.1008, 108.2768 | 30m |
| Vườn La Hán (18 tượng) | 16.1003, 108.2765 | 40m |
| Tháp Xá Lợi | 16.1010, 108.2770 | 25m |
| Cổng Tam Quan | 16.0998, 108.2775 | 20m |

Upload ảnh thumbnail cho mỗi POI. Chạy Data Pipeline để tự động dịch 15 ngôn ngữ và sinh audio.

### Task 7.2 — Kiểm thử End-to-End

**Luồng 1 — Du khách mua vé và tham quan:**
```
Staff login → tạo mã vé → hiện QR
→ Du khách quét QR → nhận token
→ Chọn ngôn ngữ → tải POI
→ Xem bản đồ → đi đến POI → tự động phát audio
→ Hỏi chatbot → nhận câu trả lời
```

**Luồng 2 — Admin quản lý nội dung:**
```
Admin login → thêm POI mới → upload thumbnail
→ Pipeline tự động dịch 15 ngôn ngữ + sinh audio
→ Admin theo dõi Pipeline Monitor → thấy status Done
→ Du khách thấy POI mới trên bản đồ
```

**Luồng 3 — Xử lý lỗi:**
```
Pipeline dịch thất bại 1 ngôn ngữ → status Failed
→ Admin thấy trên Pipeline Monitor → nhấn Retry
→ Pipeline xử lý lại → thành công
```

### Task 7.3 — Sửa lỗi & Tối ưu

- Sửa bugs phát hiện từ kiểm thử.
- Responsive UI customer-app cho mobile (viewport meta, touch-friendly).
- Lazy loading audio, preload POI gần nhất.
- Loading skeletons, error boundaries.

### Task 7.4 — Hoàn thiện tài liệu

- `README.md` gốc: Tổng quan dự án, hướng dẫn cài đặt local (Docker Compose), hướng dẫn deploy, cấu trúc thư mục.
- Cập nhật `.agents/` nếu có thay đổi kiến trúc trong quá trình thực hiện.

### Commit dự kiến Phase 7
| # | Message | Tác giả |
|:---:|:---|:---|
| 1 | `feat(db): seed dữ liệu POI thực tế Chùa Linh Ứng 5-10 điểm` | Phạm Minh Khôi |
| 2 | `fix: sửa lỗi phát hiện từ kiểm thử tích hợp E2E` | Nguyễn Mạnh Thắng |
| 3 | `fix: sửa lỗi pipeline xử lý sai thứ tự revision` | Trương Thuận Phú |
| 4 | `perf(client): tối ưu responsive mobile và lazy loading audio` | Phạm Minh Khôi |
| 5 | `style(client): polish UI customer-app và admin-dashboard` | Nguyễn Mạnh Thắng |
| 6 | `docs: hoàn thiện README hướng dẫn cài đặt và deploy` | Trương Thuận Phú |

---

## TỔNG KẾT PHÂN BỔ COMMIT

| Thành viên | Commit dự kiến | Phạm vi chính |
|:---|:---:|:---|
| **Nguyễn Mạnh Thắng** | ~18 | Auth Service, Client App (QR/GPS), API Gateway, CI/CD, Admin POI UI |
| **Phạm Minh Khôi** | ~18 | POI Service, Admin Dashboard (Login/Ticket/CRUD/Monitor), Client App (Map/Lang), Frontend Deploy |
| **Trương Thuận Phú** | ~18 | Data Pipeline, Chatbot AI, Protobuf, Outbox Publisher, gRPC, Tests, Dockerfiles |

> [!TIP]
> Tổng cộng khoảng **~54 commits** phân bổ đều cho 3 thành viên. Số lượng thực tế có thể tăng thêm do commits sửa lỗi ở Phase 7.

# KIẾN TRÚC HỆ THỐNG VÀ CÔNG NGHỆ (SYSTEM ARCHITECTURE SPECIFICATION)

> [!NOTE]
> Tài liệu này mô tả chi tiết kiến trúc tầng, các Microservices, kênh giao tiếp, công nghệ sử dụng và đường ống CI/CD của dự án theo đúng Lược đồ Component và Lược đồ Triển khai trong PRD.

![Lược đồ Component](diagrams/component_diagram.png)

---

## 1. PHÂN TẦNG KIẾN TRÚC TỔNG THỂ

### 1.1. Tầng Client (Frontend Applications)
Bao gồm 2 ứng dụng Single Page Application (SPA) xây dựng bằng **React + Vite / TypeScript**:
1. **Customer Client App (Mobile Web App):**
   - Tối ưu cho thiết bị di động của du khách tại Chùa Linh Ứng.
   - Chức năng: Quét mã QR hoặc truy cập link `/access#code=...`, xác thực lấy JWT lưu `localStorage`, bộ nhớ đệm `IndexedDB`/`Cache API` lưu danh sách POIs và audio, định vị GPS chạy ngầm tính khoảng cách Haversine tự động phát thuyết minh, màn hình Bản đồ/Danh sách POI (`getMediaUrl` xử lý ảnh Supabase & `/media/` fallback) và giao diện Chatbot AI.
2. **Admin Dashboard (Desktop Web App):**
   - Dành cho Staff và Admin quản trị.
   - Chức năng: Đăng nhập phân quyền (Admin/Staff), màn hình Dashboard thống kê thời gian thực từ `PaymentSessions` (`GET /api/auth/dashboard-stats`), tạo mã vé tiền mặt (`shorted_code`) và sinh mã QR tại quầy kèm lịch sử vé `localStorage` cho Staff, CRUD thông tin điểm tham quan POI kèm upload ảnh thumbnail, giám sát tiến độ xử lý ngôn ngữ/audio và trigger Retry cho Admin.

### 1.2. Tầng API Gateway
- **Công nghệ sử dụng:** FastAPI Gateway (`backend/api-gateway`).
- **Nhiệm vụ:**
  - Điểm tiếp nhận HTTPS Request duy nhất từ bên ngoài (kèm proxy công khai cho `GET /media/*` và `/health`).
  - Kiểm tra tính hợp lệ và thời hạn của JWT (`access_token`).
  - Phân quyền theo vai trò (`customer` / `staff` / `admin`).
  - Giới hạn tốc độ gọi (Rate Limiting) theo IP qua Redis DB 0 (mặc định `RATE_LIMIT_IP_MAX = 5000` req/giờ để không chặn nhầm du khách dùng chung WiFi/4G).
  - Định tuyến (Reverse Proxy) đến các microservice tương ứng qua HTTP.

### 1.3. Tầng Backend Microservices
Hệ thống gồm 4 Microservices độc lập:

#### 1. Authorization Service
- **Nhiệm vụ:**
  - Xác thực đăng nhập Admin/Staff, khóa tạm thời tài khoản khi nhập sai quá số lần (`LoginAttempts`).
  - Cung cấp endpoint thống kê Dashboard (`GET /api/auth/dashboard-stats`) truy vấn trực tiếp từ `PaymentSessions` (mã tạo hôm nay theo UTC+7, tổng mã, mã `Pending`, phiên `Success` đang còn hạn).
  - Staff tạo mã vé tiền mặt `shorted_code` (10 ký tự ngẫu nhiên), ghi nhận `PaymentSessions` với trạng thái `Pending` (dùng naive UTC datetime tương thích `asyncpg`) và lưu vào Redis Logical DB 0 với TTL.
  - Du khách gửi mã vé -> Đối chiếu mã, xóa nguyên tử khỏi Redis (`GETDEL`), cập nhật `PaymentSessions` thành `Success`, sinh JWT `access_token` có hạn gửi về Client.
- **Giao tiếp:** HTTP/REST, kết nối Auth & Payment DB (PostgreSQL trên Supabase qua IPv4 Connection Pooler / SQLite fallback local) và Redis DB 0 (kèm In-memory Redis fallback khi offline).

#### 2. Navigation & POI Service
- **Nhiệm vụ:**
  - Cung cấp danh sách POIs, tọa độ, bản địa hóa theo ngôn ngữ yêu cầu.
  - Hỗ trợ cơ chế kiểm tra `data_version`: nếu Client truyền `since_version` trùng với `data_version` hiện tại thì trả lời HTTP `304 Not Modified` ngay lập tức để tiết kiệm băng thông.
  - Admin tạo/sửa POI: Upload thumbnail trực tiếp lên Supabase Storage qua REST API (`httpx`, fallback về `/media/thumbnails/` cục bộ), lưu POI DB, tăng `revision`, ghi sự kiện `poi.upserted` vào bảng `OutboxEvents`.
  - Tự động gửi HTTP ping đánh thức `linh-ung-pipeline-worker` trên Render (`wake_up_pipeline_worker()`) mỗi khi phát sinh Outbox event mới (tạo/sửa/xóa/retry POI).
  - Giám sát trạng thái pipeline ngôn ngữ (Pending, Done, Failed), hỗ trợ Admin yêu cầu xử lý lại (Retry).
  - Cung cấp **Internal gRPC Server** và **Internal HTTP API (`/api/internal/*`)** dự phòng để Background Worker trên Render cập nhật trạng thái bản dịch/audio và ghi nhận cảnh báo.
- **Giao tiếp:** HTTP/REST (với Gateway và Internal fallback), gRPC (với Data Pipeline), SQL (với POI DB PostgreSQL Supabase / SQLite local), AMQP (Publish sự kiện Outbox lên CloudAMQP/RabbitMQ).

#### 3. Chatbot AI Service
- **Nhiệm vụ:**
  - Tiếp nhận câu hỏi ngôn ngữ tự nhiên từ du khách qua giao diện Chatbot.
  - Xử lý trực tiếp các intent xã giao (`greeting`, `thanks`, `farewell`) trước khi chạy RAG.
  - Chuẩn hóa câu hỏi, kiểm tra FAQ Cache trên Redis Logical DB 1 (trả ngay kết quả nếu trùng lặp).
  - Kiểm tra Rate Limit phiên chat theo `session_id`.
  - Gọi mô hình Embedding đa ngôn ngữ (`gemini-embedding-001`, ép `output_dimensionality=768`) để chuyển câu hỏi thành vector.
  - Truy vấn Vector DB (Qdrant) tìm kiếm ngữ cảnh liên quan (ngưỡng Cosine Similarity cấu hình thực tế `>= 0.55`, hỗ trợ cả POI embeddings và kho tri thức tổng quan `knowledge_base.py`).
  - Ghép prompt ngữ cảnh và gửi tới LLM (`gemini-3.5-flash`) tạo câu trả lời chính xác, sát thực tế Chùa Linh Ứng.
  - Lưu cặp câu hỏi - câu trả lời mới vào Redis Cache và trả về cho du khách.
  - Cung cấp **Internal gRPC Server** và **Internal HTTP API (`/api/internal/*`)** dự phòng cho Background Worker để cập nhật/xóa vector khi POI thay đổi hoặc xóa cache khi câu trả lời lỗi thời.
- **Giao tiếp:** HTTP/REST, gRPC, HTTPS ra ngoài tới Google Gemini AI API, kết nối Redis DB 1 (kèm In-memory fallback) và Qdrant Vector DB (kèm `:memory:` fallback).

#### 4. Data Pipeline Service (Background Worker)
- **Nhiệm vụ:**
  - Chạy ngầm kèm HTTP `/health` probe endpoint (để deploy dạng Web Service trên Render Free Tier và nhận ping đánh thức), lắng nghe Message Queue (RabbitMQ): hàng đợi `poi.upserted`, `poi.deleted`, `poi.retry`.
  - Kiểm tra Idempotency qua bảng `ProcessedEvents` theo `event_id`.
  - Ưu tiên gọi **Gemini Batch Translation** (`gemini-3.5-flash-lite`, tự động xoay vòng sang `gemini-3.5-flash` và `gemini-3.8-flash`) để dịch toàn bộ 15 ngôn ngữ mục tiêu trong **1 request JSON duy nhất**; fallback từng ngôn ngữ qua `GoogleTranslator` và `MyMemoryTranslator` (email định danh `contact@linhungpagoda.vn` mở khóa 10.000 từ/ngày).
  - Tự động gọi Text-to-Speech (`edge-tts`) tạo file âm thanh `.mp3` thuyết minh cho từng ngôn ngữ.
  - Upload file âm thanh vào Supabase Storage (`audios/`) trực tiếp qua REST API (`httpx`), fallback cục bộ khi offline.
  - Gọi Embedding model (`gemini-embedding-001`, 768 chiều) từ mô tả gốc của POI và đồng bộ vào Vector DB qua gRPC (fallback HTTP `/api/internal/upsert-vectors`) tới Chatbot Service.
  - Báo cáo kết quả thành công/thất bại và cập nhật trạng thái bản dịch về Navigation & POI Service qua gRPC (fallback HTTP `/api/internal/*`).
  - Cơ chế tự động thử lại 3 lần với khoảng lùi số mũ (exponential backoff). Nếu quá số lần thử, đẩy sự kiện vào Dead-Letter Queue (`poi.dlq`) và ghi nhận cảnh báo lỗi vào `PipelineAlerts`.

---

## 2. LƯỢC ĐỒ TRIỂN KHAI VÀ HẠ TẦNG (DEPLOYMENT SPECIFICATION)

![Lược đồ Triển khai](diagrams/deployment_diagram.png)

### 2.1. Hạ tầng Cloud & Triển khai
- **Frontend Hosting:** Vercel Edge Network (cung cấp HTTPS miễn phí, mở khóa quyền truy cập GPS và Camera cho Client).
- **Backend Services:** Render Free Tier (5 Docker Web Services theo `render.yaml`: `linh-ung-gateway`, `linh-ung-auth-service`, `linh-ung-poi-service`, `linh-ung-chatbot-service`, `linh-ung-pipeline-worker`).
- **Relational Databases:** PostgreSQL trên **Supabase** (sử dụng IPv4 Connection Pooler + `pool_pre_ping`/`pool_recycle` cho Render Free Tier; SQLite `aiosqlite` cho local dev/test).
- **Redis Cache:** Upstash Redis (Serverless / Free Tier) với 2 Logical DB tách biệt: DB 0 (Auth & Gateway Rate Limit) và DB 1 (Chatbot FAQ Cache & Rate Limit).
- **Message Broker:** CloudAMQP (RabbitMQ Managed Instance).
- **Vector DB:** Qdrant Cloud (Managed Vector Database - Free Tier).
- **Object Storage:** Supabase Storage (Public bucket `public-media` gọi trực tiếp qua REST API `httpx`, hỗ trợ fallback `/media/`).
- **External APIs:**
  - Google Gemini API (`google-genai` SDK): `gemini-embedding-001` (768 chiều), `gemini-3.5-flash` (Chatbot), `gemini-3.5-flash-lite` / `gemini-3.5-flash` / `gemini-3.8-flash` (Pipeline Batch Translation).
  - Translation & Edge-TTS: `deep-translator` (`GoogleTranslator`, `MyMemoryTranslator`) và `edge-tts` tổng hợp giọng nói đa ngôn ngữ.
  - OpenStreetMap (Leaflet): Cung cấp bản đồ nền miễn phí cho Client App.

### 2.2. Quy trình CI/CD Tự động hóa (GitHub Actions)
- Monorepo quản lý toàn bộ mã nguồn Frontend và Backend Microservices.
- GitHub Actions Workflow tự động kích hoạt khi có Push hoặc Pull Request vào nhánh `main`:
  1. **Lint & Test:** Tự động chạy Unit Tests và Linting cho từng Microservice.
  2. **Build Docker:** Đóng gói Docker Images độc lập cho từng service.
  3. **Container Registry:** Đẩy hình ảnh Docker lên GitHub Container Registry (GHCR) hoặc Docker Hub.
  4. **Deploy Webhook:** Kích hoạt Webhook tự động cập nhật container trên Cloud Platform.
  5. **Frontend Deploy:** Tự động build và deploy bản build tĩnh lên Vercel.

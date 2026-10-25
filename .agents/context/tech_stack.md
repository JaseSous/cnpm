# 💻 TECH STACK & CÔNG NGHỆ DỰ ÁN

> **Nguồn trích xuất**: PRD, `Source/docker-compose.yml`, `Source/.github/workflows/ci.yml`, `Source/docs/DECISIONS.md`.

---

## 1. Backend Services

- **Ngôn ngữ:** Python 3.11 / Python 3.13
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (hiệu năng cao, async, tự động sinh tài liệu OpenAPI/Swagger tại `/docs`).
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/)
- **HTTP Client (Liên dịch vụ):** [HTTPX](https://www.python-httpx.org/) (hỗ trợ async request giữa API Gateway và các microservices).
- **Validation & Serialization:** [Pydantic v2](https://docs.pydantic.dev/)
- **Bảo mật & Token:**
  - `python-jose[cryptography]`: Tạo và kiểm tra chữ ký JSON Web Token (JWT).
  - `passlib[bcrypt]`: Mã hóa mật khẩu người dùng theo chuẩn Bcrypt an toàn.

---

## 2. Frontend Client & Admin

- **Thư viện chính:** [React 18](https://react.dev/)
- **Ngôn ngữ:** [TypeScript](https://www.typescriptlang.org/)
- **Build Tool:** [Vite](https://vitejs.dev/) (khởi động cực nhanh, tối ưu HMR).
- **Styling:** [TailwindCSS](https://tailwindcss.com/) + PostCSS
- **Bản đồ số & Tọa độ:** [Leaflet](https://leafletjs.com/) (hiển thị vị trí người dùng, vẽ vòng tròn bán kính kích hoạt Geofence).
- **Biểu tượng (Icons):** [Lucide React](https://lucide.dev/)
- **Thuyết minh giọng nói:** Tích hợp [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API) phát âm thanh trực tiếp trên trình duyệt Client theo từng ngôn ngữ đã tải.

---

## 3. Cơ Sở Dữ Liệu & Hàng Đợi Thông Điệp

- **PostgreSQL 15 (Alpine):** Hệ quản trị CSDL quan hệ chính cho tài khoản, giao dịch thanh toán và dữ liệu điểm tham quan.
- **Redis 7 (Alpine):** Bộ nhớ đệm tốc độ cao phục vụ:
  - Cache mã vé tiền mặt ngắn hạn có thời gian sống (`TTL`).
  - Cache câu trả lời hỏi đáp thường gặp (`ChatbotFAQCache`).
- **RabbitMQ 3 (Management Alpine):** Message Broker xử lý hàng đợi bất đồng bộ:
  - Exchange & Queue: `poi.upserted`
  - Cơ chế Dead-Letter Queue (DLQ): `poi.dlq` khi xử lý tác vụ dịch thất bại quá số lần cho phép.
- **SQLite / In-Memory Fallback Adapter:** Cho phép toàn bộ logic chạy mượt mà ngay trên máy tính mà không bắt buộc có Docker.

---

## 4. Trí Tuệ Nhân Tạo (AI) & Xử Lý Đa Ngôn Ngữ

- **Kỹ thuật Chatbot:** RAG (Retrieval-Augmented Generation).
- **Vector Search:** Tính toán độ tương đồng Cosine Similarity dựa trên vector embedding với ngưỡng phân định `SIMILARITY_THRESHOLD = 0.35`.
- **Dịch thuật tự động:** Hỗ trợ cấu hình pipeline dịch thuật sang 15+ ngôn ngữ:
  `vi, en, zh, ja, ko, fr, de, es, ru, th, id, ms, it, pt, ar`.

---

## 5. DevOps, Container Hóa & CI/CD

- **Container Engine:** Docker & Docker Compose v2.
- **CI/CD Platform:** GitHub Actions (`.github/workflows/ci.yml`):
  - Job tự động kiểm thử Unit Test Backend (`pytest -v tests/test_backend.py`).
  - Job build Frontend bundle (`npm run build`).
  - Job kiểm tra tính đúng đắn khi build Dockerfile của toàn bộ 5 backend services và frontend.
- **Kịch bản khởi chạy tự động:**
  - `start.bat` (Windows): Khởi động toàn bộ hệ thống bằng 1 lệnh không cần Docker.
  - `start.sh` (Linux/macOS).
  - `docker-compose up --build` (khi chạy toàn bộ container).

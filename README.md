# Trang Web Ứng Dụng Thuyết Minh Tự Động Đa Ngôn Ngữ Cho Chùa Linh Ứng

[![Architecture: Microservices](https://img.shields.io/badge/Architecture-Microservices-blue.svg)](.agents/ARCHITECTURE.md)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript%20%2B%20Vite-61DAFB.svg)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](docker-compose.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Đồ án môn học **Công nghệ phần mềm**: Hệ thống thuyết minh tự động đa ngôn ngữ ứng dụng tại **Chùa Linh Ứng (Bãi Bụt, Bán đảo Sơn Trà, TP. Đà Nẵng)**. Hệ thống bao gồm 2 ứng dụng Frontend (Customer Mobile Web App, Admin Dashboard) và 4 Microservices Backend kèm API Gateway, giao tiếp qua REST HTTP, gRPC nội bộ và RabbitMQ Event-Driven Message Broker, triển khai với quy trình CI/CD hoàn chỉnh.

---

## 👥 THÀNH VIÊN THỰC HIỆN (TEAM MEMBERS)

| STT | Họ và tên | MSSV | Email Git | Phân công phụ trách chính |
|:---:|:---|:---:|:---|:---|
| 1 | **Nguyễn Mạnh Thắng** | 3124411283 | `jasesous@gmail.com` | Authorization Service, Auth Client App (QR & Token), API Gateway, CI/CD |
| 2 | **Phạm Minh Khôi** | 3124411135 | `phamkhoi944@gmail.com` | Navigation & POI Service, Admin Dashboard, Redis Cache, Bản đồ GPS |
| 3 | **Trương Thuận Phú** | 3124411234 | `thuanphutruong1234@gmail.com` | Chatbot AI Service (RAG), Data Pipeline Service (Worker), Vector DB & RabbitMQ |

---

## 🏛️ TỔNG QUAN HỆ THỐNG VÀ 12 USE CASES

Hệ thống phục vụ 3 nhóm đối tượng: **Du khách (Customer)**, **Nhân viên quầy vé (Staff)**, và **Quản trị viên (Admin)**.

| Nhóm chức năng | Mã UC | Tên Use Case | Tác nhân chính |
|:---|:---:|:---|:---|
| **Xác thực & Mã vé** | **UC01** | Quét mã QR / Nhập mã nhận diện (`shorted_code`) | Du khách |
| | **UC07** | Đăng nhập hệ thống quản trị | Admin, Staff |
| | **UC08** | Bán vé tại quầy (Tạo mã vé tiền mặt & in QR) | Staff |
| **Thuyết minh & Bản đồ** | **UC02** | Xem danh sách & Bản đồ điểm tham quan (POIs) | Du khách |
| | **UC05** | Chọn ngôn ngữ thuyết minh (15+ ngôn ngữ) | Du khách |
| | **UC06** | Thuyết minh tự động theo vị trí GPS & Phát Audio | Du khách |
| | **UC09** | Sử dụng ngoại tuyến (Offline mode qua IndexedDB & Cache) | Du khách |
| **Hỏi đáp AI** | **UC03** | Hỏi đáp thông tin với Chatbot AI (Gemini Flash RAG) | Du khách |
| | **UC12** | Đánh giá câu trả lời của Chatbot | Du khách |
| **Quản trị nội dung** | **UC10** | Quản lý thông tin điểm tham quan (CRUD POI) | Admin |
| | **UC11** | Giám sát tiến độ xử lý dịch & âm thanh (Retry Pipeline) | Admin |
| | **UC04** | Tự động xử lý ngôn ngữ, TTS & Vector DB (Background Worker)| Hệ thống |

---

## 🏗️ KIẾN TRÚC MONOREPO VÀ CÔNG NGHỆ

```text
cnpm/
├── .agents/                              # Chỉ dẫn, PRD, Database Schema, Kiến trúc cho AI Agents
├── .github/workflows/                    # GitHub Actions CI/CD pipeline
├── frontend/
│   ├── customer-app/                     # React + Vite SPA cho du khách (Mobile Web)
│   └── admin-dashboard/                  # React + Vite SPA cho Admin/Staff (Desktop Web)
├── backend/
│   ├── api-gateway/                      # FastAPI API Gateway (Auth proxy, Rate limiting)
│   ├── auth-service/                     # Authorization Service (UC01, UC07, UC08)
│   ├── poi-service/                      # Navigation & POI Service + gRPC Server (UC02, UC10, UC11)
│   ├── chatbot-service/                  # Chatbot AI Service (RAG) + gRPC Server (UC03, UC12)
│   └── data-pipeline-service/            # Background Worker (Dịch đa ngôn ngữ, Edge-TTS, Embeddings)
├── proto/                                # Protobuf schemas định nghĩa gRPC nội bộ
├── docker-compose.yml                    # Điều phối môi trường phát triển cục bộ
├── .env.example                          # Mẫu cấu hình biến môi trường
└── README.md                             # Tài liệu dự án
```

### Công nghệ chủ đạo:
- **Backend Framework:** Python FastAPI (tất cả 4 Microservices + API Gateway)
- **Database & ORM:** SQLAlchemy + SQLite (`aiosqlite` dev) / PostgreSQL (`asyncpg` prod)
- **Frontend Framework:** React 18, Vite, TypeScript, TailwindCSS, Leaflet, HTML5-QRCode
- **Giao tiếp nội bộ:** gRPC (`grpcio` + `protobuf`) giữa Pipeline Worker và POI/Chatbot Service
- **Message Broker:** RabbitMQ (`aio-pika`) theo mô hình Transactional Outbox & Event-Driven
- **Cache & Rate Limit:** Redis 7 (DB 0: Auth/Tickets TTL; DB 1: Chatbot FAQ Cache)
- **Vector Database:** Qdrant Cloud (Cosine Similarity cho RAG)
- **AI & TTS:** Google Gemini API (`gemini-2.5-flash`, `text-embedding-004`), Edge-TTS (15+ ngôn ngữ)
- **Object Storage:** Supabase Storage (Public bucket `public-media` chứa thumbnails và audio thuyết minh)

---

## 🚀 HƯỚNG DẪN KHỞI CHẠY (LOCAL DEVELOPMENT)

### Yêu cầu tiên quyết:
- Docker & Docker Compose (v2.0+)
- Python 3.11+
- Node.js 18+ & npm

### Bước 1: Sao chép tệp biến môi trường
```powershell
cp .env.example .env
```
Cập nhật các API key nếu có (Gemini API Key, Supabase Key, Qdrant URL).

### Bước 2: Khởi chạy toàn bộ hệ thống bằng Docker Compose
```powershell
docker compose up -d
```

### Bước 3: Truy cập các cổng dịch vụ
- **API Gateway:** [http://localhost:8000](http://localhost:8000) (Tài liệu API Swagger: `/docs`)
- **Auth Service:** [http://localhost:8001/docs](http://localhost:8001/docs)
- **POI Service:** [http://localhost:8002/docs](http://localhost:8002/docs) (gRPC: port 50051)
- **Chatbot Service:** [http://localhost:8003/docs](http://localhost:8003/docs) (gRPC: port 50052)
- **RabbitMQ Dashboard:** [http://localhost:15672](http://localhost:15672) (User: `guest` / Pass: `guest`)
- **Redis Server:** `localhost:6379`

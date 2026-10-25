# 🏗️ KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)

> **Nguồn trích xuất**: PRD mục II, V, VII (Lược đồ Component, Deployment Diagram, ERD) và `Source/docker-compose.yml`.

---

## 1. Sơ Đồ Tổng Quan Kiến Trúc (Microservices Hướng 3)

```
                            [ Du khách (Mobile Web) ]     [ Quản trị viên (Admin) ]
                                        \                     /
                                         \                   /
                                  +-------------------------------+
                                  |      API Gateway (:8000)      |
                                  |   (Xác thực Token & Định tuyến)|
                                  +---------------+---------------+
                                                  |
         +------------------------+---------------+------------------------+
         |                        |                                        |
+--------v-------+       +--------v-------+                       +--------v-------+
|  auth-service  |       |   poi-service  |                       | chatbot-service|
|    (:8001)     |       |    (:8002)     |                       |    (:8003)     |
+--------+-------+       +--------+-------+                       +--------+-------+
         |                        |                                        |
   [Users & Pay]             [POIs & Locs]                            [FAQ Cache &
    & [Cash TTL]                  |                                  Vectors Store]
                                  | (Publish: poi.upserted)
                                  v
                         [Message Queue (RabbitMQ / DLQ)]
                                  | (Consume: 15 ngôn ngữ)
                                  v
                      +-----------------------+
                      | data-pipeline-service |
                      |        (:8004)        |
                      +-----------------------+
```

---

## 2. Danh Sách Các Services & Phân Bổ Cổng (Port Allocation)

| Dịch vụ / Thành phần | Cổng Port | Vai trò & Trách nhiệm chính | Cơ sở dữ liệu / Bộ nhớ |
| :--- | :--- | :--- | :--- |
| **API Gateway** | `8000` | Điểm vào duy nhất (Single Entry Point), định tuyến HTTPS, kiểm tra hợp lệ của JWT `access_token`, tổng hợp kiểm tra sức khỏe hệ thống (`/health`). | Không có DB riêng |
| **Authorization Service (`auth-service`)** | `8001` | Xác thực người dùng, tích hợp cổng thanh toán Payoo (online), sinh và kiểm tra mã vé tiền mặt dùng 1 lần (`shorted_code`), cấp phát JWT `access_token` (UC01). | `Auth & Payment DB` + `Redis Cache` |
| **Navigation & POI Service (`poi-service`)** | `8002` | Quản lý điểm tham quan (POIs), lộ trình (`TourRoutes`), bản dịch đa ngôn ngữ. Cung cấp API `GET /pois/all` tải một lần duy nhất (UC02). Đẩy sự kiện sang Message Queue khi Admin cập nhật mô tả (UC04). | `POI DB` |
| **Chatbot AI Service (`chatbot-service`)** | `8003` | Trợ lý ảo RAG hỏi đáp tri thức Chùa Linh Ứng. Tra cứu cache câu hỏi thường gặp trong Redis, tính toán độ tương đồng Cosine Similarity trên Vector DB, từ chối câu hỏi ngoài phạm vi (UC03). | `Vector DB` + `Redis FAQ Cache` |
| **Data Pipeline Service (`data-pipeline-service`)** | `8004` | Worker xử lý ngầm bất đồng bộ từ Message Queue. Dịch tự động sang 15+ ngôn ngữ, tổng hợp file âm thanh (TTS), cập nhật `poi_localizations` và nhúng vector tri thức mới (UC04). | Ghi vào `POI DB` & `Vector DB` |
| **Frontend Web & Admin** | `3000` | Giao diện du khách (Mobile Web Leaflet GPS Geofence) và Admin Dashboard (`/admin`). | Trình duyệt Client (`localStorage`) |
| **PostgreSQL** | `5432` | Hệ quản trị CSDL quan hệ chính cho `auth-service` và `poi-service`. | `gps_auth_db`, `gps_poi_db` |
| **Redis Cache** | `6379` | Bộ nhớ đệm tốc độ cao cho mã tiền mặt có TTL và cache câu hỏi FAQ. | Redis DB 0 / DB 1 |
| **RabbitMQ** | `5672` / `15672` | Message Broker trao đổi thông điệp bất đồng bộ (AMQP và Web UI Management). | Queue `poi.upserted`, DLQ `poi.dlq` |

---

## 3. Kiến Trúc Dữ Liệu: Database-Per-Service

Hệ thống tuân thủ chặt chẽ nguyên tắc mỗi microservice quản lý một cơ sở dữ liệu độc lập:

1. **Auth & Payment DB (`gps_auth_db`)**:
   - `Users`: Quản lý tài khoản (admin, staff, user), mật khẩu hash (`bcrypt`), vai trò (`role`).
   - `PaymentSessions`: Quản lý phiên giao dịch thanh toán (`session_id`, `auth_code`, `status`, `access_token`, `expires_at`).
2. **POI DB (`gps_poi_db`)**:
   - `POIs`: Bảng chính lưu điểm đến (`poi_id`, `name`, `latitude`, `longitude`, `trigger_radius`, `thumbnail_url`, `original_description`).
   - `POILocalizations`: Lưu bản dịch đa ngôn ngữ (`poi_id`, `language_code`, `translated_title`, `translated_description`, `audio_url`).
   - `TourRoutes` & `RoutePOIs`: Quản lý các tuyến đường tham quan đề xuất và thứ tự các điểm dừng (`step_order`).
3. **Redis Cache**:
   - `ShortCodeCache`: Lưu mã tiền mặt 10 ký tự tạm thời (`shorted_code` -> `auth_code`, `ttl_seconds`). Tự động xóa ngay sau khi đổi token lần đầu.
   - `ChatbotFAQCache`: Lưu kết quả câu hỏi thường gặp (`question_hash` -> `question_text`, `cached_answer`, `ttl_seconds`).
4. **Vector DB (`KnowledgeVectors`)**:
   - `vector_id`, `poi_id`, `chunk_text`, `embedding_vector` (vector số thực), `metadata_json`.

---

## 4. Cơ Chế Giao Tiếp Giữa Các Dịch Vụ

1. **Giao tiếp Đồng bộ (Synchronous HTTP/REST)**:
   - Client gọi vào `API Gateway:8000`.
   - Gateway xác thực JWT token qua `auth-service:8001` và chuyển tiếp đến các service đích (`poi-service:8002`, `chatbot-service:8003`).
2. **Giao tiếp Bất đồng bộ (Asynchronous Message Queue)**:
   - Khi Admin thêm hoặc chỉnh sửa mô tả POI tại `poi-service`, hệ thống phát sinh event `poi.upserted` vào RabbitMQ.
   - `data-pipeline-service` nhận event, chạy ngầm dịch 15 ngôn ngữ mà không block request của Admin.
   - Nếu xảy ra sự cố trong quá trình dịch thuật/TTS, hệ thống thực hiện retry tối đa 3 lần; nếu tiếp tục lỗi thì chuyển thông điệp vào **Dead-Letter Queue (`poi.dlq`)** để tránh mất dữ liệu.
3. **Cơ Chế Fallback Độc Lập Môi Trường (In-Memory Adapters)**:
   - Trong môi trường phát triển hoặc máy demo không có Docker daemon, hệ thống kích hoạt tự động các adapter nội bộ (`shared_cache`, `shared_queue`, `shared_vector_store`) để đảm bảo hệ thống vẫn khởi chạy trơn tru 100% bằng script `start.bat`.

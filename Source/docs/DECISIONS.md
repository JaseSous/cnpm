# TÀI LIỆU QUYẾT ĐỊNH KIẾN TRÚC (ARCHITECTURAL DECISIONS) - MVP GPS CHÙA LINH ỨNG

Tài liệu này ghi lại các quyết định kỹ thuật và kiến trúc theo yêu cầu: "Khi PRD mơ hồ, chọn phương án đơn giản nhất và ghi quyết định vào docs/DECISIONS.md thay vì hỏi lại."

---

## 1. Đơn Giản Hóa Hạ Tầng Cho MVP Báo Cáo Gấp
- **Bỏ MongoDB**: Chuyển `poi-service` sang sử dụng PostgreSQL (hoặc SQLite/Postgres với schema quan hệ chuẩn). Localizations lưu bảng `poi_localizations` và hỗ trợ JSONB. Lý do: Giảm số lượng database engine phức tạp (tránh tốn RAM của MongoDB), tăng tốc độ khởi chạy container mà vẫn đảm bảo tính độc lập cơ sở dữ liệu theo service (Auth DB và POI DB riêng biệt).
- **Bỏ Qdrant**: `chatbot-service` tự lưu trữ vector embeddings trong SQLite / JSON storage nội bộ, tính toán độ tương đồng Cosine Similarity bằng thuật toán Python/Numpy thuần túy với ngưỡng lọc tương đồng `SIMILARITY_THRESHOLD = 0.35`. Lý do: Bỏ bớt container Qdrant nặng hàng GB RAM, loại bỏ độ trễ khởi động vector engine độc lập, đảm bảo chạy ổn định 100% trong bài báo cáo.
- **Giữ nguyên các thành phần cốt lõi**:
  - PostgreSQL: Dành cho Auth Service (`gps_auth_db`) và POI Service (`gps_poi_db`).
  - Redis: Dành cho ShortCodeCache (mã tiền mặt có TTL) và ChatbotFAQCache (câu hỏi thường gặp).
  - RabbitMQ: Message Queue xử lý bất đồng bộ pipeline đa ngôn ngữ có Dead-Letter Queue (DLQ).
  - Fallback Offline/In-Memory Adapter: Cho phép toàn bộ logic chạy được ngay lập tức ở cả môi trường máy tính không có Docker daemon lẫn môi trường Docker Compose.

---

## 2. Phân Bổ Cổng (Port Allocation)
- **API Gateway (public)**: `http://localhost:8000`
- **Frontend (Web/Mobile-first client & admin)**: `http://localhost:3000`
- **Auth Service**: `http://localhost:8001`
- **POI Service**: `http://localhost:8002`
- **Chatbot Service**: `http://localhost:8003`
- **Data Pipeline Service**: `http://localhost:8004`
- **PostgreSQL**: `5432`
- **Redis**: `6379`
- **RabbitMQ**: `5672` (AMQP), `15672` (Management Dashboard)

---

## 3. Chiến Lược Xác Thực & Phân Quyền (UC01)
- **Mã tiền mặt (`shorted_code`)**: 10 ký tự ngẫu nhiên (chữ hoa + số), lưu trong Redis với TTL (mặc định 3600 giây). Khi du khách dùng mã này để xác thực qua `/auth/verify`, hệ thống kiểm tra, cấp `access_token` JWT và **xóa ngay lập tức khỏi Redis** để bảo đảm chỉ sử dụng 1 lần duy nhất.
- **Mã online Payoo (`auth_code`)**: Tạo phiên `payment_sessions` với trạng thái ban đầu là `Pending`. Du khách gọi `/auth/verify` nhận thông báo `{"status": "Pending", "message": "đang chờ xử lý"}` và client tự động retry sau mỗi 2 giây. Khi webhook giả lập được kích hoạt, trạng thái chuyển thành `Success`, lần gọi verify tiếp theo sẽ sinh JWT token.
- **Chuẩn hóa thông báo lỗi theo PRD**:
  - Mã rỗng hoặc sai định dạng: HTTP 400 `"Vui lòng nhập mã xác thực hợp lệ"`
  - Mã không tồn tại, đã dùng hoặc hết hạn: HTTP 401 `"Mã xác thực không hợp lệ hoặc đã hết hạn"`
- **API Gateway**: Mọi route trừ `/auth/*` đều xác thực token qua Auth Service. Nếu token không hợp lệ -> HTTP 401. Route `/admin/*` kiểm tra thêm claim `role == "admin"`.

---

## 4. Dữ Liệu Tải 1 Lần & Geofence (UC02)
- Endpoint `GET /pois/all`: Trả về toàn bộ dữ liệu 6 điểm tham quan, tuyến tham quan mẫu và toàn bộ 15 ngôn ngữ localizations.
- Client lưu trực tiếp vào trình duyệt (localStorage) và **tuyệt đối không gọi lại API POI** trong suốt hành trình tham quan.
- Khi người dùng di chuyển vào bán kính `trigger_radius` (mét) của POI: tự động kích hoạt phát âm thanh hoặc đọc Web Speech API.

---

## 5. Pipeline Bất Đồng Bộ Đa Ngôn Ngữ & Dead-Letter Queue (UC04)
- Khi Admin tạo/sửa POI:
  - Nếu `original_description` thay đổi: Lưu DB với trạng thái `pipeline_status = "Đang xử lý (0/15)"`, trả HTTP 200/201 ngay lập tức cho Admin, đồng thời phát event `poi.upserted` vào RabbitMQ.
  - **Ngoại lệ bắt buộc**: Nếu chỉ thay đổi tọa độ (`latitude`, `longitude`) hoặc bán kính (`trigger_radius`) mà mô tả gốc giữ nguyên, POI Service **không phát event** lên RabbitMQ.
- Worker `data-pipeline-service` consume event:
  - Dịch sang 15 ngôn ngữ cấu hình (`vi, en, zh, ja, ko, fr, de, es, ru, th, id, ms, it, pt, ar`).
  - Cập nhật tiến độ `pipeline_status` (ví dụ `"Đang xử lý (7/15)"` -> `"Hoàn tất"`).
  - Cập nhật tri thức bản dịch sang `chatbot-service`.
  - Nếu gặp lỗi ngoại vi: Thử lại (retry) tối đa 3 lần. Nếu vẫn lỗi -> nack và chuyển sang Dead-Letter Queue `poi.dlq`.

---

## 6. Chatbot RAG (UC03)
- Quy trình 7 bước:
  1. Chuẩn hóa câu hỏi & kiểm tra Redis Cache -> Nếu có, trả ngay với cờ `from_cache: true`.
  2. Tạo vector embedding cho câu hỏi.
  3. Tìm kiếm top-k Cosine Similarity trong cơ sở tri thức Chùa Linh Ứng.
  4. Nếu điểm tương đồng cao nhất < `SIMILARITY_THRESHOLD (0.35)`: Trả về chính xác câu:  
     *"Xin lỗi, tôi chỉ có thể giải đáp các thông tin liên quan đến khu di tích Chùa Linh Ứng"*.
  5. Nếu câu hỏi trong phạm vi: Ghép context và gọi LLM trả lời súc tích, chuẩn xác.
  6. Lưu câu trả lời vào Redis FAQ Cache.
  7. Trả kết quả về cho client với `from_cache: false`.
- Xử lý sự cố: Nếu có lỗi kết nối/timeout, trả thông điệp: *"Hệ thống trợ lý ảo đang bận, vui lòng thử lại sau giây lát"*.

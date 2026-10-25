# 🎯 QUY TẮC 2: TUÂN THỦ NGHIÊM NGẶT PRD (PRD COMPLIANCE)

> **Mục tiêu**: Bảo đảm tính toàn vẹn của đồ án theo đặc tả yêu cầu sản phẩm (PRD), không phát triển lệch hướng và không bỏ sót yêu cầu đánh giá của giảng viên.

---

## 1. PRD Là Nguồn Sự Thật Duy Nhất (Single Source of Truth)

- Tài liệu PRD (`Product Requirements Document (PRD).docx`) là căn cứ cao nhất cho mọi quyết định kỹ thuật và tính năng sản phẩm.
- Khi có sự khác biệt giữa giả định cá nhân và PRD, PRD luôn là chuẩn mực phải tuân theo.

---

## 2. Các Ràng Buộc Tuân Thủ Cụ Thể

1. **Khớp chính xác mã lỗi HTTP & Thông báo:**
   - Khi xử lý lỗi hoặc luồng rẽ nhánh, phải trả về chính xác mã HTTP và câu thông báo tiếng Việt theo PRD:
     - `UC01 E1`: HTTP 400 — `"Vui lòng nhập mã xác thực hợp lệ"`
     - `UC01 E2`: HTTP 401 — `"Mã xác thực không hợp lệ hoặc đã hết hạn"`
     - `UC01 A1`: HTTP 200 — Status `"Pending"`, message `"đang chờ xử lý"`
     - `UC02 E1`: HTTP 500 — `"Không thể tải dữ liệu bản đồ, vui lòng thử lại"`
     - `UC02 E2`: HTTP 200 — Danh sách `[]`, message `"Dữ liệu điểm tham quan đang được cập nhật"`
     - `UC03 E1`: Thông báo `"Hệ thống trợ lý ảo đang bận, vui lòng thử lại sau giây lát"`
     - `UC03 E2`: Phản hồi chuẩn `"Xin lỗi, tôi chỉ có thể giải đáp các thông tin liên quan đến khu di tích Chùa Linh Ứng"`
2. **Quy tắc luồng A1 trong UC04 (Bắt buộc):**
   - Khi Admin chỉ thay đổi tọa độ (`latitude`, `longitude`) hoặc bán kính (`trigger_radius`) mà không thay đổi mô tả gốc (`original_description`), hệ thống **TUYỆT ĐỐI KHÔNG** được gửi sự kiện vào Message Queue để dịch thuật lại.
3. **Cơ chế Tải 1 Lần trong UC02 (Bắt buộc):**
   - Frontend chỉ gọi API lấy danh sách POI đúng một lần duy nhất (`GET /pois/all`) sau khi xác thực. Toàn bộ logic hiển thị, chuyển ngôn ngữ và thuyết minh GPS sau đó phải chạy trên dữ liệu đã lưu trữ ở Client (`localStorage`).
4. **Không tự ý thêm hoặc bớt tính năng ngoài phạm vi:**
   - Không tự ý thêm các tính năng ngoài PRD (ví dụ: giỏ hàng, đặt phòng khách sạn, mạng xã hội...).
   - Không bỏ bớt các yêu cầu đã cam kết trong PRD (ví dụ: Dead-Letter Queue trong RabbitMQ, Redis FAQ Cache cho Chatbot).

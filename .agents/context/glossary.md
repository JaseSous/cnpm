# 📖 BẢNG THUẬT NGỮ DỰ ÁN (GLOSSARY)

> **Mục đích**: Chuẩn hóa thuật ngữ kỹ thuật và nghiệp vụ dùng chung giữa PRD, Codebase và AI Agents.

---

| Thuật ngữ | Tên đầy đủ / Ý nghĩa | Định nghĩa trong dự án |
| :--- | :--- | :--- |
| **POI** | Point of Interest | Điểm tham quan cụ thể (ví dụ: Tượng Phật Bà Quan Âm 67m, Tháp Xá Lợi, Cổng Tam Quan...). Chứa tọa độ GPS, bán kính kích hoạt và mô tả. |
| **Geofence** | Vùng địa lý ảo | Vùng tròn bán kính `trigger_radius` (tính bằng mét) xung quanh tọa độ của một POI. Khi du khách bước vào vùng này, hệ thống tự động kích hoạt thuyết minh. |
| **RAG** | Retrieval-Augmented Generation | Mô hình kết hợp truy xuất dữ liệu từ cơ sở tri thức (Vector DB) rồi đưa vào prompt của LLM để trả lời chính xác, tránh hiện tượng ảo giác (hallucination). |
| **Cosine Similarity** | Độ tương đồng Cosine | Phép đo toán học tính góc giữa 2 vector số thực biểu diễn ngữ nghĩa để tìm kiếm thông tin liên quan nhất với câu hỏi của du khách. |
| **SIMILARITY_THRESHOLD** | Ngưỡng tương đồng tối thiểu | Giá trị float (mặc định `0.35`). Nếu điểm tương đồng cao nhất nhỏ hơn ngưỡng này, chatbot xác định câu hỏi nằm ngoài phạm vi di tích và từ chối trả lời. |
| **Single-fetch / Tải 1 lần** | Cơ chế tải một lần | Chiến lược tải toàn bộ danh sách POIs và 15 ngôn ngữ về trình duyệt Client ngay sau khi xác thực vé, sau đó ngắt hoàn toàn việc gọi lại API này để tiết kiệm băng thông. |
| **access_token** | JSON Web Token (JWT) | Chuỗi token có chữ ký số chứa thông tin xác thực phiên người dùng, thời hạn hết hạn (`exp`) và vai trò (`role`). Bắt buộc gửi kèm mọi request bảo mật. |
| **auth_code** | Mã xác thực giao dịch Online | Mã định danh phiên thanh toán trực tuyến do cổng thanh toán (Payoo) sinh ra, trạng thái ban đầu là `Pending`. |
| **shorted_code** | Mã vé tiền mặt ngắn hạn | Chuỗi ký tự ngẫu nhiên (10 ký tự chữ và số) cấp cho khách mua vé tiền mặt tại quầy, lưu trong Redis với TTL và chỉ đổi lấy token được đúng 1 lần. |
| **TTL** | Time-To-Live | Thời gian sống (tính bằng giây) của một bản ghi trong bộ nhớ đệm Redis (ví dụ: thời hạn của mã vé tiền mặt chưa đổi). |
| **DLQ** | Dead-Letter Queue | Hàng đợi chứa các thông điệp lỗi hoặc quá số lần thử lại (retry) trong Message Queue (RabbitMQ `poi.dlq`), phục vụ mục đích kiểm tra và xử lý lại thủ công. |
| **Database-per-service** | CSDL riêng cho từng dịch vụ | Nguyên tắc thiết kế microservices trong đó mỗi service sở hữu và toàn quyền quản lý CSDL của riêng mình, không service nào được truy cập trực tiếp DB của service khác. |

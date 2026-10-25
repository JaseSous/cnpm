# 🛑 QUY TẮC 4: KHÔNG TỰ SUY DIỄN & HỎI LẠI KHI CHƯA RÕ

> **Mục tiêu**: Ngăn ngừa hiện tượng ảo giác (hallucination), bịa đặt thông số kỹ thuật hoặc tự tiện quyết định các điểm nghiệp vụ quan trọng.

---

## 1. Nguyên Tắc "Không Giả Định" (Zero Assumption Principle)

- Nếu một thông tin, một API key, một endpoint bên thứ ba, hoặc một yêu cầu nghiệp vụ **không xuất hiện trong PRD, ảnh chụp giảng viên hoặc codebase**:
  - **TUYỆT ĐỐI KHÔNG** tự bịa đặt thông tin hoặc tự chọn phương án giả lập rồi xem như đã hoàn thành.
  - **BẮT BUỘC PHẢI** dừng lại, tổng hợp câu hỏi ngắn gọn và đưa vào danh sách cần người dùng xác nhận.

---

## 2. Các Tình Huống Cần Dừng Lại Hỏi Người Dùng

1. **Khóa truy cập hoặc tài khoản tích hợp bên ngoài:**
   - Ví dụ: Cổng thanh toán Payoo (Sandbox hay Mock?), OpenAI API Key / Azure OpenAI (có key thật không hay dùng mock?), Google Cloud Translate API.
2. **Mâu thuẫn giữa các tài liệu:**
   - Ví dụ: Ảnh bảng của giảng viên yêu cầu React Native (Mobile App) nhưng PRD và Codebase chỉ có Web App (React + Vite). Cần hỏi xác nhận trước khi quyết định viết thêm codebase Mobile.
3. **Thay đổi cấu trúc cơ sở dữ liệu lớn:**
   - Xóa bảng, đổi tên trường dữ liệu trong các bảng đã có (`Users`, `POIs`, `PaymentSessions`) bắt buộc phải được người dùng phê duyệt trước khi chạy migration.
4. **Quyết định hạ tầng:**
   - Việc chuyển đổi giữa container thật (RabbitMQ, Postgres, Redis) và In-Memory Mock Adapter khi chạy CI/CD hoặc demo.

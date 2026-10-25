# 📌 TỔNG QUAN DỰ ÁN (PROJECT OVERVIEW)

> **Nguồn trích xuất**: PRD (`Product Requirements Document (PRD).docx`), Ảnh đính kèm từ lớp học, và codebase thực tế.

---

## 1. Thông Tin Chung

- **Tên học phần:** Công nghệ phần mềm
- **Cơ sở đào tạo:** Khoa Công nghệ Thông tin — Trường Đại học Sài Gòn (SGU)
- **Giảng viên giảng dạy:** ThS. Nguyễn Quốc Huy
- **Nhóm sinh viên thực hiện:**
  - Nguyễn Mạnh Thắng — MSSV: `3124411283`
  - Phạm Minh Khôi — MSSV: `3124411135`
  - Trương Thuận Phú — MSSV: `3124411234`
- **Thời gian lập PRD:** Tháng 10 năm 2026

---

## 2. Đề Tài & Địa Điểm Triển Khai Thực Tế

- **Tên đề tài:** Ứng dụng Thuyết minh tự động đa ngôn ngữ
- **Địa điểm thử nghiệm:** Khu du tích **Chùa Linh Ứng** (Bán đảo Sơn Trà, Đà Nẵng).
- **Đối tượng người dùng:**
  - **Du khách tham quan (Customer):** Khách du lịch trong nước và quốc tế trải nghiệm thuyết minh tự động qua điện thoại thông minh theo tọa độ GPS và hỏi đáp trợ lý ảo.
  - **Quản trị viên / Nhân viên (Admin / Staff):** Quản lý danh mục điểm tham quan (POI), theo dõi tiến độ dịch thuật ngầm và tạo mã vé tiền mặt.

---

## 3. Vấn Đề Thực Tế Cần Giải Quyết (Problem Alignment)

1. **Thiếu hỗ trợ đa ngôn ngữ cá nhân hóa:** Du khách quốc tế tham quan Chùa Linh Ứng thiếu sự hướng dẫn bằng ngôn ngữ ưa thích, không có hướng dẫn viên hoặc tài liệu đầy đủ và thiếu kênh giải đáp thắc mắc tức thời.
2. **Hạn chế mở rộng của kiến trúc truyền thống:** Các hệ thống Monolithic truyền thống dễ rơi vào tình trạng quá tải hoặc nghẽn cổ chai khi lượng khách đông, hoặc khi máy chủ phải gánh các tác vụ tốn tài nguyên như dịch thuật tự động 15+ ngôn ngữ và tổng hợp giọng nói (Text-to-Speech). Điều này dẫn đến phản hồi chậm trễ và ảnh hưởng nghiêm trọng đến trải nghiệm du khách.

---

## 4. Hướng Triển Khai Nhóm Đã Chọn

Theo yêu cầu môn học được giảng viên ghi trên bảng (gồm 3 đề tài riêng biệt):
- **Đề tài nhóm chọn: Hướng 3** — **BE Dev Tạo các services giao tiếp với nhau bao gồm CD/CI**.
- **Phạm vi giao diện:** Nhóm chỉ phát triển **Web App** (React + Vite + TypeScript, giao diện responsive mobile-first tối ưu cho trình duyệt điện thoại du khách).
- **Lưu ý phạm vi:** Mục *"1. FE DEV (React Native + React.js)"* trên bảng là một đề tài riêng biệt khác của nhóm khác, nhóm **không** chọn và **không** triển khai ứng dụng di động React Native.
- **Mục tiêu trước mắt:** Đảm bảo toàn bộ luồng demo từ UC01 đến UC04 chạy mượt mà, ổn định phục vụ các đợt kiểm tra và báo cáo.

---

## 5. Mục Tiêu Cốt Lõi Của Hệ Thống (Goals)

1. **Kiến trúc phân tán:** Tách biệt hệ thống thành các Microservices độc lập, mỗi service sở hữu cơ sở dữ liệu riêng (Database-per-service).
2. **Giao tiếp liên dịch vụ linh hoạt:** Thiết lập luồng giao tiếp đồng bộ (HTTP/REST) qua API Gateway và luồng giao tiếp bất đồng bộ qua Message Queue (RabbitMQ) cho các tác vụ nặng.
3. **Hiệu suất cao (Cơ chế Tải 1 Lần):** Thiết lập cơ chế nạp toàn bộ dữ liệu điểm đến (POIs) và dữ liệu bản dịch cho Client chỉ trong một lượt tải duy nhất (`GET /pois/all`) để tối ưu băng thông và giảm tải cho backend.
4. **Hỏi đáp thông minh (RAG AI):** Tích hợp trợ lý ảo tìm kiếm ngữ cảnh dựa trên tri thức thực tế của Chùa Linh Ứng, kết hợp bộ nhớ đệm Redis FAQ Cache để giảm độ trễ và chi phí.
5. **Tự động hóa CI/CD:** Chuẩn hóa quy trình kiểm thử tự động (Unit Test với pytest) và build container Docker bằng GitHub Actions.

---

## 6. Các Mốc Đánh Giá Quan Trọng

- **Tuần 7:** Kiểm tra tiến độ giữa kỳ với giảng viên.
- **Tuần 11 – 12:** Báo cáo đồ án môn học cuối kỳ.
- **Kênh giao tiếp nhóm:** Toàn bộ mã nguồn, tài liệu và trao đổi tiến độ thông qua Git / GitHub.

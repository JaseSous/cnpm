# 🔍 QUY TẮC 3: XEM LẠI CODEBASE & GIT LOG TRƯỚC KHI THAY ĐỔI LỚN

> **Mục tiêu**: Tránh phá vỡ kiến trúc đã có, tránh viết mã trùng lặp và bảo đảm khả năng tương thích cao nhất với toàn bộ hệ thống.

---

## 1. Quy Trình Khảo Sát Trước Khi Thực Hiện

Trước khi bắt tay vào tạo một service mới, chỉnh sửa API Gateway, hoặc tái cấu trúc cơ sở dữ liệu:

1. **Kiểm tra cấu trúc thư mục hiện hành:**
   - Xem xét thư mục `Source/` để hiểu vị trí các service, frontend, scripts và tests.
2. **Đọc mã nguồn hiện có (Existing Patterns):**
   - Đọc các module dùng chung trong `Source/shared/` (adapters, queue, cache, vector store) để tái sử dụng logic sẵn có thay vì viết mới từ đầu.
   - Tham khảo cách viết endpoint, Pydantic schemas, và cách xử lý exception trong các service hiện hữu (`auth-service`, `poi-service`).
3. **Đọc lịch sử Commit (`git log`):**
   - Chạy lệnh `git log -n 5` hoặc `git log --oneline -n 10` để xem các thành viên khác trong nhóm hoặc các Agent trước đó đã làm gì gần đây.
   - Đọc tài liệu quyết định kiến trúc tại `Source/docs/DECISIONS.md` để nắm các điều chỉnh kỹ thuật đã thống nhất (ví dụ: lý do thay thế MongoDB/Qdrant bằng PostgreSQL/SQLite in-memory cho bản demo).
4. **Kiểm tra trạng thái Git trước khi viết code:**
   - Chạy `git status` để bảo đảm cây thư mục làm việc đang sạch (clean working tree). Không bắt đầu chỉnh sửa mới trên một workspace đang có xung đột dở dang.

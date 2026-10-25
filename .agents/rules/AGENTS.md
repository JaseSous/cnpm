# 📜 QUY TẮC BẮT BUỘC DÀNH CHO AI AGENT (RULES OF ENGAGEMENT)

> **Phạm vi áp dụng:** Mọi AI Agent tham gia đọc, viết mã nguồn, kiểm thử hoặc sửa đổi tài liệu trong kho lưu trữ này đều bắt buộc phải tuân thủ 100% các quy tắc dưới đây.

---

## 1. Commit Liên Tục & Nguyên Tử (Atomic Commits)
- **Luôn commit ngay sau mỗi thay đổi logic hoặc tài liệu có ý nghĩa.** Không gộp nhiều thay đổi không liên quan vào chung một commit lớn.
- **Tuân thủ chuẩn Conventional Commits:**
  - `feat:` Tính năng mới bám sát PRD.
  - `fix:` Sửa lỗi logic, sửa bug phản hồi mã lỗi HTTP.
  - `docs:` Thêm/sửa tài liệu hoặc comment.
  - `refactor:` Tái cấu trúc mã nguồn không làm thay đổi hành vi nghiệp vụ.
  - `test:` Bổ sung hoặc chỉnh sửa unit test/integration test.
  - `chore:` Tác vụ cấu hình, dọn dẹp môi trường, khởi tạo thư mục.
  - `ci:` Cập nhật workflow GitHub Actions hoặc cấu hình Docker.
- *Xem hướng dẫn chi tiết tại:* [01_git_commit_rules.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/rules/01_git_commit_rules.md)

---

## 2. Tuyệt Đối Tuân Thủ PRD (Strict PRD Compliance)
- **PRD (`Product Requirements Document (PRD).docx`) là nguồn sự thật tối cao (Source of Truth).**
- Mọi API endpoint, mã trạng thái HTTP (200, 400, 401, 500), câu thông báo lỗi bằng tiếng Việt (ví dụ: *"Vui lòng nhập mã xác thực hợp lệ"*, *"Xin lỗi, tôi chỉ có thể giải đáp các thông tin liên quan đến khu di tích Chùa Linh Ứng"*) phải khớp 100% với PRD.
- **Tuyệt đối không tự ý thêm hoặc bớt tính năng ngoài phạm vi PRD** nếu chưa có yêu cầu rõ ràng từ người dùng.
- *Xem hướng dẫn chi tiết tại:* [02_prd_compliance.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/rules/02_prd_compliance.md)

---

## 3. Xem Lại Codebase & Git Log Trước Khi Thay Đổi Lớn (Pre-Change Review)
- Trước khi tạo file mới, sửa đổi kiến trúc, hoặc thay đổi service hiện có:
  1. Phải quét cấu trúc thư mục liên quan.
  2. Đọc mã nguồn hiện tại để kế thừa các pattern đã thiết lập (adapters, database schema, shared logic).
  3. Kiểm tra lịch sử commit gần nhất (`git log -n 5`) để hiểu ngữ cảnh những thay đổi gần đây, tránh xung đột và trùng lặp mã.
- *Xem hướng dẫn chi tiết tại:* [03_codebase_review.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/rules/03_codebase_review.md)

---

## 4. Không Tự Suy Diễn & Luôn Xác Nhận Khi Chưa Rõ (Zero Hallucination)
- **Cấm tự ý suy đoán yêu cầu kỹ thuật hoặc nghiệp vụ chưa được định nghĩa trong PRD.**
- Khi phát hiện điểm mâu thuẫn, thiếu sót hoặc mơ hồ giữa PRD và codebase, Agent **phải dừng lại và đặt câu hỏi làm rõ với người dùng** thay vì tự tiện đưa ra quyết định giả định.
- Giữ vững tính trung thực về hiện trạng hệ thống: nếu test lỗi hoặc thiếu thư viện, báo cáo chính xác nguyên nhân, không che giấu lỗi.
- *Xem hướng dẫn chi tiết tại:* [04_no_assumptions.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/rules/04_no_assumptions.md)

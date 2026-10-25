# 📝 QUY TẮC 1: COMMIT LIÊN TỤC & CONVENTIONAL COMMITS

> **Mục tiêu**: Đảm bảo lịch sử Git rõ ràng, minh bạch, dễ truy vết và phản ánh từng bước tiến độ nhỏ của dự án.

---

## 1. Nguyên Tắc Commit Liên Tục (Continuous Committing)
- **Không để dồn thay đổi:** Sau khi hoàn thành một chỉnh sửa logic nhỏ, một hàm kiểm thử, hoặc cập nhật tài liệu, phải commit ngay lên Git.
- **Tính nguyên tử (Atomic Commit):** Mỗi commit chỉ nên tập trung vào MỘT mục đích duy nhất. Tránh gộp chung việc sửa bug backend với cập nhật giao diện frontend vào cùng một commit.
- **Kiểm tra trạng thái trước khi commit:**
  - Luôn chạy `git status` và `git diff` để kiểm tra chính xác các file đã thay đổi.
  - Không commit các file tạm, file log, thư mục virtual environment (`venv/`), hoặc binary SQLite phát sinh ngoài ý muốn.

---

## 2. Định Dạng Conventional Commits Bắt Buộc

Cấu trúc message commit:
```
<type>(<scope>): <mô tả ngắn bằng tiếng Việt>
```

### Bảng các `type` được phép sử dụng:
| Type | Khi nào sử dụng | Ví dụ |
| :--- | :--- | :--- |
| `feat` | Thêm tính năng mới theo PRD | `feat(auth): thêm logic kiểm tra mã shorted_code từ redis` |
| `fix` | Sửa lỗi logic, sửa mã lỗi HTTP sai | `fix(poi): trả về danh sách rỗng thay vì null khi poi db trống` |
| `docs` | Thêm hoặc cập nhật tài liệu | `docs(agents): bổ sung ngữ cảnh kiến trúc microservices` |
| `refactor` | Tái cấu trúc code (không đổi tính năng) | `refactor(gateway): tách logic xác thực jwt thành middleware` |
| `test` | Thêm hoặc sửa test cases | `test(uc03): thêm test case kiểm tra ngoại lệ câu hỏi ngoài lề` |
| `chore` | Cấu hình, khởi tạo thư mục, việc vặt | `chore: khởi tạo thư mục .agents cho ngữ cảnh và quy tắc agent` |
| `ci` | Thay đổi pipeline CI/CD | `ci(github): thêm bước chạy backend unit test trên ubuntu` |
| `perf` | Tối ưu hóa hiệu năng hệ thống | `perf(poi): tối ưu thời gian phản hồi endpoint /pois/all` |

### Quy định về `<scope>`:
- Nêu rõ module hoặc service bị tác động: `(auth)`, `(poi)`, `(chatbot)`, `(pipeline)`, `(gateway)`, `(frontend)`, `(ci)`, `(agents)`, `(db)`. Nếu thay đổi toàn cục thì có thể bỏ qua scope.
- Mô tả viết ngắn gọn, súc tích bằng tiếng Việt, viết chữ thường, không kết thúc bằng dấu chấm.

---
name: git-commit
description: Hướng dẫn quy trình tạo git commit vi mô, liên tục và chuẩn hóa theo Conventional Commits.
---

# 📦 SKILL: QUY TRÌNH TẠO GIT COMMIT CHUẨN

Skill này hướng dẫn các bước thực hiện commit an toàn, chuẩn xác và đúng quy ước Conventional Commits cho mọi tác vụ trong dự án.

---

## Bước 1: Kiểm Tra Trạng Thái Thay Đổi (Diff Review)

Trước khi thêm file vào stage, luôn chạy:

```bash
git status
```
và kiểm tra chi tiết nội dung đã thay đổi:
```bash
git diff
```

**Nguyên tắc quan trọng:**
- Không stage các file không liên quan hoặc file sinh tự động (`__pycache__`, `.pytest_cache`, thư viện `node_modules`, file DB nhị phân thay đổi ngẫu nhiên).
- Nếu chỉ muốn commit một nhóm file cụ thể, dùng `git add <đường-dẫn-file>` thay vì `git add .` bừa bãi.

---

## Bước 2: Chọn Type & Scope Phù Hợp

Cấu trúc:
```
<type>(<scope>): <mô tả ngắn bằng tiếng Việt>
```

- **Types thông dụng:**
  - `feat`: Tính năng mới theo PRD.
  - `fix`: Sửa lỗi logic, sửa mã lỗi HTTP.
  - `docs`: Cập nhật tài liệu (`README`, PRD, `.agents`).
  - `refactor`: Tái cấu trúc mã nguồn không đổi hành vi.
  - `test`: Viết thêm hoặc sửa unit test.
  - `chore`: Việc bảo trì, cấu hình, dọn dẹp.
  - `ci`: Thay đổi cấu hình CI/CD GitHub Actions.
- **Scope gợi ý:**
  - `auth`, `poi`, `chatbot`, `pipeline`, `gateway`, `frontend`, `ci`, `agents`.

---

## Bước 3: Thực Hiện Lệnh Commit

Chạy lệnh commit với thông điệp rõ ràng:

```bash
git add <các file đã chọn>
git commit -m "<type>(<scope>): <mô tả ngắn>"
```

*Ví dụ thực tế:*
```bash
git commit -m "feat(auth): thêm logic đối chiếu mã shorted_code từ redis"
git commit -m "fix(poi): sửa ngoại lệ 500 khi mất kết nối poi db"
git commit -m "chore: khởi tạo thư mục .agents cho ngữ cảnh và quy tắc agent"
```

---

## Bước 4: Xác Nhận Commit Đã Tạo

Sau khi commit, kiểm tra lại bằng lệnh:

```bash
git log -n 1 --stat
```
Đảm bảo message hiển thị đúng, file được commit chính xác và không sót file thừa.

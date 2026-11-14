# DANH SÁCH THÀNH VIÊN VÀ CẤU HÌNH GIT (TEAM MEMBERS & GIT ROTATION)

Dự án gồm 3 thành viên thực hiện đồ án môn học Công nghệ phần mềm:

| STT | Họ và tên | Mã số sinh viên (MSSV) | Email Git | Vai trò định hướng kỹ thuật |
| :---: | :--- | :---: | :--- | :--- |
| 1 | **Nguyễn Mạnh Thắng** | 3124411283 | `jasesous@gmail.com` | Authorization Service, Auth Client App (QR & Token), CI/CD |
| 2 | **Phạm Minh Khôi** | 3124411135 | `phamkhoi944@gmail.com` | Navigation & POI Service, Admin Dashboard, Redis Cache |
| 3 | **Trương Thuận Phú** | 3124411234 | `thuanphutruong1234@gmail.com` | Chatbot AI Service, Data Pipeline Service, Vector DB & MQ |

---

## 1. Lệnh cấu hình Git trước khi commit

Trước khi chạy lệnh `git commit`, agent hãy chạy 1 trong 3 cụm lệnh tương ứng với thành viên được phân bổ:

### Thành viên 1: Nguyễn Mạnh Thắng
```powershell
git config user.name "Nguyễn Mạnh Thắng"
git config user.email "jasesous@gmail.com"
```

### Thành viên 2: Phạm Minh Khôi
```powershell
git config user.name "Phạm Minh Khôi"
git config user.email "phamkhoi944@gmail.com"
```

### Thành viên 3: Trương Thuận Phú
```powershell
git config user.name "Trương Thuận Phú"
git config user.email "thuanphutruong1234@gmail.com"
```

---

## 2. Quy tắc luân chuyển commit (Commit Rotation Matrix)

Để đảm bảo số lượng commit chia đều và hợp lý cho cả 3 thành viên trên GitHub Insights:
1. **Kiểm tra tác giả commit gần nhất:**
   ```powershell
   git log -1 --pretty=format:"%an <%ae>"
   ```
2. **Luân phiên theo vòng:**
   - Nếu commit trước là **Nguyễn Mạnh Thắng** -> Commit tiếp theo đổi sang **Phạm Minh Khôi**.
   - Nếu commit trước là **Phạm Minh Khôi** -> Commit tiếp theo đổi sang **Trương Thuận Phú**.
   - Nếu commit trước là **Trương Thuận Phú** -> Commit tiếp theo đổi sang **Nguyễn Mạnh Thắng**.
3. **Hoặc theo ngữ cảnh chức năng chuyên sâu:**
   - Các commit liên quan đến xác thực, login, sinh token, QR code, GitHub Actions workflow -> Ưu tiên gán `Nguyễn Mạnh Thắng`.
   - Các commit liên quan đến dữ liệu POI, bản đồ, CRUD POI, ngôn ngữ, cache phiên bản `data_version` -> Ưu tiên gán `Phạm Minh Khôi`.
   - Các commit liên quan đến Chatbot AI, Embedding RAG, Data Pipeline (dịch thuật đa ngôn ngữ & Text-to-Speech), xử lý hàng đợi RabbitMQ -> Ưu tiên gán `Trương Thuận Phú`.

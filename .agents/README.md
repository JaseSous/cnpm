# THƯ MỤC CẤU HÌNH VÀ CHỈ DẪN DÀNH CHO AI AGENTS (`.agents/`)

Chào mừng các AI Agents tham gia phát triển dự án đồ án môn học Công nghệ phần mềm:
**"Trang web ứng dụng thuyết minh tự động đa ngôn ngữ cho Chùa Linh Ứng (Frontend và Backend microservice) có CI/CD"**.

Thư mục `.agents/` này được thiết lập nhằm cung cấp toàn diện ngữ cảnh, quy tắc phát triển, lược đồ cơ sở dữ liệu, kiến trúc kỹ thuật và thông tin thành viên nhằm đảm bảo tính nhất quán tuyệt đối giữa tài liệu PRD và mã nguồn thực tế.

---

## 1. CẤU TRÚC THƯ MỤC `.agents/`

```text
.agents/
├── README.md                      # [Tài liệu này] Chỉ dẫn tổng quan và điều hướng cho AI Agents
├── RULES.md                       # Quy tắc cốt lõi: Conventional Commits, đổi tác giả git, strict PRD
├── MEMBERS.md                     # Danh sách 3 thành viên, email, MSSV và lệnh đổi git config
├── PROJECT_CONTEXT.md             # Tóm tắt bối cảnh Chùa Linh Ứng, mục tiêu, giải pháp và 12 Use Cases
├── DATABASE_SCHEMA.md             # Đặc tả chi tiết 100% các Database, bảng, cột, khóa theo đúng ERD
├── ARCHITECTURE.md                # Thiết kế kiến trúc Microservices, Gateway, Web Apps, MQ, CI/CD
├── IMPLEMENTATION_PLAN.md         # Bản kế hoạch thực hiện chi tiết 8 Phase (ĐÃ DUYỆT)
├── PRD.md                         # Toàn văn tài liệu PRD định dạng Markdown (đầy đủ 12 Use Cases)
├── Product Requirements Document (PRD).docx  # Bản gốc tài liệu PRD dạng Word
└── diagrams/                      # Thư mục chứa toàn bộ 36 lược đồ/sơ đồ trích xuất từ PRD
    ├── erd_overview.png           # Lược đồ quan hệ thực thể (ERD) tổng quan hệ thống
    ├── component_diagram.png      # Lược đồ phân rã Component
    ├── deployment_diagram.png     # Lược đồ Triển khai hạ tầng Cloud & Microservices
    ├── system_usecase_diagram.png # Sơ đồ Use Case tổng quan
    ├── dfd_level_0.png .. 2_5.png # Các mức sơ đồ luồng dữ liệu (DFD)
    └── uc01_.._uc12_..diagram.png # Use Case và Activity Diagrams chi tiết cho từng UC
```

---

## 2. QUY TRÌNH LÀM VIỆC DÀNH CHO AI AGENTS

Mỗi khi nhận nhiệm vụ hoặc triển khai code mới, AI Agent **BẮT BUỘC** phải tuân theo 4 bước sau:

### Bước 1: Đọc và nắm vững yêu cầu
1. Đọc [PROJECT_CONTEXT.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/PROJECT_CONTEXT.md) và Use Case liên quan trong [PRD.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/PRD.md).
2. Tra cứu cấu trúc dữ liệu chính xác tại [DATABASE_SCHEMA.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/DATABASE_SCHEMA.md). **Không tự ý thêm bớt cột hay đổi kiểu dữ liệu.**
3. Bám sát kế hoạch triển khai chi tiết từng Phase tại [IMPLEMENTATION_PLAN.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/IMPLEMENTATION_PLAN.md).

### Bước 2: Xác nhận nếu có thắc mắc
- Nếu có bất kỳ điều gì ngoài PRD hoặc có sự không rõ ràng, **DỪNG LẠI và hỏi người dùng để được phê duyệt**. Tuyệt đối không tự suy đoán (No hallucination).

### Bước 3: Hướng dẫn thiết lập môi trường & dịch vụ bên ngoài (nếu có)
- Khi cần tích hợp bất kỳ dịch vụ bên ngoài (Google Gemini API, Redis, Vector DB, RabbitMQ, Supabase Storage, Docker, Cloud hosting...), AI Agent **phải hướng dẫn chi tiết từng bước** cho người dùng thực hiện: link đăng ký, thao tác lấy key, file mẫu `.env.example`, và script/lệnh kiểm tra kết nối.

### Bước 4: Triển khai mã nguồn
- Viết mã nguồn theo đúng kiến trúc microservices trong [ARCHITECTURE.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/ARCHITECTURE.md).
- Đảm bảo mã nguồn bám sát các ràng buộc kỹ thuật (Idempotency, Outbox pattern, JWT auth, Redis TTL atomic operations).

### Bước 5: Commit lên Git theo đúng quy chuẩn
1. Luân chuyển tác giả git hợp lý cho 3 thành viên theo hướng dẫn tại [MEMBERS.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/MEMBERS.md):
   ```powershell
   git config user.name "<Tên thành viên>"
   git config user.email "<Email thành viên>"
   ```
2. Commit với thông điệp theo chuẩn Conventional Commits quy định tại [RULES.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/RULES.md):
   ```powershell
   git add <files>
   git commit -m "<type>(<scope>): <mô tả thay đổi>"
   ```

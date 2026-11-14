# QUY TẮC PHÁT TRIỂN DÀNH CHO AI AGENTS (DEVELOPMENT RULES)

Tài liệu này là **QUY CHUẨN BẮT BUỘC** áp dụng cho tất cả các AI Agents tham gia hỗ trợ, viết mã nguồn, thiết kế kiến trúc và triển khai dự án **"Trang web ứng dụng thuyết minh tự động đa ngôn ngữ cho Chùa Linh Ứng"**.

---

## 1. NGUYÊN TẮC VÀNG #1: TUÂN THỦ TUYỆT ĐỐI PRD VÀ DATABASE SCHEMA

1. **Tuyệt đối không tự ý thay đổi, thêm, bớt hoặc đổi tên:**
   - Số lượng Database: Chuẩn xác 2 Relational Database (Auth & Payment DB, POI DB), 1 Redis Cache Server (2 Logical DB tách biệt), 1 Vector DB, và 1 File Storage Bucket.
   - Tên bảng: Đúng 100% từng ký tự như trong PRD/ERD (ví dụ: `Users`, `TicketPackages`, `LoginAttempts`, `PaymentSessions`, `SupportedLanguages`, `SystemMetadata`, `POIs`, `POILocalizations`, `OutboxEvents`, `ProcessedEvents`, `PipelineAlerts`).
   - Tên cột, kiểu dữ liệu, ràng buộc khóa chính/khóa ngoại, giá trị mặc định: Phải đối chiếu và khớp chính xác tuyệt đối với [DATABASE_SCHEMA.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/DATABASE_SCHEMA.md).
2. **Quyết định phát sinh ngoài PRD:**
   - Bất kỳ thay đổi, cải tiến kiến trúc, thư viện bổ sung hoặc cấu hình nằm ngoài phạm vi đã ghi trong PRD **BẮT BUỘC PHẢI HỎI VÀ ĐƯỢC NGƯỜI DÙNG DUYỆT** trước khi tạo file hoặc sửa code.

---

## 2. NGUYÊN TẮC VÀNG #2: KHÔNG BỊA ĐẶT, KHÔNG ĐOÁN MÒ (NO HALLUCINATION)

1. Nếu gặp bất kỳ chi tiết nào mơ hồ, không rõ ràng, xung đột giữa các phần hoặc chưa được định nghĩa trong PRD:
   - **DỪNG LẠI NGAY LẬP TỨC**.
   - Trình bày rõ ràng vấn đề, các phương án khả thi và yêu cầu người dùng xác nhận / phê duyệt.
2. Không tự suy diễn các yêu cầu nghiệp vụ của Chùa Linh Ứng hoặc các logic xác thực, thanh toán ngoài phạm vi tài liệu.

---

## 3. NGUYÊN TẮC VÀNG #3: QUY CHUẨN COMMIT VÀ PHÂN BỔ TÁC GIẢ (GIT CONVENTION & AUTHOR ROTATION)

### 3.1. Thời điểm commit
- Commit ngay sau khi hoàn thành một chức năng, sửa xong một lỗi, cập nhật xong một tài liệu hoặc cấu hình một module.
- Không dồn nhiều tính năng khác nhau vào một commit lớn.

### 3.2. Định dạng Commit Message (Conventional Commits)
Tất cả các commit message phải tuân thủ nghiêm ngặt chuẩn Conventional Commits theo cấu trúc:
```text
<type>(<scope>): <mô tả ngắn gọn, súc tích bằng tiếng Việt hoặc tiếng Anh>
```
Các `type` được phép sử dụng:
- `feat`: Tính năng mới (ví dụ: `feat(auth): thêm API đổi shorted_code lấy JWT token`)
- `fix`: Sửa lỗi (ví dụ: `fix(poi): sửa lỗi tính khoảng cách Haversine khi GPS bị lệch`)
- `docs`: Thêm hoặc cập nhật tài liệu (ví dụ: `docs(agents): hoàn thiện quy tắc và schema database`)
- `style`: Định dạng code, dấu chấm phẩy, khoảng trắng, không ảnh hưởng logic
- `refactor`: Tái cấu trúc code (không thêm tính năng, không sửa lỗi)
- `perf`: Tối ưu hóa hiệu năng
- `test`: Viết thêm hoặc sửa unit test, integration test
- `chore`: Cấu hình build tool, package dependency, dọn dẹp repo
- `ci`: Cấu hình CI/CD, GitHub Actions workflows

### 3.3. Phân bổ commit đều và hợp lý cho 3 thành viên
Nhóm thực hiện gồm có 3 thành viên:
1. **Nguyễn Mạnh Thắng** | `jasesous@gmail.com`
2. **Phạm Minh Khôi** | `phamkhoi944@gmail.com`
3. **Trương Thuận Phú** | `thuanphutruong1234@gmail.com`

**CÁCH THỰC HIỆN:**
Trước khi thực hiện lệnh `git commit`, AI Agent **BẮT BUỘC** phải đổi thông tin tác giả trong git config:
```powershell
git config user.name "<Tên tác giả>"
git config user.email "<Email tác giả>"
```

**Cơ chế chia lượt commit (Xoay vòng Round-Robin hoặc theo phân vùng phụ trách):**
- Đảm bảo lịch sử commit cuối cùng phản ánh sự đóng góp cân bằng giữa cả 3 thành viên (số lượng commit xấp xỉ nhau).
- Có thể phân chia theo module/service hợp lý, ví dụ:
  - **Nguyễn Mạnh Thắng**: Authorization Service, Client App (Auth/QR flow), CI/CD.
  - **Phạm Minh Khôi**: Navigation & POI Service, Admin Dashboard (POI CRUD), Redis Cache.
  - **Trương Thuận Phú**: Chatbot AI Service, Data Pipeline Service, Vector DB & Message Queue.
- Khi làm các tác vụ chung (setup, refactor, tài liệu, test), áp dụng luân phiên theo thứ tự: Thắng -> Khôi -> Phú -> Thắng...

---

## 4. QUY TẮC KIẾN TRÚC VÀ CODEBASE

1. **Microservices độc lập (Database-per-service):**
   - Mỗi backend service sở hữu cơ sở dữ liệu riêng. Tuyệt đối không để một service này truy vấn hoặc chỉnh sửa trực tiếp database của service khác (ngoại trừ qua API/gRPC hoặc Message Broker).
   - `Data Pipeline Service` không ghi trực tiếp vào `POI DB` hay `Vector DB`; nó phải gọi gRPC/API tới service chủ quản.
2. **Transactional Outbox & Idempotency:**
   - Các sự kiện POI (`poi.upserted`, `poi.deleted`) được lưu vào bảng `OutboxEvents` trong cùng giao dịch với dữ liệu POI.
   - Message consumer phải kiểm tra trùng lặp qua bảng `ProcessedEvents` theo `event_id` trước khi xử lý.
3. **Bảo mật và Hiệu năng:**
   - Dùng JWT (`access_token`) xác thực giữa Client và API Gateway.
   - Giới hạn tốc độ gọi (Rate Limiting) trên API Gateway và Redis Cache.
   - Mã vé `shorted_code` trong Redis Cache có TTL và là thao tác nguyên tử (atomic `GETDEL` hoặc giao dịch Redis), dùng một lần duy nhất.

---

## 5. NGUYÊN TẮC VÀNG #4: HƯỚNG DẪN CHI TIẾT THIẾT LẬP MÔI TRƯỜNG & DỊCH VỤ BÊN NGOÀI

Trong suốt quá trình phát triển dự án, nếu phát sinh nhu cầu cài đặt hoặc cấu hình bất kỳ môi trường hay dịch vụ bên ngoài nào:
- **AI & External APIs:** Google Gemini API (AI Studio), Text Embedding model (`text-embedding-004`), Text-to-Speech (Edge-TTS), Translation APIs.
- **Cơ sở dữ liệu & Caching:** Upstash Redis (Logical DB 0 & DB 1), Qdrant Cloud (Vector DB), Supabase Storage / Cloudinary (Object Storage).
- **Hạ tầng truyền thông:** CloudAMQP / RabbitMQ Message Broker.
- **Container & Môi trường:** Docker, Dockerfile cho từng Microservice, Docker Compose chạy nội bộ (Local dev environment).
- **Triển khai & CI/CD:** GitHub Actions Secrets, Render / Fly.io / Koyeb, Vercel Edge Network.

**HÀNH ĐỘNG BẮT BUỘC DÀNH CHO AI AGENT:**
1. **Hướng dẫn chi tiết từng bước (Step-by-Step Walkthrough):** Tuyệt đối không chỉ đưa ra yêu cầu chung chung mà phải chỉ dẫn rõ ràng cho người dùng:
   - Đường link truy cập trang quản trị dịch vụ (Console/Dashboard).
   - Các bước thao tác cụ thể trên giao diện (chọn gói Free Tier, tạo Project, tạo Database/Queue, tạo API Key).
   - Nơi lấy chuỗi kết nối (`DATABASE_URL`, `REDIS_URL`, `AMQP_URL`, API Key...).
2. **Cung cấp tệp mẫu cấu hình môi trường (`.env.example`):**
   - Liệt kê đầy đủ tên biến, mô tả mục đích và cú pháp chuẩn.
   - Hướng dẫn người dùng cách tạo file `.env` cục bộ và nhắc nhở đưa `.env` vào `.gitignore` để không làm lộ bí mật lên Git.
3. **Cung cấp lệnh kiểm tra kết nối (Verification Command):**
   - Luôn viết sẵn script hoặc lệnh CLI ngắn gọn để người dùng chạy thử kiểm tra dịch vụ đã sẵn sàng và kết nối thành công trước khi tiến hành code logic nghiệp vụ.

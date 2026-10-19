# ỨNG DỤNG THUYẾT MINH TỰ ĐỘNG ĐA NGÔN NGỮ - CHÙA LINH ỨNG (MVP GPS)
> **Đồ án môn Công nghệ phần mềm - Đại học Sài Gòn (SGU)**  
> **Sinh viên thực hiện**: Nguyễn Mạnh Thắng (3124411283), Phạm Minh Khôi (3124411135), Trương Thuận Phú (3124411234)  
> **Giảng viên hướng dẫn**: ThS. Nguyễn Quốc Huy  

---

## 🏛️ Kiến Trúc Hệ Thống (Microservices)

```
                            [ Du khách (Mobile Web) ]     [ Quản trị viên (Admin) ]
                                        \                     /
                                         \                   /
                                  +-------------------------------+
                                  |      API Gateway (:8000)      |
                                  |   (Xác thực Token & Định tuyến)
                                  +---------------+---------------+
                                                  |
         +------------------------+---------------+------------------------+
         |                        |                                        |
+--------v-------+       +--------v-------+                       +--------v-------+
|  auth-service  |       |   poi-service  |                       | chatbot-service|
|    (:8001)     |       |    (:8002)     |                       |    (:8003)     |
+--------+-------+       +--------+-------+                       +--------+-------+
         |                        |                                        |
   [Users & Pay]             [POIs & Locs]                            [FAQ Cache &
    & [Cash TTL]                  |                                  Vectors Store]
                                  | (Publish: poi.upserted)
                                  v
                         [Message Queue (DLQ)]
                                  | (Consume: 15 ngôn ngữ)
                                  v
                      +-----------------------+
                      | data-pipeline-service |
                      |        (:8004)        |
                      +-----------------------+
```

---

## 🔌 Danh Sách Dịch Vụ & Cổng (Port Mapping)

| Thành phần | Cổng | Công nghệ | Nhiệm vụ chính |
| :--- | :--- | :--- | :--- |
| **API Gateway** | `8000` | FastAPI, HTTPX | Điểm vào duy nhất, kiểm tra `access_token`, tổng hợp sức khỏe |
| **Authorization Service** | `8001` | FastAPI, JWT, Bcrypt | Xác thực vé Online Payoo / Tiền mặt shortcode dùng 1 lần (UC01) |
| **Navigation & POI Service**| `8002` | FastAPI, SQLite/PG | CRUD POI, tuyến tham quan, endpoint `/pois/all` tải 1 lần (UC02) |
| **Chatbot AI Service** | `8003` | FastAPI, RAG, Vectors| Trợ lý ảo RAG hỏi đáp tri thức, Redis FAQ cache, từ chối ngoài lề (UC03) |
| **Data Pipeline Service** | `8004` | FastAPI, Worker, DLQ | Dịch tự động 15 ngôn ngữ ngầm, cập nhật tiến độ realtime (UC04) |
| **Frontend Client & Admin**| `3000` | React, Vite, Leaflet | Client App GPS Geofence & Admin Dashboard (`/admin`) |

---

## 🚀 Hướng Dẫn Khởi Chạy Bằng 1 Lệnh

### Cách 1: Chạy Local Mode (Không cần Docker, khuyến nghị cho máy demo)
Chỉ cần nhấp đúp hoặc chạy file kịch bản duy nhất:
```bat
start.bat
```
*(Trên Linux/macOS: chạy `./start.sh`)*

Hệ thống sẽ tự động khởi tạo môi trường, cài đặt thư viện và bật đồng loạt 5 backend services + API gateway + Vite frontend:
- **Ứng dụng Du khách (Mobile-first)**: `http://localhost:3000`
- **Trang Quản trị (Admin)**: `http://localhost:3000/admin` (Tài khoản: `admin` / Mật khẩu: `admin123`)
- **API Gateway Swagger Docs**: `http://localhost:8000/docs`
- **Kiểm tra trạng thái hệ thống**: `http://localhost:8000/health`

### Cách 2: Khởi chạy bằng Docker Compose (Khi môi trường có Docker)
```bash
docker compose up --build
```

---

## 📋 KỊCH BẢN DEMO 5 PHÚT CHO GIẢNG VIÊN (TỪNG BƯỚC)

### 🔹 Bước 1: Quét QR & Xác thực nhận Access Token (UC01)
1. Mở trình duyệt vào `http://localhost:3000`.
2. **Thử nghiệm Online Payoo**:
   - Bấm nút **"1. Giả lập Payoo (Pending)"** -> Sinh mã tự động dạng `PAY-XXXX`.
   - Bấm **"Xác Thực & Bắt Đầu"** -> Nhận thông báo: *"Giao dịch đang chờ xử lý từ cổng Payoo"*, ứng dụng tự động auto-retry mỗi 2 giây.
   - Bấm nút **"2. Webhook: Thành công"** -> Cổng Payoo xác nhận, Client auto-retry thành công và nhận JWT `access_token`!
3. **Thử nghiệm vé Tiền mặt (dùng 1 lần)**:
   - Vào `http://localhost:3000/admin`, bấm **"Tạo Mã Tiền Mặt"** -> Nhận mã 10 ký tự.
   - Dùng mã này xác thực tại màn hình chính -> Nhận token thành công.
   - Thử nhập lại mã lần 2 -> Hệ thống từ chối ngay lập tức: *"Mã xác thực không hợp lệ hoặc đã hết hạn"*.

### 🔹 Bước 2: Tải dữ liệu POI 1 lần duy nhất (UC02)
1. Sau khi có token, Client tự động gọi `GET /pois/all` **một lần duy nhất**.
2. Kiểm tra tab Network của DevTools: Toàn bộ 6 POI + 1 tuyến tham quan + toàn bộ 15 ngôn ngữ được nạp vào bộ nhớ trình duyệt.
3. Trong suốt quá trình tham quan, di chuyển, đổi tab, **không có thêm bất kỳ request nào gọi lại API POI**.

### 🔹 Bước 3: Giả lập GPS & Geofence Tự Động Thuyết Minh
1. Trên bản đồ Leaflet, thấy 6 điểm tham quan với vòng tròn bán kính kích hoạt (màu vàng nét đứt).
2. Bấm nút **"Đi tới POI tiếp theo"** (hoặc click trực tiếp lên một vòng tròn POI trên bản đồ):
   - Marker du khách di chuyển vào trong bán kính của POI (ví dụ: *Tượng Phật Bà Quan Âm 67m*).
   - Thẻ thông tin POI **tự động bật lên** và phát thuyết minh âm thanh.
   - Đứng yên trong vùng: Thuyết minh **chỉ phát 1 lần**, không bị lặp đi lặp lại.
3. **Đổi ngôn ngữ tức thì**:
   - Chọn ngôn ngữ trên thanh tiêu đề (ví dụ: `English`, `日本語`, `Français`...).
   - Nội dung thẻ thuyết minh và giọng đọc Web Speech API **thay đổi ngay lập tức** từ dữ liệu có sẵn ở client mà không gọi API.

### 🔹 Bước 4: Trợ lý ảo AI RAG (UC03)
1. Chuyển sang tab **"Trợ Lý AI (RAG)"**:
2. **Câu hỏi trong phạm vi**: Bấm gợi ý *"Tượng Phật Bà cao bao nhiêu mét?"* -> Chatbot trả lời chuẩn xác (cao 67m, 30 tầng) với nhãn **🧠 RAG KNOWLEDGE STORE**.
3. **Kiểm tra Redis FAQ Cache**: Gửi lại câu hỏi trên -> Câu trả lời phản hồi tức thì với huy hiệu xanh **⚡ TỪ BỘ NHỚ ĐỆM (CACHE HIT)**.
4. **Câu hỏi ngoài phạm vi**: Bấm gợi ý *"Cách làm bánh pizza hải sản?"* -> Chatbot từ chối lịch sự đúng văn bản quy định:  
   *"Xin lỗi, tôi chỉ có thể giải đáp các thông tin liên quan đến khu di tích Chùa Linh Ứng"*.

### 🔹 Bước 5: Quản trị Admin & Pipeline Dịch 15 Ngôn Ngữ Ngầm (UC04)
1. Bấm tab **"Quản Trị"** hoặc vào `http://localhost:3000/admin`.
2. Bấm **"Thêm POI Mới"** -> Điền thông tin, click bản đồ chọn vị trí, nhập mô tả tiếng Việt -> Bấm **"Lưu & Kích Hoạt Pipeline"**.
3. POI được tạo và phản hồi **ngay lập tức** cho Admin mà không bị treo.
4. Nhìn cột **Tiến độ Pipeline**: Hệ thống tự động polling mỗi 2 giây, thanh tiến độ chạy ngầm bất đồng bộ:  
   `Đang xử lý (3/15)` ➔ `Đang xử lý (8/15)` ➔ `Hoàn tất (15/15)`.
5. **Thử nghiệm Ngoại lệ UC04 A1**:
   - Bấm nút Sửa POI vừa tạo, **chỉ thay đổi tọa độ hoặc bán kính** (giữ nguyên mô tả) -> Bấm Lưu.
   - Hệ thống ghi nhận: *"Cập nhật tọa độ/bán kính thành công (bỏ qua dịch thuật vì mô tả không đổi)"* -> Không tốn tài nguyên chạy pipeline dịch lại.
6. Chuyển sang tab **"Giám Sát (Monitoring)"**: Xem trạng thái Message Queue và Dead-Letter Queue (DLQ).

---

## 🧪 Kiểm Thử Tự Động (Automated Testing)

Chạy toàn bộ bộ test tự động kiểm tra 100% các Use Case UC01, UC02, UC03, UC04:
```powershell
.\venv\Scripts\pytest.exe -v tests/test_backend.py
```
*(Kết quả: 10/10 test PASSED)*

Chạy kịch bản nghiệm thu luồng demo hoàn chỉnh:
```powershell
.\venv\Scripts\python.exe scripts/verify_demo_flow.py
```
*(Kết quả: 100% các use case chạy trơn tru)*

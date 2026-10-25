# 📋 CHI TIẾT CÁC USE CASES (PRODUCT BACKLOG)

> **Nguồn trích xuất**: PRD mục VI (UC01, UC02, UC03, UC04) và bộ test kiểm thử `Source/tests/test_backend.py`.

---

## 1. UC01 — Xác Thực và Cấp Quyền Truy Cập

- **Actor(s):** Customer (Du khách / Client App), Payoo Payment API.
- **Tóm tắt:** Du khách gửi mã xác thực sau khi thanh toán (`auth_code` từ luồng online hoặc `shorted_code` từ vé tiền mặt) tới hệ thống để kiểm tra và nhận JWT `access_token` truy cập ứng dụng.

### Luồng sự kiện chính (Basic Course of Events)
1. Customer hoàn tất thanh toán và gửi yêu cầu xác thực kèm mã xác thực trên Client App.
2. API Gateway tiếp nhận HTTPS Request và định tuyến đến `auth-service`.
3. `auth-service` kiểm tra mã:
   - Với mã tiền mặt (`shorted_code`): Đối chiếu trong Redis Cache.
   - Với mã online (`auth_code`): Kiểm tra trạng thái giao dịch trong Auth & Payment DB.
4. Hệ thống xác nhận thanh toán hợp lệ, cập nhật trạng thái phiên vào Auth & Payment DB và sinh JWT `access_token`.
5. Hệ thống trả `access_token` về cho Client App.
6. Client App lưu `access_token` vào `localStorage` để sử dụng cho mọi request tiếp theo.

### Luồng rẽ nhánh (Alternative Path — A1)
- **A1 — Thanh toán trực tuyến đang chờ xử lý (Pending):**
  - Khi Client gọi đổi `auth_code` nhưng Payoo chưa gửi kịp webhook xác nhận, `auth-service` kiểm tra thấy trạng thái `Pending` và trả về `{"status": "Pending", "message": "đang chờ xử lý"}`.
  - Client App đợi 2 giây và tự động retry cho đến khi nhận được token hoặc hết số lần thử tối đa.

### Các luồng ngoại lệ (Exception Paths)
- **E1 — Mã bị bỏ trống hoặc sai định dạng:** Trả về HTTP `400 Bad Request` kèm thông báo:  
  `"Vui lòng nhập mã xác thực hợp lệ"`.
- **E2 — Mã không tồn tại, đã dùng hoặc hết hạn:** Trả về HTTP `401 Unauthorized` kèm thông báo:  
  `"Mã xác thực không hợp lệ hoặc đã hết hạn"`.

### Quy tắc nghiệp vụ (Business Rules)
- Mã tiền mặt (`shorted_code`) có độ dài 10 ký tự, có thời hạn sống (`TTL`) trong Redis và **chỉ được đổi lấy token 1 lần duy nhất** (xóa khỏi cache ngay sau lần đổi đầu tiên).
- Mọi request gọi đến các service khác sau bước này đều bắt buộc kèm header `Authorization: Bearer <access_token>`.

---

## 2. UC02 — Truy Xuất Dữ Liệu Điểm Đến

- **Actor(s):** Client App (Mobile / Web App).
- **Tóm tắt:** Ngay sau khi xác thực thành công, Client App gọi API tải toàn bộ dữ liệu POI (tọa độ GPS, bán kính kích hoạt, văn bản và audio 15+ ngôn ngữ) trong **MỘT LẦN DUY NHẤT** về thiết bị.

### Luồng sự kiện chính (Basic Course of Events)
1. Client App tự động gửi request `GET /pois/all` kèm `access_token` tới API Gateway.
2. API Gateway phối hợp với `auth-service` kiểm tra tính hợp lệ của token.
3. Khi token hợp lệ, Gateway chuyển tiếp request đến `poi-service`.
4. `poi-service` truy vấn POI DB để đọc toàn bộ danh sách điểm tham quan, tọa độ, bán kính, thumbnail, gợi ý lộ trình và bản dịch/audio đa ngôn ngữ.
5. `poi-service` đóng gói dữ liệu thành JSON và trả về cho Client.
6. Client App lưu toàn bộ dữ liệu POI vào bộ nhớ trình duyệt (`localStorage`) để sử dụng xuyên suốt chuyến tham quan mà **không gọi lại API POI lần nào nữa**.

### Luồng rẽ nhánh & Ngoại lệ
- **A1 — Token không hợp lệ hoặc đã hết hạn:** Trả về HTTP `401 Unauthorized` và yêu cầu người dùng xác thực lại.
- **E1 — Mất kết nối DB:** Trả về HTTP `500 Internal Server Error` kèm thông báo `"Không thể tải dữ liệu bản đồ, vui lòng thử lại"`.
- **E2 — Dữ liệu POI trống:** Trả về danh sách rỗng `[]` kèm thông báo `"Dữ liệu điểm tham quan đang được cập nhật"`.

### Quy tắc nghiệp vụ & Geofence
- **Cơ chế tải 1 lần:** Tối ưu hóa tối đa băng thông mạng di động tại điểm tham quan.
- **Geofence GPS:** Khi tọa độ du khách đi vào trong vùng `trigger_radius` của điểm POI, Client tự động hiển thị thông tin và phát thuyết minh âm thanh. Không phát lặp lại nếu du khách vẫn đứng trong vùng.

---

## 3. UC03 — Hỏi Đáp Qua Chatbot AI

- **Actor(s):** Customer, AI API.
- **Tóm tắt:** Du khách đặt câu hỏi ngôn ngữ tự nhiên; hệ thống sử dụng kiến trúc RAG kết hợp Vector DB và mô hình AI để tìm kiếm ngữ cảnh và trả lời tức thì.

### Luồng sự kiện chính (Basic Course of Events)
1. Customer gửi câu hỏi qua khung chat kèm `access_token`.
2. API Gateway xác thực token và chuyển đến `chatbot-service`.
3. `chatbot-service` kiểm tra câu hỏi trong `ChatbotFAQCache` (Redis Cache).
4. **Nếu Cache Miss:** Gọi mô hình embedding chuyển câu hỏi thành vector.
5. Truy vấn Vector DB tìm kiếm các đoạn thông tin có độ tương đồng ngữ nghĩa (Cosine Similarity).
6. Ghép câu hỏi gốc và ngữ cảnh thành Prompt, gửi tới mô hình AI sinh câu trả lời.
7. Lưu cặp câu hỏi - câu trả lời vào Redis Cache, trả kết quả về cho Client.
8. Customer xem câu trả lời hiển thị trên màn hình chat.

### Luồng rẽ nhánh & Ngoại lệ
- **A1 — Cache Hit:** Nếu câu hỏi đã có trong Redis Cache, hệ thống lập tức trả kết quả ngay với `from_cache: true` mà không cần gọi embedding hay mô hình AI.
- **E1 — AI hoặc Vector DB timeout / lỗi kết nối:** Trả về thông báo:  
  `"Hệ thống trợ lý ảo đang bận, vui lòng thử lại sau giây lát"`.
- **E2 — Câu hỏi ngoài phạm vi Chùa Linh Ứng (Độ tương đồng < SIMILARITY_THRESHOLD):** Hệ thống từ chối lịch sự bằng câu trả lời mặc định:  
  `"Xin lỗi, tôi chỉ có thể giải đáp các thông tin liên quan đến khu di tích Chùa Linh Ứng"`.

---

## 4. UC04 — Xử Lý Dữ Liệu Đa Ngôn Ngữ & Tạo Audio Tự Động

- **Actor(s):** Admin / Staff (thông qua Admin Dashboard), Message Queue, Translation & TTS APIs.
- **Tóm tắt:** Khi Admin thêm hoặc cập nhật thông tin gốc của một POI, hệ thống đẩy sự kiện qua Message Queue để `data-pipeline-service` chạy ngầm tự động dịch sang 15+ ngôn ngữ, tạo file âm thanh và cập nhật Vector DB.

### Luồng sự kiện chính (Basic Course of Events)
1. Admin nhập thông tin POI trên Admin Dashboard và nhấn Lưu.
2. `poi-service` lưu thông tin cơ bản vào POI DB và trả phản hồi thành công ngay lập tức cho Admin (non-blocking).
3. Đồng thời, `poi-service` đẩy một sự kiện (`poi.upserted`) vào Message Queue (RabbitMQ).
4. `data-pipeline-service` lắng nghe hàng đợi, nhận dữ liệu văn bản gốc của POI.
5. `data-pipeline-service` gọi Translation & TTS APIs để dịch mô tả sang 15+ ngôn ngữ và tổng hợp âm thanh.
6. Cập nhật bản dịch và audio URL vào `POILocalizations` trong POI DB.
7. Tạo vector embeddings mới và đồng bộ sang Vector DB phục vụ Chatbot RAG.

### Luồng rẽ nhánh đặc biệt bắt buộc (Alternative Path — A1)
- **A1 — Admin chỉ sửa tọa độ hoặc bán kính (Mô tả gốc giữ nguyên):**
  - `poi-service` cập nhật trực tiếp vào POI DB và **TUYỆT ĐỐI KHÔNG** phát sự kiện vào Message Queue để tránh lãng phí tài nguyên và chi phí gọi API.

### Các luồng ngoại lệ
- **E1 — Lỗi kết nối hoặc quá hạn ngạch API dịch thuật/TTS:** `data-pipeline-service` giữ thông điệp trong hàng đợi, thực hiện retry tối đa 3 lần; nếu vẫn lỗi thì chuyển thông điệp vào Dead-Letter Queue (`poi.dlq`) để không làm gián đoạn các POI khác.
- **E2 — Lỗi ghi DB:** Ghi nhận cảnh báo lỗi lên Monitoring Dashboard để quản trị viên kiểm tra.

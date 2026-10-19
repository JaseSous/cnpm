# Kịch bản kiểm thử toàn bộ luồng Demo (Demo Flow Verification)
import sys
import time
from pathlib import Path
import importlib.util

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient

def load_app(file_path: Path):
    module_name = file_path.stem + "_" + file_path.parent.parent.stem.replace("-", "_")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.app

auth_app = load_app(ROOT_DIR / "services" / "auth-service" / "app" / "main.py")
poi_app = load_app(ROOT_DIR / "services" / "poi-service" / "app" / "main.py")
chat_app = load_app(ROOT_DIR / "services" / "chatbot-service" / "app" / "main.py")
pipeline_app = load_app(ROOT_DIR / "services" / "data-pipeline-service" / "app" / "main.py")
gateway_app = load_app(ROOT_DIR / "api-gateway" / "app" / "main.py")

auth_c = TestClient(auth_app)
poi_c = TestClient(poi_app)
chat_c = TestClient(chat_app)
pipeline_c = TestClient(pipeline_app)
gateway_c = TestClient(gateway_app)

def run_demo():
    print("=" * 70)
    print("🎬 BẮT ĐẦU CHẠY KIỂM THỬ KỊCH BẢN DEMO TỰ ĐỘNG - CHÙA LINH ỨNG (MVP)")
    print("=" * 70)

    # -------------------------------------------------------------
    # BƯỚC 1: XÁC THỰC UC01 (ONLINE PAYOO PENDING + SUCCESS & TIỀN MẶT)
    # -------------------------------------------------------------
    print("\n[BƯỚC 1.1] Giả lập quét QR Payoo tại cổng (Tạo phiên Pending)...")
    res_payoo = auth_c.post("/auth/payoo/create-session", json={"amount": 50000.0})
    payoo_data = res_payoo.json()
    auth_code = payoo_data["auth_code"]
    print(f"  -> Mã thanh toán tạo ra: {auth_code} | Trạng thái: {payoo_data['status']}")
    assert payoo_data["status"] == "Pending"

    print("[BƯỚC 1.2] Du khách thử verify khi cổng Payoo chưa xác nhận (UC01 A1)...")
    res_pending = auth_c.post("/auth/verify", json={"code": auth_code})
    print(f"  -> Phản hồi: {res_pending.json()}")
    assert res_pending.json()["status"] == "Pending"
    assert res_pending.json()["message"] == "đang chờ xử lý"

    print("[BƯỚC 1.3] Giả lập Webhook Payoo chuyển trạng thái sang Success...")
    res_webhook = auth_c.post("/auth/payoo/webhook-mock", json={"auth_code": auth_code, "status": "Success"})
    print(f"  -> Webhook kết quả: {res_webhook.json()['new_status']}")
    assert res_webhook.json()["new_status"] == "Success"

    print("[BƯỚC 1.4] Client auto-retry gửi lại mã sau khi webhook thành công...")
    res_success = auth_c.post("/auth/verify", json={"code": auth_code})
    token = res_success.json()["access_token"]
    print(f"  -> Nhận JWT access_token: {token[:25]}... (Hợp lệ: Success)")
    assert "access_token" in res_success.json()

    print("\n[BƯỚC 1.5] Thử nghiệm luồng vé TIỀN MẶT (Admin tạo shorted_code)...")
    res_cash = auth_c.post("/auth/admin/cash-code")
    cash_code = res_cash.json()["shorted_code"]
    print(f"  -> Admin cấp mã tiền mặt 10 ký tự: {cash_code}")
    assert len(cash_code) == 10

    print("  -> Du khách đổi mã tiền mặt lần 1 (thành công)...")
    res_cash_verify1 = auth_c.post("/auth/verify", json={"code": cash_code})
    assert "access_token" in res_cash_verify1.json()
    print("  -> Đổi mã lần 1 thành công!")

    print("  -> Thử đổi lại mã tiền mặt lần 2 (mã dùng 1 lần)...")
    res_cash_verify2 = auth_c.post("/auth/verify", json={"code": cash_code})
    print(f"  -> Phản hồi: {res_cash_verify2.status_code} - {res_cash_verify2.json()['detail']}")
    assert res_cash_verify2.status_code == 401
    print("  -> Mã dùng 1 lần đã bị vô hiệu hóa chuẩn xác!")

    # -------------------------------------------------------------
    # BƯỚC 2: TRUY XUẤT DỮ LIỆU BẢN ĐỒ TẢI 1 LẦN (UC02)
    # -------------------------------------------------------------
    print("\n[BƯỚC 2] Tải toàn bộ dữ liệu POIs, Tour Routes và 15 ngôn ngữ...")
    res_all_pois = poi_c.get("/pois/all")
    pois_data = res_all_pois.json()
    poi_count = len(pois_data["pois"])
    route_count = len(pois_data["tour_routes"])
    print(f"  -> Tải thành công {poi_count} điểm tham quan và {route_count} tuyến tham quan!")
    assert poi_count >= 6
    assert route_count >= 1

    first_poi = pois_data["pois"][0]
    loc_count = len(first_poi.get("localizations", {}))
    print(f"  -> POI mẫu: '{first_poi['name']}' có sẵn {loc_count} bản dịch ngôn ngữ!")
    assert loc_count >= 15

    # -------------------------------------------------------------
    # BƯỚC 3: HỎI ĐÁP CHATBOT AI RAG (UC03)
    # -------------------------------------------------------------
    print("\n[BƯỚC 3.1] Hỏi Chatbot câu hỏi trong phạm vi: 'Tượng Phật Bà cao bao nhiêu mét?'...")
    q1 = "Tượng Phật Bà cao bao nhiêu mét?"
    res_chat1 = chat_c.post("/chat/ask", json={"question": q1})
    chat1_data = res_chat1.json()
    print(f"  -> Trả lời: {chat1_data['answer']}")
    print(f"  -> from_cache: {chat1_data['from_cache']} (Lần 1 từ Vector DB RAG)")
    assert chat1_data["from_cache"] is False

    print("\n[BƯỚC 3.2] Hỏi lại đúng câu hỏi trên để kiểm tra Redis FAQ Cache...")
    res_chat2 = chat_c.post("/chat/ask", json={"question": q1})
    chat2_data = res_chat2.json()
    print(f"  -> Trả lời: {chat2_data['answer']}")
    print(f"  -> from_cache: {chat2_data['from_cache']} (Lần 2 trúng Cache)")
    assert chat2_data["from_cache"] is True

    print("\n[BƯỚC 3.3] Hỏi câu hỏi ngoài phạm vi di tích: 'Cách làm bánh pizza hải sản?'...")
    q_out = "Cách làm bánh pizza hải sản?"
    res_chat3 = chat_c.post("/chat/ask", json={"question": q_out})
    chat3_data = res_chat3.json()
    print(f"  -> Phản hồi: '{chat3_data['answer']}'")
    assert chat3_data["in_scope"] is False
    assert "Xin lỗi, tôi chỉ có thể giải đáp các thông tin liên quan đến khu di tích Chùa Linh Ứng" in chat3_data["answer"]

    # -------------------------------------------------------------
    # BƯỚC 4: PIPELINE BẤT ĐỒNG BỘ ĐA NGÔN NGỮ (UC04)
    # -------------------------------------------------------------
    print("\n[BƯỚC 4.1] Admin thêm POI mới -> Phản hồi ngay, dịch 15 ngôn ngữ ngầm...")
    new_poi_res = poi_c.post("/pois", json={
        "name": "Bảo Tháp Xá Lợi Mới",
        "latitude": 16.1012,
        "longitude": 108.2785,
        "trigger_radius": 25,
        "original_description": "Bảo Tháp Xá Lợi là công trình kiến trúc Phật giáo tôn nghiêm lưu giữ các viên ngọc xá lợi Phật linh thiêng."
    })
    created_poi = new_poi_res.json()
    print(f"  -> POI tạo thành công: {created_poi['poi_id']} | Pipeline status: {created_poi['pipeline_status']}")
    assert created_poi["status"] == "success"

    print("  -> Chờ worker ngầm xử lý dịch 15 ngôn ngữ (Polling)...")
    for _ in range(30):
        time.sleep(0.1)
        poi_status_res = poi_c.get(f"/pois/{created_poi['poi_id']}/pipeline-status")
        cur_status = poi_status_res.json()["pipeline_status"]
        if "Hoàn tất" in cur_status:
            break

    print(f"  -> Trạng thái pipeline sau khi chạy ngầm: {cur_status}")
    assert "Hoàn tất" in cur_status

    print("\n[BƯỚC 4.2] Admin sửa CHỈ tọa độ/bán kính (UC04 A1) -> BỎ QUA dịch thuật...")
    edit_coord_res = poi_c.put(f"/pois/{created_poi['poi_id']}", json={
        "latitude": 16.1015,
        "trigger_radius": 35
    })
    print(f"  -> Kết quả: description_changed={edit_coord_res.json()['description_changed']}")
    assert edit_coord_res.json()["description_changed"] is False

    # -------------------------------------------------------------
    # BƯỚC 5: TỔNG HỢP HEALTHCHECK TẠI API GATEWAY
    # -------------------------------------------------------------
    print("\n[BƯỚC 5] Kiểm tra API Gateway tổng hợp trạng thái các service...")
    gw_health = gateway_c.get("/health")
    print(f"  -> Healthcheck Gateway: {gw_health.json()}")
    assert gw_health.status_code == 200

    print("\n" + "=" * 70)
    print("🎉 TOÀN BỘ KỊCH BẢN DEMO ĐÃ ĐẠT 100% TIÊU CHÍ NGHIỆM THU!")
    print("=" * 70)

if __name__ == "__main__":
    run_demo()

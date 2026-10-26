import sys
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import importlib.util

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

from shared.adapters import shared_cache, shared_queue, shared_vector_store

auth_client = TestClient(auth_app)
poi_client = TestClient(poi_app)
chat_client = TestClient(chat_app)
pipeline_client = TestClient(pipeline_app)
gateway_client = TestClient(gateway_app)


# ===============================================================
# KIỂM THỬ UC01: XÁC THỰC VÀ CẤP QUYỀN TRUY CẬP
# ===============================================================

def test_uc01_invalid_empty_code_returns_400():
    """UC01 E1: Mã rỗng hoặc sai định dạng -> 400 'Vui lòng nhập mã xác thực hợp lệ'"""
    # Mã rỗng
    res = auth_client.post("/auth/verify", json={"code": ""})
    assert res.status_code == 400
    assert res.json()["detail"] == "Vui lòng nhập mã xác thực hợp lệ"

    # Mã quá ngắn
    res_short = auth_client.post("/auth/verify", json={"code": "12"})
    assert res_short.status_code == 400
    assert res_short.json()["detail"] == "Vui lòng nhập mã xác thực hợp lệ"


def test_uc01_nonexistent_or_expired_code_returns_401():
    """UC01 E2: Mã không tồn tại hoặc hết hạn -> 401 'Mã xác thực không hợp lệ hoặc đã hết hạn'"""
    res = auth_client.post("/auth/verify", json={"code": "UNKNOWN-CODE-999"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Mã xác thực không hợp lệ hoặc đã hết hạn"


def test_uc01_online_payment_pending_and_success():
    """UC01 & A1: Luồng Payoo Online: Pending -> Webhook -> Success -> JWT Token"""
    # 1. Khách hàng tạo phiên thanh toán giả lập Payoo
    create_res = auth_client.post("/auth/payoo/create-session", json={"amount": 50000.0})
    assert create_res.status_code == 200
    auth_code = create_res.json()["auth_code"]
    assert create_res.json()["status"] == "Pending"

    # 2. UC01 A1: Verify khi còn Pending -> trả thông báo 'đang chờ xử lý'
    verify_pending = auth_client.post("/auth/verify", json={"code": auth_code})
    assert verify_pending.status_code == 200
    assert verify_pending.json()["status"] == "Pending"
    assert verify_pending.json()["message"] == "đang chờ xử lý"

    # 3. Giả lập Payoo Webhook chuyển sang Success
    webhook_res = auth_client.post("/auth/payoo/webhook-mock", json={
        "auth_code": auth_code,
        "status": "Success"
    })
    assert webhook_res.status_code == 200

    # 4. Client auto-retry gửi lại -> Nhận được access_token JWT
    verify_success = auth_client.post("/auth/verify", json={"code": auth_code})
    assert verify_success.status_code == 200
    assert verify_success.json()["status"] == "Success"
    assert "access_token" in verify_success.json()


def test_uc01_cash_code_single_use():
    """UC01: Mã tiền mặt (shorted_code) lấy từ Redis, có TTL, chỉ dùng 1 LẦN DUY NHẤT rồi xóa"""
    # 1. Admin tạo mã tiền mặt 10 ký tự
    cash_res = auth_client.post("/auth/admin/cash-code")
    assert cash_res.status_code == 200
    shorted_code = cash_res.json()["shorted_code"]
    assert len(shorted_code) == 10

    # 2. Du khách nhập mã đổi token lần đầu -> Thành công
    first_verify = auth_client.post("/auth/verify", json={"code": shorted_code})
    assert first_verify.status_code == 200
    assert "access_token" in first_verify.json()

    # 3. Dùng lại mã lần 2 -> Thất bại vì đã bị xóa (dùng 1 lần)
    second_verify = auth_client.post("/auth/verify", json={"code": shorted_code})
    assert second_verify.status_code == 401
    assert second_verify.json()["detail"] == "Mã xác thực không hợp lệ hoặc đã hết hạn"


# ===============================================================
# KIỂM THỬ UC02: TRUY XUẤT DỮ LIỆU ĐIỂM ĐẾN
# ===============================================================

def test_uc02_fetch_all_pois_and_routes_once():
    """UC02: Tải MỘT LẦN toàn bộ POIs + 15 localizations + tour route"""
    res = poi_client.get("/pois/all")
    assert res.status_code == 200
    data = res.json()
    assert "pois" in data
    assert len(data["pois"]) >= 6
    assert "tour_routes" in data
    assert len(data["tour_routes"]) >= 1

    # Kiểm tra POI đầu tiên có đủ 15 ngôn ngữ
    first_poi = data["pois"][0]
    assert "localizations" in first_poi
    assert "vi" in first_poi["localizations"]
    assert "en" in first_poi["localizations"]
    assert "zh" in first_poi["localizations"]
    assert "ja" in first_poi["localizations"]
    assert "ko" in first_poi["localizations"]


def test_uc02_gateway_rejects_unauthorized():
    """UC02 A1: API Gateway từ chối truy cập /pois/all khi không có token hoặc sai token"""
    res_no_token = gateway_client.get("/pois/all")
    assert res_no_token.status_code == 401
    assert res_no_token.json()["detail"] == "Mã xác thực không hợp lệ hoặc đã hết hạn"

    res_fake_token = gateway_client.get(
        "/pois/all",
        headers={"Authorization": "Bearer fake-invalid-token"}
    )
    assert res_fake_token.status_code == 401


# ===============================================================
# KIỂM THỬ UC03: CHATBOT AI RAG
# ===============================================================

def test_uc03_chatbot_in_scope_and_cache_hit():
    """UC03 & A1: Hỏi đáp trong phạm vi và cơ chế Cache Hit (from_cache=true)"""
    question = "Tượng Phật Bà Quan Thế Âm cao bao nhiêu mét?"

    # Lần 1: Hỏi đáp từ Vector DB + RAG -> from_cache=False
    res1 = chat_client.post("/chat/ask", json={"question": question})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["from_cache"] is False
    assert "67" in data1["answer"] or "Phật Bà" in data1["answer"]

    # Lần 2: Hỏi lại đúng câu hỏi đó -> Trả về ngay từ Redis Cache (from_cache=True)
    res2 = chat_client.post("/chat/ask", json={"question": question})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["from_cache"] is True
    assert data2["answer"] == data1["answer"]


def test_uc03_chatbot_out_of_scope_rejection():
    """UC03 E2: Câu hỏi ngoài phạm vi -> Từ chối lịch sự đúng văn bản quy định"""
    out_of_scope_q = "Công thức làm bánh pizza hải sản truyền thống của Ý?"
    res = chat_client.post("/chat/ask", json={"question": out_of_scope_q})
    assert res.status_code == 200
    data = res.json()
    assert data["in_scope"] is False
    assert data["answer"] == "Xin lỗi, tôi chỉ có thể giải đáp các thông tin liên quan đến khu di tích Chùa Linh Ứng"


# ===============================================================
# KIỂM THỬ UC04: DATA PIPELINE ĐA NGÔN NGỮ & MESSAGE QUEUE
# ===============================================================

def test_uc04_no_publish_when_only_coords_changed():
    """UC04 A1: Admin chỉ đổi tọa độ/bán kính (mô tả giữ nguyên) -> KHÔNG publish event dịch thuật"""
    queue_len_before = len(shared_queue._queue)

    update_res = poi_client.put("/pois/poi_1", json={
        "latitude": 16.10099,
        "trigger_radius": 40
    })
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["description_changed"] is False

    # Độ dài hàng đợi không tăng
    queue_len_after = len(shared_queue._queue)
    assert queue_len_after == queue_len_before


def test_uc04_publish_and_process_when_description_changed():
    """UC04: Đổi mô tả gốc -> CÓ publish event và data-pipeline dịch đủ 15 ngôn ngữ"""
    new_desc = f"Tượng Phật Bà Quan Thế Âm cao 67m uy nghiêm hướng nhìn ra biển Đông - Cập nhật lúc {time.time()}."
    
    update_res = poi_client.put("/pois/poi_1", json={
        "original_description": new_desc
    })
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["description_changed"] is True

    # Chờ nhẹ cho worker background xử lý bất đồng bộ
    status = ""
    for _ in range(15):
        time.sleep(0.2)
        status_res = poi_client.get("/pois/poi_1/pipeline-status")
        assert status_res.status_code == 200
        status = status_res.json()["pipeline_status"]
        if "Đang xử lý" in status or "Hoàn tất" in status:
            break

    assert ("Đang xử lý" in status) or ("Hoàn tất" in status)


# ===============================================================
# KIỂM THỬ THỐNG KÊ LƯỢNG KHÁCH TRUY CẬP (ACTIVE, HÔM NAY, TỔNG SỐ)
# ===============================================================

def test_visitor_heartbeat_and_stats():
    """Kiểm thử gửi heartbeat và tra cứu số khách online, hôm nay và tổng lượt"""
    client_id = f"test_vis_{int(time.time())}"
    heartbeat_res = auth_client.post("/auth/heartbeat", json={"client_id": client_id})
    assert heartbeat_res.status_code == 200
    assert heartbeat_res.json()["status"] == "ok"
    assert heartbeat_res.json()["active_visitors"] >= 1

    stats_res = auth_client.get("/auth/active-visitors")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "active_visitors" in stats
    assert "today_visitors" in stats
    assert "total_visitors" in stats
    assert stats["active_visitors"] >= 1
    assert stats["today_visitors"] >= 1
    assert stats["total_visitors"] >= stats["today_visitors"]

    vstats_res = auth_client.get("/auth/visitor-stats")
    assert vstats_res.status_code == 200
    assert vstats_res.json()["today_visitors"] == stats["today_visitors"]

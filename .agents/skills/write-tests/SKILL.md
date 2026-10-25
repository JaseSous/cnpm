---
name: write-tests
description: Hướng dẫn viết unit test và integration test cho các Use Cases của backend sử dụng pytest và FastAPI TestClient.
---

# 🧪 SKILL: HƯỚNG DẪN VIẾT UNIT TEST VÀ INTEGRATION TEST

Skill này hướng dẫn quy chuẩn viết và mở rộng bộ test tự động tại `Source/tests/test_backend.py` nhằm bao phủ 100% các Use Cases (UC01, UC02, UC03, UC04) theo đúng PRD.

---

## 1. Cấu Trúc Khởi Tạo TestClient Cho Từng Service

Trong kiến trúc Microservices, kiểm thử cục bộ được thực hiện bằng cách nạp trực tiếp FastAPI application qua `importlib` và `TestClient`:

```python
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent

def load_app(file_path: Path):
    module_name = file_path.stem + "_" + file_path.parent.parent.stem.replace("-", "_")
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app

# Nạp các app cần kiểm thử
auth_app = load_app(ROOT_DIR / "services" / "auth-service" / "app" / "main.py")
auth_client = TestClient(auth_app)
```

---

## 2. Quy Chuẩn Viết Test Theo Mã Lỗi PRD

Tên hàm test và docstring phải ghi rõ Use Case và mã ngoại lệ tương ứng:

```python
def test_uc01_invalid_empty_code_returns_400():
    """UC01 E1: Mã rỗng hoặc sai định dạng -> 400 'Vui lòng nhập mã xác thực hợp lệ'"""
    res = auth_client.post("/auth/verify", json={"code": ""})
    assert res.status_code == 400
    assert res.json()["detail"] == "Vui lòng nhập mã xác thực hợp lệ"

def test_uc01_nonexistent_code_returns_401():
    """UC01 E2: Mã không tồn tại hoặc hết hạn -> 401 'Mã xác thực không hợp lệ hoặc đã hết hạn'"""
    res = auth_client.post("/auth/verify", json={"code": "INVALID-CODE"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Mã xác thực không hợp lệ hoặc đã hết hạn"
```

---

## 3. Kiểm Thử Ngoại Lệ Nghiệp Vụ Bắt Buộc

1. **UC04 A1 (Không publish khi mô tả không đổi):**
   ```python
   def test_uc04_no_publish_when_only_coords_changed():
       """UC04 A1: Admin chỉ đổi tọa độ/bán kính -> KHÔNG publish event dịch thuật"""
       # Kiểm tra độ dài hàng đợi trước và sau request không đổi
   ```
2. **UC01 Dùng 1 lần của mã tiền mặt:**
   - Đổi lần 1: Thành công (`200 OK`, có `access_token`).
   - Đổi lần 2 cùng mã đó: Thất bại (`401 Unauthorized`).
3. **UC03 Từ chối câu hỏi ngoài lề:**
   - Kiểm tra cờ `in_scope == False`.
   - Kiểm tra nội dung trả về đúng câu quy định trong PRD:  
     `"Xin lỗi, tôi chỉ có thể giải đáp các thông tin liên quan đến khu di tích Chùa Linh Ứng"`.

---

## 4. Lệnh Chạy Bộ Test

Tại thư mục `Source/`:
```bash
pytest -v tests/test_backend.py
```
Để xem log in ra chi tiết khi debug:
```bash
pytest -v -s tests/test_backend.py
```

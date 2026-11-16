import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_admin_create_poi_success(client: AsyncClient, admin_token: str):
    """UC10: Admin tạo POI mới thành công kèm 15 localizations và Transactional Outbox"""
    poi_payload = {
        "original_language_code": "vi",
        "original_title": "Tượng Phật Bà Quan Âm",
        "original_description": "Tượng Phật Bà Quan Âm cao 67m tại Chùa Linh Ứng Bãi Bụt.",
        "latitude": 16.1001,
        "longitude": 108.2775,
        "trigger_radius": 35.0,
        "thumbnail_url": "https://example.com/thumb.jpg"
    }
    res = await client.post("/api/pois", json=poi_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 201
    data = res.json()
    assert data["poi_id"] == 1
    assert data["original_title"] == "Tượng Phật Bà Quan Âm"
    assert data["revision"] == 1
    assert data["vector_status"] == "Pending"
    assert len(data["localizations"]) == 15

    # Ngôn ngữ gốc 'vi' phải là Done, các ngôn ngữ khác là Pending
    vi_loc = next(l for l in data["localizations"] if l["language_code"] == "vi")
    assert vi_loc["status"] == "Done"
    en_loc = next(l for l in data["localizations"] if l["language_code"] == "en")
    assert en_loc["status"] == "Pending"

@pytest.mark.asyncio
async def test_create_poi_invalid_language(client: AsyncClient, admin_token: str):
    """Tạo POI với ngôn ngữ không được hỗ trợ trả về 400 hoặc 422"""
    poi_payload = {
        "original_language_code": "xx",
        "original_title": "Test POI",
        "original_description": "Description test invalid language hợp lệ độ dài",
        "latitude": 16.1001,
        "longitude": 108.2775
    }
    res = await client.post("/api/pois", json=poi_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 400
    assert res.json()["detail"]["error_code"] == "INVALID_LANGUAGE"

@pytest.mark.asyncio
async def test_admin_update_poi_content(client: AsyncClient, admin_token: str):
    """UC10: Cập nhật nội dung tiêu đề/mô tả sẽ tăng revision lên 2"""
    # 1. Tạo POI
    create_res = await client.post("/api/pois", json={
        "original_language_code": "vi",
        "original_title": "Chánh Điện",
        "original_description": "Chánh điện uy nghiêm của Chùa Linh Ứng.",
        "latitude": 16.1005,
        "longitude": 108.2780
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert create_res.status_code == 201
    poi_id = create_res.json()["poi_id"]
    assert create_res.json()["revision"] == 1

    # 2. Cập nhật bài thuyết minh
    update_res = await client.put(f"/api/pois/{poi_id}", json={
        "original_description": "Chánh điện uy nghiêm của Chùa Linh Ứng với kiến trúc mái ngói rồng uốn lượn."
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert update_res.status_code == 200
    assert update_res.json()["revision"] == 2

@pytest.mark.asyncio
async def test_admin_update_poi_coordinates_only(client: AsyncClient, admin_token: str):
    """Cập nhật tọa độ không đổi revision"""
    create_res = await client.post("/api/pois", json={
        "original_language_code": "vi",
        "original_title": "Cổng Tam Quan",
        "original_description": "Cổng Tam Quan hướng ra biển cả bao la.",
        "latitude": 16.1010,
        "longitude": 108.2790
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert create_res.status_code == 201
    poi_id = create_res.json()["poi_id"]

    update_res = await client.put(f"/api/pois/{poi_id}", json={
        "latitude": 16.1015,
        "trigger_radius": 45.0
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert update_res.status_code == 200
    assert update_res.json()["revision"] == 1
    assert update_res.json()["trigger_radius"] == 45.0

@pytest.mark.asyncio
async def test_admin_delete_poi(client: AsyncClient, admin_token: str):
    """UC10: Xóa POI thành công"""
    create_res = await client.post("/api/pois", json={
        "original_language_code": "vi",
        "original_title": "Điểm cần xóa",
        "original_description": "Mô tả tạm thời cho điểm cần xóa đạt chuẩn độ dài.",
        "latitude": 16.1000,
        "longitude": 108.2700
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert create_res.status_code == 201
    poi_id = create_res.json()["poi_id"]

    del_res = await client.delete(f"/api/pois/{poi_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_res.status_code == 200
    assert del_res.json()["success"] == True

    # Kiểm tra không còn tồn tại
    get_res = await client.get(f"/api/pois/{poi_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert get_res.status_code == 404

@pytest.mark.asyncio
async def test_unauthorized_poi_management(client: AsyncClient, customer_token: str):
    """Role customer không có quyền tạo/sửa/xóa POI (403 Forbidden)"""
    res = await client.post("/api/pois", json={
        "original_language_code": "vi",
        "original_title": "Test Điểm",
        "original_description": "Test bài thuyết minh đạt chuẩn độ dài",
        "latitude": 16.1,
        "longitude": 108.2
    }, headers={"Authorization": f"Bearer {customer_token}"})
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_upload_thumbnail(client: AsyncClient, admin_token: str):
    """Admin upload ảnh thumbnail POI"""
    file_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    files = {"file": ("test_upload.jpg", file_content, "image/jpeg")}
    res = await client.post(
        "/api/pois/upload-thumbnail",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "thumbnail_url" in data
    assert "thumbnails/poi_thumb_" in data["thumbnail_url"] or "/media/thumbnails/" in data["thumbnail_url"]

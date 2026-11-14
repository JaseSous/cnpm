import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_customer_fetch_pois_success(client: AsyncClient, admin_token: str, customer_token: str):
    """UC02: Du khách lấy danh sách POIs theo ngôn ngữ gốc"""
    # 1. Tạo 1 POI
    await client.post("/api/pois", json={
        "original_language_code": "vi",
        "original_title": "Tượng Quan Âm Bãi Bụt",
        "original_description": "Thuyết minh chi tiết tiếng Việt.",
        "latitude": 16.1001,
        "longitude": 108.2775
    }, headers={"Authorization": f"Bearer {admin_token}"})

    # 2. Du khách gọi GET /api/pois
    res = await client.get("/api/pois?lang=vi", headers={"Authorization": f"Bearer {customer_token}"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["pois"]) >= 1
    assert data["pois"][0]["title"] == "Tượng Quan Âm Bãi Bụt"
    assert data["pois"][0]["fallback"] == False
    assert "data_version" in data

@pytest.mark.asyncio
async def test_customer_poi_304_not_modified(client: AsyncClient, admin_token: str, customer_token: str):
    """UC02: Trả về HTTP 304 Not Modified khi since_version trùng data_version hiện tại"""
    # 1. Lấy danh sách lần đầu để biết version
    res1 = await client.get("/api/pois?lang=vi", headers={"Authorization": f"Bearer {customer_token}"})
    assert res1.status_code == 200
    current_ver = res1.json()["data_version"]

    # 2. Gọi lại với since_version = current_ver -> Phải trả 304
    res_304 = await client.get(f"/api/pois?lang=vi&since_version={current_ver}", headers={"Authorization": f"Bearer {customer_token}"})
    assert res_304.status_code == 304

@pytest.mark.asyncio
async def test_customer_poi_fallback_language(client: AsyncClient, admin_token: str, customer_token: str):
    """UC02: Trả về bản dịch ngôn ngữ fallback (tiếng Việt) kèm cờ fallback=True khi ngôn ngữ yêu cầu chưa có bản dịch Done"""
    await client.post("/api/pois", json={
        "original_language_code": "vi",
        "original_title": "Tháp Xá Lợi",
        "original_description": "Tháp Xá Lợi 9 tầng.",
        "latitude": 16.1008,
        "longitude": 108.2779
    }, headers={"Authorization": f"Bearer {admin_token}"})

    # Yêu cầu tiếng Pháp 'fr' (chưa được worker dịch xong -> Pending)
    res_fr = await client.get("/api/pois?lang=fr", headers={"Authorization": f"Bearer {customer_token}"})
    assert res_fr.status_code == 200
    data = res_fr.json()
    assert data["pois"][0]["fallback"] == True
    assert data["pois"][0]["language_code"] == "vi"

@pytest.mark.asyncio
async def test_pipeline_status_overview(client: AsyncClient, admin_token: str):
    """UC11: Admin theo dõi trạng thái tiến trình xử lý ngôn ngữ và cảnh báo lỗi"""
    await client.post("/api/pois", json={
        "original_language_code": "vi",
        "original_title": "Vườn Tượng La Hán",
        "original_description": "18 vị La Hán bằng đá cẩm thạch non nước.",
        "latitude": 16.1003,
        "longitude": 108.2772
    }, headers={"Authorization": f"Bearer {admin_token}"})

    res = await client.get("/api/pois/pipeline-status", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    poi = items[0]
    assert "localizations" in poi
    assert len(poi["localizations"]) == 15
    assert "vector_status" in poi

@pytest.mark.asyncio
async def test_retry_pipeline(client: AsyncClient, admin_token: str):
    """UC11: Admin kích hoạt Retry xử lý lại ngôn ngữ bị lỗi"""
    create_res = await client.post("/api/pois", json={
        "original_language_code": "vi",
        "original_title": "Điểm Retry",
        "original_description": "Thuyết minh kiểm tra retry.",
        "latitude": 16.1004,
        "longitude": 108.2774
    }, headers={"Authorization": f"Bearer {admin_token}"})
    poi_id = create_res.json()["poi_id"]

    retry_res = await client.post(
        f"/api/pois/{poi_id}/retry",
        json={"language_codes": ["en", "zh"], "retry_vector": True},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert retry_res.status_code == 200
    data = retry_res.json()
    assert data["success"] == True
    assert "en" in data["retried_languages"]

@pytest.mark.asyncio
async def test_get_languages_uc05(client: AsyncClient):
    """UC05: Lấy danh mục ngôn ngữ hỗ trợ (15 ngôn ngữ, tiếng Việt fallback đầu tiên)"""
    res = await client.get("/api/languages")
    assert res.status_code == 200
    langs = res.json()
    assert len(langs) == 15
    assert langs[0]["language_code"] == "vi"
    assert langs[0]["is_fallback"] == True

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent

def load_app(module_path: Path):
    """Tải FastAPI app từ đường dẫn file bất kỳ"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["main"] = module
    spec.loader.exec_module(module)
    return module.app

def test_api_gateway_health():
    """Kiểm tra healthcheck của api-gateway"""
    app = load_app(ROOT_DIR / "api-gateway" / "app" / "main.py")
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api-gateway"}

def test_auth_service_health():
    """Kiểm tra healthcheck của auth-service"""
    app = load_app(ROOT_DIR / "services" / "auth-service" / "app" / "main.py")
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "auth-service"}

def test_poi_service_health_and_skeleton():
    """Kiểm tra healthcheck và endpoint /pois/all của poi-service"""
    app = load_app(ROOT_DIR / "services" / "poi-service" / "app" / "main.py")
    client = TestClient(app)
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "ok", "service": "poi-service"}

    res_all = client.get("/pois/all")
    assert res_all.status_code == 200
    data = res_all.json()
    assert "pois" in data
    assert "tour_routes" in data

def test_chatbot_service_health_and_skeleton():
    """Kiểm tra healthcheck và endpoint /chat/ask của chatbot-service"""
    app = load_app(ROOT_DIR / "services" / "chatbot-service" / "app" / "main.py")
    client = TestClient(app)
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "ok", "service": "chatbot-service"}

    res_chat = client.post("/chat/ask", json={"question": "Chùa Linh Ứng ở đâu?"})
    assert res_chat.status_code == 200
    assert "answer" in res_chat.json()

def test_data_pipeline_service_health_and_skeleton():
    """Kiểm tra healthcheck và pipeline status của data-pipeline-service"""
    app = load_app(ROOT_DIR / "services" / "data-pipeline-service" / "app" / "main.py")
    client = TestClient(app)
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "ok", "service": "data-pipeline-service"}

    res_status = client.get("/pipeline/status/poi-001")
    assert res_status.status_code == 200
    data = res_status.json()
    assert data["poi_id"] == "poi-001"
    assert data["status"] == "completed"

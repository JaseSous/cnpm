import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir / "backend" / "auth-service") not in sys.path:
    sys.path.insert(0, str(root_dir / "backend" / "auth-service"))

from app.services.security import hash_password

@pytest.mark.asyncio
async def test_e2e_complete_flow():
    """
    Kiểm thử tích hợp End-to-End (E2E) toàn trình:
    1. Staff đăng nhập và tạo vé tham quan chứa mã QR shorted_code
    2. Du khách quét mã vé shorted_code nhận JWT Access Token
    3. Du khách đồng bộ danh sách POI (lần 1: 200 OK, lần 2: 304 Not Modified)
    4. Du khách gửi câu hỏi tới Chatbot AI nhận câu trả lời RAG có sources
    5. Kiểm tra cơ chế FAQ Cache HIT khi cùng một câu hỏi được lặp lại
    """
    import uuid
    # 1. Test Auth Service
    import app.main as auth_main
    from app.database import AsyncSessionLocal as AuthSession, init_db as init_auth_db
    from app.models import User, TicketPackage

    username = f"staff_{uuid.uuid4().hex[:8]}"
    await init_auth_db()
    async with AuthSession() as session:
        # Seed staff & package
        staff = User(username=username, password_hash=hash_password("staff123"), role="staff", is_active=True)
        pkg = TicketPackage(package_name=f"Vé E2E {uuid.uuid4().hex[:4]}", price=50000, is_active=True)
        session.add_all([staff, pkg])
        await session.commit()
        await session.refresh(pkg)
        pkg_id = pkg.package_id

    auth_transport = ASGITransport(app=auth_main.app)
    async with AsyncClient(transport=auth_transport, base_url="http://test") as auth_client:
        # Staff Login
        login_res = await auth_client.post("/api/auth/login", json={"username": username, "password": "staff123"})
        assert login_res.status_code == 200
        staff_token = login_res.json()["access_token"]

        # Staff tạo vé
        ticket_res = await auth_client.post(
            "/api/auth/tickets",
            json={"package_id": pkg_id, "amount": 50000.0, "payment_method": "cash"},
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert ticket_res.status_code in (200, 201)
        shorted_code = ticket_res.json()["shorted_code"]
        assert len(shorted_code) == 10

        # Du khách kích hoạt mã vé
        verify_res = await auth_client.post("/api/auth/verify-code", json={"shorted_code": shorted_code})
        assert verify_res.status_code == 200
        customer_token = verify_res.json()["access_token"]
        assert customer_token is not None

    # 2. Test POI Service
    # Đổi sys.path sang poi-service
    sys.path.remove(str(root_dir / "backend" / "auth-service"))
    for mod in list(sys.modules.keys()):
        if mod.startswith("app"):
            del sys.modules[mod]
    sys.path.insert(0, str(root_dir / "backend" / "poi-service"))

    import app.main as poi_main
    from app.database import init_db as init_poi_db
    from app.seed_data import seed_real_pois

    await init_poi_db()
    await seed_real_pois()

    poi_transport = ASGITransport(app=poi_main.app)
    async with AsyncClient(transport=poi_transport, base_url="http://test") as poi_client:
        # Du khách tải danh sách POI lần 1
        pois_res1 = await poi_client.get(
            "/api/pois?lang=vi",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert pois_res1.status_code == 200
        data1 = pois_res1.json()
        assert len(data1["pois"]) >= 6
        current_ver = data1["data_version"]

        # Du khách tải danh sách POI lần 2 (since_version -> 304)
        pois_res2 = await poi_client.get(
            f"/api/pois?lang=vi&since_version={current_ver}",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert pois_res2.status_code == 304

    # 3. Test Chatbot AI Service
    sys.path.remove(str(root_dir / "backend" / "poi-service"))
    for mod in list(sys.modules.keys()):
        if mod.startswith("app"):
            del sys.modules[mod]
    sys.path.insert(0, str(root_dir / "backend" / "chatbot-service"))

    import app.main as chatbot_main
    chatbot_transport = ASGITransport(app=chatbot_main.app)
    async with AsyncClient(transport=chatbot_transport, base_url="http://test") as bot_client:
        chat_req = {"question": "Tượng Phật Bà Quan Âm cao bao nhiêu mét?", "lang": "vi"}

        # Lần 1: Trả lời mới (cached=False)
        chat_res1 = await bot_client.post(
            "/api/chatbot/ask",
            json=chat_req,
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert chat_res1.status_code == 200
        ans1 = chat_res1.json()
        assert ans1["cached"] is False
        assert "answer" in ans1

        # Lần 2: Cùng câu hỏi -> FAQ Cache HIT (cached=True)
        chat_res2 = await bot_client.post(
            "/api/chatbot/ask",
            json=chat_req,
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert chat_res2.status_code == 200
        ans2 = chat_res2.json()
        assert ans2["cached"] is True
        assert ans2["answer"] == ans1["answer"]

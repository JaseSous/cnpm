# Launcher khoi dong toan bo Backend Microservices + Frontend + Mo trinh duyet
import sys
import os
import time
import subprocess
import webbrowser
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent

SERVICES = [
    {"name": "Auth Service", "path": "services/auth-service/app/main.py", "port": 8001},
    {"name": "POI Service", "path": "services/poi-service/app/main.py", "port": 8002},
    {"name": "Chatbot Service", "path": "services/chatbot-service/app/main.py", "port": 8003},
    {"name": "Data Pipeline Service", "path": "services/data-pipeline-service/app/main.py", "port": 8004},
    {"name": "API Gateway", "path": "api-gateway/app/main.py", "port": 8000},
]

processes = []

def main():
    print("=" * 70)
    print("🚀 HE THONG THUYET MINH TU DONG DA NGON NGU - CHUA LINH UNG")
    print("=" * 70)

    # Xac dinh trinh thuc thi Python
    python_exe = sys.executable
    venv_py = ROOT_DIR / "venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        python_exe = str(venv_py)

    # 1. Khoi dong 5 backend services + gateway
    print("\n[*] Dang khoi dong 5 Backend Services + API Gateway...")
    for svc in SERVICES:
        app_dir = str(ROOT_DIR / Path(svc["path"]).parent.parent)
        cmd = [
            python_exe, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", str(svc["port"]),
            "--app-dir", app_dir
        ]
        p = subprocess.Popen(cmd, cwd=str(ROOT_DIR))
        processes.append((svc["name"], p))
        print(f"  [+] {svc['name']:<22} dang chay tai http://localhost:{svc['port']}")
        time.sleep(0.3)

    # 2. Khoi dong Frontend (Vite)
    print("\n[*] Dang khoi dong Frontend Client & Admin (Vite)...")
    frontend_dir = ROOT_DIR / "frontend"
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    p_front = subprocess.Popen([npm_cmd, "run", "dev", "--", "--port", "3000"], cwd=str(frontend_dir))
    processes.append(("Frontend (Vite)", p_front))

    time.sleep(2)

    print("\n" + "=" * 70)
    print("✅ HE THONG DA SAN SANG!")
    print("  - Client App (Du khach):   http://localhost:3000")
    print("  - Admin Dashboard:         http://localhost:3000/admin")
    print("  - API Gateway Docs:        http://localhost:8000/docs")
    print("  - Tai khoan Admin mac dinh: admin / admin123")
    print("=" * 70)
    print("  (Dang tu dong mo trinh duyet... Nhap Ctrl+C de dung toan bo he thong)")

    # 3. Tu dong mo trinh duyet
    try:
        webbrowser.open("http://localhost:3000")
    except Exception:
        pass

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Dang tat toan bo cac tien trinh...")
        for name, p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        for name, p in processes:
            try:
                p.wait(timeout=2)
            except Exception:
                pass
        print("✅ Da dung toan bo he thong.")

if __name__ == "__main__":
    main()

# Runner khởi động toàn bộ 5 Backend Services + API Gateway trong chế độ Local
import sys
import time
import subprocess
import signal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

SERVICES = [
    {"name": "Auth Service", "path": "services/auth-service/app/main.py", "port": 8001},
    {"name": "POI Service", "path": "services/poi-service/app/main.py", "port": 8002},
    {"name": "Chatbot Service", "path": "services/chatbot-service/app/main.py", "port": 8003},
    {"name": "Data Pipeline Service", "path": "services/data-pipeline-service/app/main.py", "port": 8004},
    {"name": "API Gateway", "path": "api-gateway/app/main.py", "port": 8000},
]

processes = []

def run_all():
    python_exe = sys.executable
    print("=" * 65)
    print("🚀 KHỞI ĐỘNG HỆ THỐNG MICROSERVICES - ỨNG DỤNG CHÙA LINH ỨNG")
    print("=" * 65)

    for svc in SERVICES:
        cmd = [
            python_exe, "-m", "uvicorn",
            f"app.main:app",
            "--host", "0.0.0.0",
            "--port", str(svc["port"]),
            "--app-dir", str(ROOT_DIR / Path(svc["path"]).parent.parent)
        ]
        p = subprocess.Popen(cmd, cwd=str(ROOT_DIR))
        processes.append((svc["name"], p, svc["port"]))
        print(f"  [+] {svc['name']:<22} đang chạy tại http://localhost:{svc['port']}")
        time.sleep(0.5)

    print("=" * 65)
    print("✅ TOÀN BỘ 5 SERVICES + API GATEWAY ĐÃ KHỞI CHẠY THÀNH CÔNG!")
    print("  - API Gateway Docs:   http://localhost:8000/docs")
    print("  - Aggregated Health:  http://localhost:8000/health")
    print("  - Nhấn Ctrl+C để dừng toàn bộ hệ thống")
    print("=" * 65)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Đang dừng các service...")
        for name, p, _ in processes:
            p.terminate()
        for name, p, _ in processes:
            p.wait()
        print("✅ Đã dừng toàn bộ dịch vụ.")

if __name__ == "__main__":
    run_all()

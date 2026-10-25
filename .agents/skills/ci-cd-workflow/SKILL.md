---
name: ci-cd-workflow
description: Hướng dẫn cấu hình, kiểm tra và vận hành quy trình CI/CD với GitHub Actions và Docker cho dự án.
---

# 🔄 SKILL: CẤU HÌNH & VẬN HÀNH CI/CD WORKFLOW

Skill này giải thích cấu trúc pipeline CI/CD hiện có tại `Source/.github/workflows/ci.yml`, cách kiểm tra cục bộ và cách mở rộng pipeline khi có thêm service mới.

---

## 1. Cấu Trúc Pipeline Hiện Tại (`ci.yml`)

Workflow được kích hoạt tự động khi có sự kiện `push` hoặc `pull_request` vào các nhánh `main` hoặc `master`:

```yaml
name: CI Pipeline

on:
  push:
    branches: [ master, main ]
  pull_request:
    branches: [ master, main ]

jobs:
  test-and-build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install fastapi uvicorn httpx pydantic python-jose[cryptography] passlib[bcrypt] numpy pytest

      - name: Run Backend Unit Tests (UC01, UC02, UC03, UC04)
        run: |
          pytest -v tests/test_backend.py

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Build Frontend (React + Vite + TypeScript)
        run: |
          cd frontend
          npm install
          npm run build

      - name: Verify Dockerfile builds
        run: |
          docker build -t api-gateway:latest ./api-gateway
          docker build -t auth-service:latest ./services/auth-service
          docker build -t poi-service:latest ./services/poi-service
          docker build -t chatbot-service:latest ./services/chatbot-service
          docker build -t data-pipeline-service:latest ./services/data-pipeline-service
          docker build -t frontend:latest ./frontend
```

---

## 2. Kiểm Tra Cục Bộ Trước Khi Đẩy Lên Git

Trước khi đẩy commit lên remote repository, nên kiểm tra:

1. **Kiểm tra unit tests:**
   ```bash
   pytest -v tests/test_backend.py
   ```
2. **Kiểm tra build frontend:**
   ```bash
   cd frontend
   npm run build
   ```
3. **Kiểm tra build docker images:**
   ```bash
   docker compose build
   ```

---

## 3. Quy Trình Mở Rộng Pipeline Khi Thêm Service

Khi tạo thêm service mới (ví dụ: `notification-service`):
1. Thêm các thư viện Python mới vào bước `Install Python dependencies` nếu có.
2. Thêm dòng kiểm tra build Dockerfile vào bước `Verify Dockerfile builds`:
   ```yaml
   docker build -t notification-service:latest ./services/notification-service
   ```
3. Đảm bảo toàn bộ test case kiểm thử service mới được chạy trong bước `pytest`.

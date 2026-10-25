# 🧠 BỘ NÃO CHUNG DỰ ÁN (.agents)
> **Học phần:** Công nghệ phần mềm — Đại học Sài Gòn (SGU)  
> **Đề tài:** Ứng dụng Thuyết minh tự động đa ngôn ngữ (Chùa Linh Ứng)  
> **Hướng triển khai:** Hướng 3 — Backend Microservices phân tán có CI/CD  

---

## 🎯 Giới Thiệu & Mục Đích

Thư mục `.agents/` đóng vai trò là **bộ não chung (Shared Brain)** cho mọi AI Agent và lập trình viên tham gia phát triển dự án. Thư mục này chuẩn hóa toàn bộ:
1. **Ngữ cảnh dự án (Context)**: Nguồn sự thật duy nhất về yêu cầu (PRD), kiến trúc microservices, cơ sở dữ liệu và tech stack.
2. **Quy tắc làm việc (Rules)**: Các nguyên tắc bất khả xâm phạm về quy trình phát triển, commit git và tuân thủ phạm vi.
3. **Kỹ năng tái sử dụng (Skills)**: Hướng dẫn chi tiết từng tác vụ chuẩn hóa (tạo service, commit, viết test, CI/CD).

---

## 🧭 Thứ Tự Đọc Bắt Buộc Dành Cho AI Agent

Mỗi khi bắt đầu một phiên làm việc hoặc nhận nhiệm vụ mới trong dự án, Agent **PHẢI** đọc tài liệu theo thứ tự sau:

```
[1. ĐỌC RULES]  ──>  [2. ĐỌC CONTEXT]  ──>  [3. TRA CỨU SKILLS]  ──>  [4. THỰC THI]
  Nắm chắc các         Hiểu kiến trúc,        Tra cứu quy trình       Tuân thủ PRD,
  nguyên tắc &         Use Cases & DB         chuẩn cho tác vụ        commit liên tục
  ràng buộc            từ PRD                                         và báo cáo
```

1. **Bước 1 — Đọc Quy Tắc Làm Việc (`.agents/rules/`)**:
   - Bắt đầu với [AGENTS.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/rules/AGENTS.md) để nắm 4 quy tắc cốt lõi: **Commit liên tục**, **Tuân thủ PRD**, **Xem lại trước khi thay đổi lớn**, **Không tự suy diễn**.
2. **Bước 2 — Nạp Ngữ Cảnh Dự Án (`.agents/context/`)**:
   - [project_overview.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/context/project_overview.md): Nắm mục tiêu, bối cảnh Chùa Linh Ứng và các mốc đánh giá (Tuần 7 giữa kỳ, Tuần 11-12 cuối kỳ).
   - [architecture.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/context/architecture.md): Nắm kiến trúc Microservices, sơ đồ giao tiếp, cổng kết nối và nguyên tắc Database-per-service.
   - [use_cases.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/context/use_cases.md): Nắm vững 4 Use Cases cốt lõi (UC01, UC02, UC03, UC04) cùng luồng rẽ nhánh và mã ngoại lệ.
   - [tech_stack.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/context/tech_stack.md): Tra cứu công nghệ thực tế đang sử dụng.
   - [glossary.md](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/context/glossary.md): Tra cứu định nghĩa các thuật ngữ kỹ thuật trong dự án.
3. **Bước 3 — Tra Cứu Kỹ Năng Khi Thao Tác (`.agents/skills/`)**:
   - [create-service](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/skills/create-service/SKILL.md): Khi cần tạo hoặc mở rộng một service backend mới.
   - [git-commit](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/skills/git-commit/SKILL.md): Khi tạo git commit theo chuẩn Conventional Commits.
   - [ci-cd-workflow](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/skills/ci-cd-workflow/SKILL.md): Khi cấu hình hoặc kiểm tra luồng CI/CD GitHub Actions và Docker.
   - [write-tests](file:///c:/Users/Jase%20Sous/Desktop/cnpm/.agents/skills/write-tests/SKILL.md): Khi viết unit test hoặc kịch bản kiểm thử cho backend.

---

## 📂 Sơ Đồ Cấu Trúc Thư Mục `.agents`

```
.agents/
├── README.md                      # Mục lục và hướng dẫn điều hướng (file này)
├── context/                       # Ngữ cảnh dự án trích xuất từ PRD & Codebase
│   ├── project_overview.md        # Bối cảnh môn học, mục tiêu, nhóm thực hiện, các mốc thời gian
│   ├── architecture.md            # Kiến trúc Microservices (Hướng 3), sơ đồ dịch vụ, port, DB
│   ├── tech_stack.md              # Công nghệ chi tiết (FastAPI, React, RabbitMQ, Redis, Postgres...)
│   ├── use_cases.md               # Chi tiết đặc tả 4 Use Cases: UC01, UC02, UC03, UC04
│   └── glossary.md                # Bảng thuật ngữ chuyên ngành và thuật ngữ dự án
├── rules/                         # Quy tắc bắt buộc cho mọi AI Agent
│   ├── AGENTS.md                  # Điểm truy cập quy tắc tổng hợp cho Antigravity IDE
│   ├── 01_git_commit_rules.md     # Quy tắc commit liên tục & Conventional Commits
│   ├── 02_prd_compliance.md       # Quy tắc bám sát PRD, không thêm/bớt tính năng
│   ├── 03_codebase_review.md      # Quy tắc đọc codebase & git log trước khi thay đổi lớn
│   └── 04_no_assumptions.md       # Quy tắc cấm suy diễn/bịa đặt, bắt buộc hỏi khi chưa rõ
└── skills/                        # Hướng dẫn tái sử dụng theo định dạng Skill chuẩn
    ├── create-service/
    │   └── SKILL.md               # Quy trình tạo mới một Microservice chuẩn hóa
    ├── git-commit/
    │   └── SKILL.md               # Quy trình commit vi mô và cú pháp chuẩn
    ├── ci-cd-workflow/
    │   └── SKILL.md               # Quy trình thiết lập và chạy CI/CD với GitHub Actions
    └── write-tests/
        └── SKILL.md               # Quy trình viết Unit Test và Integration Test backend
```

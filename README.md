# FrogHippo Phone — Hệ Thống Quản Lý Trung Tâm Sửa Chữa Điện Thoại
*Chuẩn phát triển AI-Augmented SDLC với kiến trúc phân tách độc lập Frontend & Backend.*

---

## 🏛️ Kiến Trúc Hệ Thống (Phân Tách Frontend & Backend)

Dự án được tổ chức theo chuẩn **Separation of Concerns (SoC)**, tách biệt hoàn toàn giữa tầng hiển thị giao diện người dùng và tầng xử lý nghiệp vụ/dữ liệu:

```
quan_ly_sua_chua/
│
├── frontend/                      # 🎨 TOÀN BỘ PHÂN HỆ GIAO DIỆN & STATIC ASSETS
│   ├── assets/                    # Logo, hình ảnh, tài nguyên tĩnh
│   │   ├── froghippo_logo.png
│   │   ├── hama_logo.png
│   │   └── logo.png
│   ├── index.html                 # Trang chủ & Hub điều hướng tất cả phân hệ
│   ├── khach_hang.html            # Cổng tra cứu tiến độ Khách hàng & AI Tư vấn
│   ├── le_tan.html                # Phân hệ Lễ tân & Tiếp nhận sửa chữa
│   ├── ky_thuat_vien.html         # Phân hệ Kỹ thuật viên (KTV)
│   ├── thu_ngan.html              # Phân hệ Thu ngân (Thu cọc 30% & Quyết toán)
│   ├── ke_toan.html               # Phân hệ Kế toán (Dòng tiền & Bảng lương)
│   └── admin.html                 # Phân hệ Quản trị viên (Hệ thống & Nhân sự)
│
├── backend/                       # ⚙️ TOÀN BỘ LOGIC BACKEND & API (FASTAPI)
│   ├── __init__.py
│   ├── config.py                  # Cấu hình đường dẫn kết nối Frontend & Assets
│   ├── main.py                    # Khởi tạo FastAPI App, CORS, Mount Routers
│   ├── database.py                # Kết nối MySQL & SessionLocal
│   ├── models.py                  # SQLAlchemy ORM Models (12 bảng)
│   ├── ai_service.py              # Dịch vụ AI (Gemini, OpenAI, Grounding Fallback)
│   ├── ai_service_extra.py        # Mở rộng tiện ích AI
│   ├── routers/                   # Routers phân hệ nghiệp vụ theo Router Pattern
│   │   ├── __init__.py
│   │   ├── admin.py               # API Quản trị & Nhân sự
│   │   ├── le_tan.py              # API Lễ tân & Tiếp nhận
│   │   ├── ky_thuat_vien.py       # API Kỹ thuật viên
│   │   ├── thu_ngan.py            # API Thu ngân & Ca làm việc
│   │   ├── ke_toan.py             # API Kế toán & Bảng lương
│   │   └── khach_hang.py          # API Cổng tra cứu Khách hàng
│   └── migrations/                # Scripts migration & cập nhật schema DB
│       ├── migrate_admin.py
│       └── migrate_mysql.py
│
├── docs/                          # 📚 Tài liệu chuẩn SDLC & Coding Standards
├── tests/                         # 🧪 Bộ kiểm thử tự động
├── main.py                        # 🚀 Entrypoint tương thích (Chuyển tiếp đến backend.main:app)
├── run.py                         # ⚡ Script khởi chạy nhanh tiện lợi
├── run_tests.py                   # 🧪 Script chạy kiểm thử
└── .env                           # 🔐 Cấu hình biến môi trường
```

---

## 🚀 Hướng Dẫn Khởi Chạy

### 1. Khởi động Server
Bạn có thể chạy bằng một trong hai cách tiện lợi:
```powershell
# Cách 1: Sử dụng runner tiện lợi
python run.py

# Cách 2: Sử dụng lệnh uvicorn tiêu chuẩn
python -m uvicorn main:app --reload --port 8000
```

### 2. Truy cập Giao diện Trực tuyến
- **Trang chủ & Hub điều hướng**: [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)
- **Cổng Khách hàng**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) hoặc [http://127.0.0.1:8000/khach-hang](http://127.0.0.1:8000/khach-hang)
- **Lễ tân**: [http://127.0.0.1:8000/le-tan](http://127.0.0.1:8000/le-tan)
- **Kỹ thuật viên**: [http://127.0.0.1:8000/ky-thuat-vien](http://127.0.0.1:8000/ky-thuat-vien)
- **Thu ngân**: [http://127.0.0.1:8000/thu-ngan](http://127.0.0.1:8000/thu-ngan)
- **Kế toán**: [http://127.0.0.1:8000/ke-toan](http://127.0.0.1:8000/ke-toan)
- **Admin Portal**: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
- **Tài liệu API tương tác**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

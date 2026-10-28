---
name: implementation
description: >
  Triển khai tính năng mới hoặc sửa lỗi cho hệ thống FrogHippo Phone.
  Tuân thủ kiến trúc modular (router pattern), đọc spec trước khi code,
  chạy lint sau khi code, báo cáo thay đổi, DỪNG nếu spec không rõ.
---

# Implementation Skill — FrogHippo Phone

## Bối Cảnh Kỹ Thuật

```
Project root: c:\Users\FPT\Downloads\quan_ly_sua_chua\
Entrypoint  : main.py (FastAPI app + router registration)
Models      : models.py (SQLAlchemy ORM)
DB session  : database.py → get_db() dependency injection
AI service  : ai_service.py (Gemini → OpenAI → Fallback)
Config      : .env (GEMINI_API_KEY, OPENAI_API_KEY, DB_*)
Dev server  : uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## File Structure Hiện Tại

```
quan_ly_sua_chua/
├── main.py             — Entry point, auth API, linh kiện CRUD, seed data
├── models.py           — 12 SQLAlchemy models
├── database.py         — DB engine, SessionLocal, get_db
├── ai_service.py       — AI service layer
├── le_tan.py           — Lễ Tân router
├── ky_thuat_vien.py    — KTV router
├── thu_ngan.py         — Thu Ngân router
├── ke_toan.py          — Kế Toán router (MỚI)
├── admin.py            — Admin router
├── khach_hang.py       — Cổng Khách Hàng router
├── *.html              — Frontend giao diện từng phân hệ
├── .env                — Environment variables (KHÔNG commit)
└── requirements.txt
```

## Objective

Triển khai tính năng theo specification đã được phê duyệt, tuân thủ kiến trúc
hiện có, và báo cáo kết quả rõ ràng.

## Inputs

Đọc trước khi bắt đầu code:
- `docs/coding-standards.md` — Bộ chuẩn mã nguồn và quy ước lập trình
- `docs/requirements.md` — FR đã approved
- `docs/architecture.md` — Kiến trúc đã approved
- `docs/database-design.md` — Schema đã approved
- File router hiện có nếu đang sửa chức năng hiện hữu

## Process

### 1. Đọc Specification

Trước khi viết bất kỳ dòng code nào, trả lời:
- FR nào đang triển khai?
- Component/router nào cần thêm hoặc sửa?
- Endpoint nào (METHOD + PATH)?
- Request/Response schema ra sao?
- DB tables nào bị tác động?

**Nếu không trả lời được → DỪNG và báo cáo thiếu spec.**

### 2. Kiểm Tra Architecture Compliance

Trước khi code, xác nhận:
- [ ] Endpoint mới có thuộc đúng router không? (VD: thu cọc → `le_tan.py`)
- [ ] Model đã có trong `models.py` chưa?
- [ ] Cột DB đã tồn tại chưa? (chạy `SHOW COLUMNS FROM ...`)
- [ ] AI call đi qua `ai_service.py`, không gọi trực tiếp API

### 3. Coding Standards

**Python (Backend)**:
```python
# ✅ Đúng: Dependency injection
@router.post("/api/le-tan/thu-coc/{ma_phieu}")
def thu_coc(ma_phieu: str, req: ThuCocRequest, db: Session = Depends(get_db)):
    ...

# ❌ Sai: Tạo session trực tiếp trong route
def thu_coc(ma_phieu: str):
    db = SessionLocal()  # KHÔNG làm thế này
    ...
```

```python
# ✅ Đúng: Pydantic validation
class ThuCocRequest(BaseModel):
    phuongThuc: str = "TienMat"
    tienKhachDua: Optional[float] = 0.0

# ❌ Sai: Không validate input
def thu_coc(phuong_thuc: str):
    ...
```

```python
# ✅ Đúng: HTTPException với detail rõ ràng
raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa!")

# ❌ Sai: Return None hoặc không xử lý lỗi
if not phieu:
    return None
```

**JavaScript (Frontend)**:
```javascript
// ✅ Đúng: Fetch với error handling
try {
    const res = await fetch('/api/...', { method: 'POST', ... });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Lỗi server');
} catch(e) {
    showToast(e.message, 'error');
}

// ❌ Sai: Không handle lỗi
const data = await fetch('/api/...').then(r => r.json());
```

```javascript
// ✅ Đúng: Format tiền VND
new Intl.NumberFormat('vi-VN', {style: 'currency', currency: 'VND'}).format(n)

// ❌ Sai: Concat chuỗi thủ công
n + " đ"
```

**HTML (UI)**:
- Dùng Tailwind CDN classes (đã có sẵn)
- Tất cả interactive element có unique `id`
- Form phải có `onsubmit="handleXxx(event)"` và `event.preventDefault()`
- Loading state: disable button + spinner khi fetch

### 4. AI Service Integration

```python
# ✅ Đúng: Qua ai_service layer
import ai_service
reply = ai_service.chat_tu_van_linh_kien(message, danh_muc)

# ❌ Sai: Gọi thẳng API trong route
import urllib.request
# ... gọi Gemini API trực tiếp trong router
```

```python
# ✅ Đúng: API key từ environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ❌ Sai: Hard-code API key
GEMINI_API_KEY = "AIzaSy..."
```

### 5. Database Operations

```python
# ✅ Đúng: Dùng ORM, không raw SQL injection
phieu = db.query(models.PhieuSuaChua)\
    .filter(models.PhieuSuaChua.maPhieu == ma_phieu).first()

# ❌ Sai: String concatenation SQL
query = f"SELECT * FROM phieu_sua_chua WHERE maPhieu = '{ma_phieu}'"
```

```python
# ✅ Đúng: Commit sau khi thay đổi
phieu.daDatCoc = True
db.commit()
db.refresh(phieu)

# ❌ Sai: Quên commit
phieu.daDatCoc = True
# (không commit → dữ liệu không lưu)
```

### 6. Chạy Verification Sau Khi Code

```bash
# 1. Kiểm tra Python syntax
python -c "import <module_name>; print('OK')"

# 2. Restart server và test endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/..." `
    -Method POST `
    -ContentType "application/json" `
    -Body '{"test": "data"}' `
    -UseBasicParsing | Select-Object StatusCode, Content

# 3. Kiểm tra DB thay đổi
python -c "
from database import engine
from sqlalchemy import text, inspect
inspector = inspect(engine)
print(inspector.get_columns('phieu_sua_chua'))
"
```

### 7. Báo Cáo Thay Đổi

Sau khi hoàn thành, báo cáo:
```
FILES CREATED:
- ke_toan.py (route mới)
- ke_toan.html (giao diện mới)

FILES MODIFIED:
- models.py: Thêm class BangLuong, thêm cột tienDatCoc/daDatCoc
- main.py: import ke_toan, app.include_router(ke_toan.router)
- ai_service.py: Thêm chat_tu_van_linh_kien(), generate_deposit_message()

DATABASE CHANGES:
- ALTER TABLE phieu_sua_chua ADD COLUMN tienDatCoc FLOAT DEFAULT 0.0
- ALTER TABLE phieu_sua_chua ADD COLUMN daDatCoc TINYINT(1) DEFAULT 0
- CREATE TABLE bang_luong (...)

ENDPOINTS ADDED:
- POST /api/le-tan/thu-coc/{ma_phieu}
- POST /api/le-tan/quyet-toan/{ma_phieu}
- POST /api/le-tan/chatbot-linh-kien
- GET/POST /api/ke-toan/*
```

## Rules — BẮT BUỘC

- ❌ KHÔNG thay đổi requirements hoặc architecture đã approved
- ❌ KHÔNG hard-code API keys
- ❌ KHÔNG tạo session DB thủ công trong route (dùng Depends(get_db))
- ❌ KHÔNG gọi AI API trực tiếp từ route (phải qua ai_service.py)
- ✅ DỪNG và báo cáo nếu specification không đủ để triển khai
- ✅ Báo cáo đầy đủ files changed + DB changes sau khi hoàn thành
- ✅ Kiểm tra import syntax trước khi báo hoàn thành

## Stopping Conditions — KHI NÀO PHẢI DỪNG

Agent tốt phải biết khi nào cần dừng:
1. **Spec không rõ**: FR đang triển khai không xác định rõ behavior
2. **Conflict**: Yêu cầu mới mâu thuẫn với code hiện có
3. **DB không đồng bộ**: Column cần thiết chưa tồn tại trong MySQL
4. **Dependency missing**: Import thất bại, package chưa cài
5. **Test fails**: Endpoint trả 500 sau khi code

→ Khi gặp các tình huống trên: **DỪNG, mô tả vấn đề, hỏi người dùng quyết định**

## Outputs

- Code đã implement
- Test evidence (curl/PowerShell output)
- Danh sách files thay đổi
- DB changes log

---
name: architecture-design
description: >
  Thiết kế kiến trúc phần mềm cho hệ thống FrogHippo Phone từ yêu cầu đã được phê duyệt.
  Đảm bảo traceability từ yêu cầu → thành phần kiến trúc, phù hợp stack
  FastAPI + SQLAlchemy + MySQL + Tailwind CSS + AI (Gemini/OpenAI).
---

# Architecture Design Skill — FrogHippo Phone

## Bối Cảnh Kỹ Thuật Cố Định

```
Backend  : FastAPI (Python 3.x) + Uvicorn
ORM      : SQLAlchemy (declarative base)
Database : MySQL (localhost:3306, database: quan_ly_sua_chua)
Frontend : HTML5 + Vanilla JS + Tailwind CSS CDN
AI       : Google Gemini API (primary) → OpenAI API (fallback) → Mock (offline)
Auth     : Token-based (in-memory, non-JWT hiện tại)
File Srv : FastAPI StaticFiles (HTML/CSS/JS phục vụ trực tiếp)
```

## Objective

Chuyển đổi yêu cầu đã phê duyệt thành kiến trúc phần mềm có cấu trúc rõ ràng,
với traceability đầy đủ từ FR/BR → component.

## Inputs

Chỉ đọc tài liệu đã được APPROVED:
- `docs/requirements.md`
- `docs/user-stories.md`
- `docs/acceptance-criteria.md`
- `docs/business-rules.md`

## Process

### 1. Xác Định Architectural Style

Mô tả lý do lựa chọn và đánh đổi:
- **Monolithic RESTful** (hiện tại): phù hợp quy mô nhỏ, 1 server
- **Router-based Modular**: mỗi phân hệ là 1 FastAPI router riêng
- **Separation of Concerns**: HTML/JS frontend tách khỏi Python backend

### 2. Xác Định Các Module Chính

Mỗi module phải có:
- Tên và trách nhiệm rõ ràng
- Router file tương ứng (`.py`)
- Giao diện HTML tương ứng (`.html`)
- Danh sách FR/BR mà module đáp ứng

```
MODULE MAP (thực tế dự án):
┌─────────────────────────────────────────────────────────────┐
│  main.py          — Entry point, CORS, seed data, auth API  │
│  models.py        — SQLAlchemy ORM models (12 bảng)         │
│  database.py      — DB connection, SessionLocal             │
│  ai_service.py    — Gemini/OpenAI/Fallback service layer    │
├─────────────────────────────────────────────────────────────┤
│  le_tan.py        — Lễ Tân router (phiếu, cọc, tin AI)     │
│  ky_thuat_vien.py — KTV router (trạng thái, LK, AI)        │
│  thu_ngan.py      — Thu Ngân router (HĐ, ca, biên lai)     │
│  ke_toan.py       — Kế Toán router (lương, dòng tiền)      │
│  admin.py         — Admin router (CRUD nhân viên, LK, BC)  │
│  khach_hang.py    — Cổng KH router (tra cứu, đánh giá)     │
└─────────────────────────────────────────────────────────────┘
```

### 3. Luồng Dữ Liệu Chính

Vẽ data flow cho từng luồng nghiệp vụ quan trọng:

```
LUỒNG AI CHATBOT:
HTTP POST /api/le-tan/chatbot-linh-kien
→ le_tan.py router
→ DB query: SELECT * FROM linh_kien
→ ai_service.chat_tu_van_linh_kien(message, danh_muc)
→ Build system_prompt (grounded trên dữ liệu thật)
→ Gemini API → OpenAI API → Keyword Fallback
→ Return {reply, tongSoLinhKien}

LUỒNG THU CỌC 30%:
POST /api/le-tan/thu-coc/{ma_phieu}
→ Validate phiếu tồn tại, chưa cọc
→ Tính tong_hoa_don từ chi_tiet_sua_chua
→ tien_coc = round(tong * 0.3)
→ UPDATE phieu: tienDatCoc, daDatCoc=True
→ INSERT thong_bao_khach_hang (ghi nhận)
→ Return {tienDatCoc, tongHoaDon, tienConLai70}
```

### 4. Ranh Giới Bảo Mật (Security Boundaries)

```
INTERNET (Khách Hàng)
    │ HTTPS (production) / HTTP localhost (dev)
    ▼
FastAPI App (Port 8000)
    │ CORS middleware
    │ Role-based route guards (require_roles)
    ▼
SQLAlchemy ORM ── MySQL (localhost)
    │
    └── ai_service.py ── Gemini/OpenAI API (external)
                         API Key từ .env KHÔNG từ code
```

### 5. Quyết Định Kiến Trúc (Architectural Decisions)

Dùng định dạng ADR (Architecture Decision Record):
```
ADR-001: [Tiêu đề]
Status: Accepted / Deprecated / Superseded
Context: Tại sao vấn đề này phát sinh?
Decision: Quyết định chọn gì?
Rationale: Lý do?
Consequences: Hệ quả, đánh đổi?
```

Ví dụ ADR bắt buộc ghi lại:
- ADR-001: Chọn Monolithic thay vì Microservices
- ADR-002: AI fallback 3 cấp (Gemini → OpenAI → Keyword-based)
- ADR-003: Chatbot grounded trên CSDL thật (anti-hallucination)
- ADR-004: Frontend HTML thuần (không React/Vue) cho đơn giản

### 6. Component-to-Requirement Traceability

Bắt buộc liệt kê bảng traceability:
```
FR-ID    │ Component / Module          │ Endpoint
──────────┼─────────────────────────────┼──────────────────────────
FR-001   │ le_tan.py                   │ POST /phieu-sua/
FR-061   │ le_tan.py                   │ POST /api/le-tan/thu-coc/
FR-081   │ ai_service.py + le_tan.py   │ POST /api/le-tan/chatbot-linh-kien
FR-121   │ ke_toan.py                  │ POST /api/ke-toan/tao-bang-luong
```

### 7. External Systems

Xác định hệ thống ngoài cần kết nối:
- Google Gemini API (`generativelanguage.googleapis.com`)
- OpenAI API (`api.openai.com`) — fallback
- MySQL Server (localhost)
- (Future) Zalo OA API / SMTP cho gửi thật

## Rules — BẮT BUỘC

- ❌ KHÔNG triển khai source code
- ❌ KHÔNG thay đổi yêu cầu đã được phê duyệt
- ❌ KHÔNG đưa vào công nghệ không cần thiết
- ✅ Mọi quyết định kiến trúc có rationale rõ ràng
- ✅ Mọi FR quan trọng có ít nhất 1 component đáp ứng

## Outputs

```
docs/architecture.md              — Kiến trúc tổng quan & module map
docs/architecture-decisions.md    — Danh sách ADR
docs/data-flow.md                 — Luồng dữ liệu chính
docs/component-map.md             — FR → Component traceability
```

## Verification

- [ ] Mọi FR chính được ít nhất 1 component đáp ứng
- [ ] Luồng 30%/70% có data flow riêng
- [ ] Luồng AI chatbot có data flow riêng
- [ ] Security boundaries được vẽ rõ
- [ ] ADR cho các quyết định quan trọng

## Human Gate

```
Architecture Review
Status: APPROVED / NEEDS_REVISION
Checked:
  [X] FR → Component mapping đầy đủ
  [X] AI grounding mechanism được thiết kế
  [X] Security boundary rõ ràng (API key, CORS, roles)
  [X] Data flow cho luồng cọc 30%/70%
  [X] Không có công nghệ thừa
Approved for: Database Design
```

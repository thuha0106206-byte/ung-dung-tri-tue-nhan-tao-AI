---
name: database-design
description: >
  Thiết kế và xác minh cơ sở dữ liệu MySQL cho hệ thống FrogHippo Phone.
  Kiểm tra schema thực tế trong models.py, đảm bảo chuẩn hóa, FK integrity,
  và phản ánh đúng nghiệp vụ (đặc biệt tienDatCoc, daDatCoc, bang_luong).
---

# Database Design Skill — FrogHippo Phone

## Bối Cảnh CSDL Hiện Tại

```
Database: quan_ly_sua_chua (MySQL, localhost:3306)
ORM: SQLAlchemy (models.py)
Migration: Thủ công bằng ALTER TABLE (không dùng Alembic)
```

**12 Bảng hiện có** (đọc từ `models.py`):
```
1.  nhan_vien          — Nhân viên (4 vai trò)
2.  khach_hang         — Khách hàng
3.  phieu_sua_chua     — Phiếu sửa chữa (+ tienDatCoc, daDatCoc)
4.  chi_tiet_sua_chua  — Linh kiện trong phiếu (bảng trung gian n-n)
5.  linh_kien          — Kho linh kiện
6.  phieu_nhap_kho     — Nhập kho linh kiện
7.  hoa_don            — Hóa đơn quyết toán
8.  bao_hanh           — Phiếu bảo hành
9.  thong_bao_khach_hang — Lịch sử tin nhắn AI gửi khách
10. danh_gia_dich_vu   — Đánh giá 1-5 sao của khách
11. khieu_nai          — Khiếu nại / góp ý
12. bang_luong         — Bảng lương nhân viên theo tháng (MỚI)
```

## Objective

Xem xét schema CSDL hiện tại, phát hiện vấn đề và đảm bảo schema đáp ứng
đầy đủ yêu cầu nghiệp vụ đã được phê duyệt.

## Inputs

- `models.py` — SQLAlchemy model hiện tại (nguồn sự thật)
- `docs/requirements.md` — FR đã phê duyệt
- `docs/architecture.md` — Kiến trúc đã phê duyệt
- `docs/business-rules.md` — BR đặc thù

## Process

### 1. Đọc Và Phân Tích models.py

Đọc toàn bộ `models.py` và lập danh sách:
- Tên bảng (tablename)
- Các cột với type, nullable, default, constraint
- Primary Key, Foreign Key
- Relationships

### 2. Kiểm Tra Chuẩn Hóa (Normalization)

Kiểm tra từng bảng đạt chuẩn 3NF:
- Không có cột lặp (repeating groups)
- Mọi thuộc tính phụ thuộc vào toàn bộ PK
- Không có phụ thuộc bắc cầu

Đặc biệt chú ý:
```sql
phieu_sua_chua
├── tienDatCoc  FLOAT DEFAULT 0.0  -- Đảm bảo có cột này
├── daDatCoc    BOOLEAN DEFAULT 0   -- Đảm bảo có cột này
└── Kiểm tra ALTER TABLE đã chạy chưa
```

### 3. Kiểm Tra FK Integrity

```
phieu_sua_chua.maKH → khach_hang.maKH
phieu_sua_chua.maKTV → nhan_vien.maNV
chi_tiet_sua_chua.maPhieu → phieu_sua_chua.maPhieu
chi_tiet_sua_chua.maLK → linh_kien.maLK
hoa_don.maPhieu → phieu_sua_chua.maPhieu
hoa_don.maThuNgan → nhan_vien.maNV
bang_luong.maNV → nhan_vien.maNV
bao_hanh.maPhieu → phieu_sua_chua.maPhieu
thong_bao_khach_hang.maPhieu → phieu_sua_chua.maPhieu
```

### 4. Kiểm Tra Constraints & Indexes

Cho từng bảng, xác nhận:
- PK được định nghĩa
- FK được định nghĩa (SQLAlchemy ForeignKey)
- NOT NULL cho trường bắt buộc
- Unique ở nơi cần thiết (VD: tenDangNhap trong nhan_vien)

### 5. Kiểm Tra Hỗ Trợ Nghiệp Vụ Đặc Thù

```
BR-001 (Cọc 30%):
  phieu_sua_chua.tienDatCoc EXISTS? ✓/✗
  phieu_sua_chua.daDatCoc EXISTS? ✓/✗
  Có thể tính: chi_tiet_sua_chua JOIN để ra tong_hoa_don? ✓/✗

BR-008 (Bảng lương):
  bang_luong.luongCoBan EXISTS? ✓/✗
  bang_luong.thuong EXISTS? ✓/✗
  bang_luong.thucLinh EXISTS? ✓/✗
  bang_luong.trangThai IN ('CHO_DUYET','DA_PHAT') ✓/✗

Chatbot (NFR-002 anti-hallucination):
  linh_kien.tenLK EXISTS? ✓/✗
  linh_kien.giaBan EXISTS? ✓/✗
  linh_kien.soLuongTon EXISTS? ✓/✗
```

### 6. Phát Hiện Vấn Đề & Đề Xuất

Ghi lại mọi vấn đề phát hiện:
```
ISSUE-DB-001: [Mô tả vấn đề]
Severity: HIGH / MEDIUM / LOW
Affected table: [tên bảng]
Current state: [trạng thái hiện tại]
Recommendation: [đề xuất sửa đổi]
Fix: ALTER TABLE ... ADD COLUMN ... / CREATE INDEX ...
```

### 7. ERD (Entity Relationship Diagram - Text Form)

```
nhan_vien [PK: maNV]
    │1
    │N
phieu_sua_chua [PK: maPhieu, FK: maKH, maKTV]
    │1
    │N
chi_tiet_sua_chua [PK: maPhieu+maLK (composite), FK: maLK]
    │N
    │1
linh_kien [PK: maLK]

phieu_sua_chua [1] ─── [1] hoa_don
phieu_sua_chua [1] ─── [N] thong_bao_khach_hang
phieu_sua_chua [1] ─── [N] bao_hanh
nhan_vien [1] ─── [N] bang_luong
```

### 8. SQL Schema Verification Script

Tạo script kiểm tra schema có khớp với models.py không:
```sql
-- Kiểm tra cột tienDatCoc tồn tại
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'quan_ly_sua_chua'
AND TABLE_NAME = 'phieu_sua_chua'
AND COLUMN_NAME IN ('tienDatCoc', 'daDatCoc');

-- Kiểm tra bảng bang_luong tồn tại
SHOW TABLES LIKE 'bang_luong';

-- Kiểm tra FK constraints
SELECT CONSTRAINT_NAME, TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'quan_ly_sua_chua'
AND REFERENCED_TABLE_NAME IS NOT NULL;
```

## Rules — BẮT BUỘC

- ❌ KHÔNG viết Flask/FastAPI source code
- ❌ KHÔNG thay đổi yêu cầu hoặc kiến trúc đã approved
- ✅ Chỉ thiết kế/xem xét CSDL
- ✅ Sử dụng parameterized queries (không string concatenation)
- ✅ Ghi rõ migration script khi thêm cột mới
- ✅ Xác nhận script ALTER TABLE đã chạy thành công

## Outputs

```
docs/database-design.md       — Schema đầy đủ, ERD, FK map
database/schema.sql           — SQL schema tạo từ đầu (bao gồm MỚI)
database/migration_log.md     — Lịch sử các ALTER TABLE đã chạy
database/verification.sql     — Script kiểm tra schema
```

## Verification Checklist

- [ ] Tất cả 12 bảng có trong models.py và MySQL đồng bộ
- [ ] `tienDatCoc` và `daDatCoc` tồn tại trong `phieu_sua_chua`
- [ ] `bang_luong` tồn tại với đủ cột lương
- [ ] FK từ `bang_luong.maNV` → `nhan_vien.maNV`
- [ ] Không có SQL injection risk trong queries
- [ ] Migration log ghi lại đủ ALTER TABLE history

## Human Gate

```
Database Design Review
Status: APPROVED / NEEDS_REVISION
Checked:
  [X] 12 bảng đồng bộ models.py ↔ MySQL
  [X] tienDatCoc + daDatCoc confirmed in DB
  [X] bang_luong confirmed in DB
  [X] FK integrity verified
  [X] No injection risks
Approved for: Implementation
```

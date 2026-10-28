---
name: code-review
description: >
  Đánh giá và kiểm tra mã nguồn (Code Review) cho dự án FrogHippo Phone.
  Đảm bảo tuân thủ kiến trúc phân tầng FastAPI, chuẩn Clean Code, bảo mật xác thực RBAC,
  và tối ưu hóa truy vấn SQLAlchemy ORM.
---

# Code Review Skill — FrogHippo Phone

## Mục Tiêu

Đảm bảo mã nguồn backend (FastAPI/Python) và frontend (HTML/JS/Tailwind) đạt tiêu chuẩn chất lượng cao, dễ bảo trì, an toàn bảo mật, và đáp ứng chính xác nghiệp vụ trung tâm sửa chữa điện thoại theo đúng tài liệu chuẩn mã nguồn: [`docs/coding-standards.md`](file:///c:/Users/FPT/Downloads/quan_ly_sua_chua/docs/coding-standards.md).

---

## Tiêu Chí Đánh Giá Cốt Lõi

### 1. Kiến Trúc & Cấu Trúc Mã Nguồn (Architecture & Organization)
- [ ] **Router Pattern**: Các endpoint phải được chia theo router nghiệp vụ (`routers/auth.py`, `routers/tickets.py`, `routers/inventory.py`, `routers/accounting.py`, `routers/ai.py`). Không nhồi nhét logic vào `main.py`.
- [ ] **Separation of Concerns**: Tách biệt rõ ràng giữa Router (HTTP handling) -> Service/CRUD (Business logic) -> Model/Schema (Data definitions).
- [ ] **Dependency Injection**: Sử dụng `Depends(get_db)` cho database session và `Depends(get_current_user)` cho auth context.

### 2. Xử Lý Nghiệp Vụ Cốt Lõi (Business Logic Integrity)
- [ ] **Đặt cọc 30%**: Kiểm tra tính toán `tien_dat_coc = round(tong_tien * 0.3)` và cờ `da_dat_coc` trước khi chuyển trạng thái sang `dang_sua`.
- [ ] **Quyết toán 70%**: Số tiền thanh toán cuối cùng = `tong_tien - tien_dat_coc`.
- [ ] **Trạng thái phiếu sửa chữa**: Luồng chuyển trạng thái hợp lệ:
  `tiep_nhan` → `kiem_tra_bao_gia` → `cho_khach_duyet` → `da_coc_cho_sua` → `dang_sua` → `hoan_thanh` → `da_tra_may`.
- [ ] **Kho & Linh kiện**: Trừ tồn kho (`so_luong_ton`) ngay khi phiếu chuyển sang trạng thái dùng linh kiện hoặc hoàn thành. Ngăn chặn số lượng tồn bị âm.
- [ ] **Bảng lương KTV & Nhân viên**: Tính đúng hoa hồng/thưởng theo phiếu sửa chữa hoàn thành và lương cứng.

### 3. Cơ Sở Dữ Liệu & ORM (SQLAlchemy)
- [ ] **Transaction Management**: Các thao tác cập nhật nhiều bảng (ví dụ: tạo hóa đơn + trừ kho + cập nhật trạng thái phiếu) phải được bọc trong database transaction (`db.commit()`, `db.rollback()` khi có lỗi).
- [ ] **Tránh N+1 Query**: Sử dụng `joinedload` hoặc `selectinload` cho các quan hệ (vd: Phiếu sửa chữa + Khách hàng + KTV + Chi tiết linh kiện).
- [ ] **Index hợp lý**: Đảm bảo các trường thường xuyên tìm kiếm có Index (`so_dien_thoai`, `ma_phieu`, `trang_thai`).

### 4. Bảo Mật & Xác Thực (Security & Auth)
- [ ] **RBAC (Role-Based Access Control)**: Endpoint quản trị, duyệt lương, kho phải kiểm tra đúng vai trò (`admin`, `ke_toan`, `thu_ngan`, `le_tan`, `ky_thuat_vien`).
- [ ] **Mật khẩu**: Mã hóa mật khẩu với `bcrypt` (không bao giờ lưu plain text).
- [ ] **Token JWT**: Kiểm tra thời gian hết hạn (`exp`) và thuật toán ký an toàn (`HS256`).
- [ ] **Validation đầu vào**: Luôn dùng Pydantic schema để validate input, ngăn chặn injection và payload độc hại.

### 5. Frontend & UI/UX Standards
- [ ] **Responsive & Modern**: Giao diện Tailwind CSS nhất quán, hiển thị tốt trên Desktop và Mobile/Tablet.
- [ ] **User Feedback**: Luôn hiển thị loading spinner, toast thông báo thành công/thất bại, modal xác nhận trước các hành động xóa hoặc thanh toán.
- [ ] **Data Sanitization**: Tránh `innerHTML` với dữ liệu nhập từ người dùng mà không sanitize (chống XSS).

---

## Mẫu Báo Cáo Code Review

Khi thực hiện review, xuất báo cáo theo mẫu sau:

```markdown
# Báo Cáo Code Review: [Tên File / Module]

## 1. Tổng Quan
- **Đánh giá chung**: [Đạt / Cần chỉnh sửa / Nghiêm trọng]
- **Tác động nghiệp vụ**: [Thấp / Trung bình / Cao]

## 2. Điểm Tốt (Strengths)
- ...

## 3. Vấn Đề Cần Sửa (Issues & Improvements)
| Mức độ | Vị trí (File:Line) | Vấn đề | Đề xuất giải pháp |
|---|---|---|---|
| 🔴 Critical | `routers/tickets.py:45` | Thiếu kiểm tra quyền của KTV | Thêm dependency `require_roles(['ktv', 'admin'])` |
| 🟡 Warning | `services/inventory.py:80` | Có nguy cơ âm kho khi 2 người đặt cùng lúc | Thêm lock hoặc atomic update |
| 🟢 Info | `templates/ky_thuat_vien.html:120` | Hardcode màu sắc | Chuyển sang class Tailwind đồng bộ |

## 4. Kết Luận & Hành Động Tiếp Theo
- [ ] Các bước cần lập trình viên khắc phục trước khi merge.
```

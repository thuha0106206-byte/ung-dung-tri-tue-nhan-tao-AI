# BỘ CHUẨN MÃ NGUỒN & QUY ƯỚC LẬP TRÌNH (CODING STANDARDS)
**Dự án**: Hệ Thống Quản Lý Trung Tâm Sửa Chữa Điện Thoại — FrogHippo Phone  
**Áp dụng cho**: Lập trình viên, AI Agents (Codex, Antigravity, Copilot)  
**Phiên bản**: 1.0 — Chuẩn AI-Augmented SDLC  

---

## 1. MỤC TIÊU & NGUYÊN TẮC CỐT LÕI

1. **Tính Nhất Quán (Consistency)**: Mọi module dù do con người hay AI sinh ra đều phải tuân thủ cùng một văn phong, cấu trúc và quy chuẩn định danh.
2. **Dễ Đọc & Dễ Bảo Trì (Readability & Maintainability)**: Ưu tiên mã nguồn rõ ràng, tường minh (Explicit is better than implicit), chú thích đầy đủ logic nghiệp vụ phức tạp.
3. **Traceability (Khả năng truy vết)**: Mã nguồn phải ánh xạ trực tiếp đến tài liệu đặc tả yêu cầu (FR/NFR), thiết kế kiến trúc và mô hình CSDL.
4. **Fail-safe & Defensive Programming**: Luôn kiểm tra điều kiện biên, xử lý ngoại lệ chặt chẽ, kiểm soát transaction cơ sở dữ liệu để bảo toàn dữ liệu tài chính (tiền cọc 30%, doanh thu, kho linh kiện).

---

## 2. QUY CHUẨN CẤU TRÚC THƯ MỤC & FILE

```
quan_ly_sua_chua/
├── .agents/                    # Bộ AI Skills theo chuẩn AI-Augmented SDLC
│   └── skills/
├── docs/                       # Tài liệu đặc tả kỹ thuật & nghiệp vụ
│   ├── coding-standards.md     # File chuẩn mã nguồn này
│   ├── requirements.md         # Đặc tả yêu cầu phần mềm
│   ├── architecture.md         # Thiết kế kiến trúc
│   └── database-design.md     # Thiết kế CSDL
├── routers/                    # Router theo từng phân hệ nghiệp vụ (Router Pattern)
│   ├── __init__.py
│   ├── auth_router.py          # Đăng nhập, xác thực JWT, phân quyền RBAC
│   ├── ticket_router.py        # Quản lý phiếu tiếp nhận, sửa chữa, cọc 30%
│   ├── inventory_router.py     # Quản lý linh kiện, nhập/xuất kho
│   ├── accounting_router.py    # Quản lý thu chi, bảng lương KTV, đối soát
│   ├── customer_router.py      # Cổng tra cứu tiến độ công khai cho khách
│   └── ai_router.py            # AI chẩn đoán, soạn tin Lễ tân, Chatbot
├── services/                   # Business logic xử lý độc lập
├── models.py                   # SQLAlchemy ORM Models (12 bảng CSDL)
├── schemas.py                  # Pydantic Schemas (Request/Response validation)
├── database.py                 # Cấu hình engine kết nối MySQL & get_db session
├── main.py                     # Entry point FastAPI, CORS, mount routes
├── templates/ hoặc static/     # Giao diện Frontend (HTML, CSS, JS)
│   ├── index.html              # Trang chủ & Cổng thông tin khách hàng
│   ├── le_tan.html             # Dashboard Lễ tân (tiếp nhận máy, thu cọc)
│   ├── ky_thuat_vien.html      # Dashboard KTV (báo giá, cập nhật tiến độ)
│   ├── thu_ngan.html           # Dashboard Thu ngân (thanh toán 70%, hóa đơn)
│   ├── ke_toan.html            # Dashboard Kế toán (lương, dòng tiền kho)
│   └── admin.html              # Quản trị viên
├── tests/                      # Bộ kiểm thử tự động (pytest)
├── .env                        # Biến môi trường (DATABASE_URL, SECRET_KEY, GEMINI_API_KEY)
├── requirements.txt            # Danh sách dependencies
└── README.md                   # Hướng dẫn cài đặt & vận hành
```

---

## 3. QUY CHUẨN BACKEND (PYTHON & FASTAPI)

### 3.1. Tuân Thủ PEP 8 & Định Danh (Naming Conventions)

| Đối tượng | Quy tắc | Ví dụ chuẩn | Ví dụ sai |
|---|---|---|---|
| **File / Module** | `snake_case.py` | `ticket_router.py`, `ai_service.py` | `TicketRouter.py`, `ai-service.py` |
| **Class (Model/Schema)** | `PascalCase` | `PhieuSuaChua`, `LinhKien`, `UserCreate` | `phieu_sua_chua`, `tbl_LinhKien` |
| **Function / Method** | `snake_case()` | `tinh_tien_dat_coc()`, `get_ticket_by_id()` | `tinhTienDatCoc()`, `GetTicket()` |
| **Variable / Parameter** | `snake_case` | `so_dien_thoai`, `tien_dat_coc`, `db` | `soDienThoai`, `TienDatCoc` |
| **Constant (Hằng số)** | `UPPER_CASE` | `TI_LE_COC_MAC_DINH = 0.3`, `JWT_EXPIRE_MIN` | `tiLeCoc = 0.3`, `jwt_expire` |
| **Endpoint URL** | `kebab-case`, số nhiều | `/api/tickets`, `/api/inventory/parts` | `/api/get_ticket`, `/api/Parts` |

### 3.2. Ép Kiểu Dữ Liệu (Type Hints Bắt Buộc 100%)
Mọi hàm trong Backend phải có chú thích kiểu dữ liệu tham số và giá trị trả về:
```python
# CHUẨN:
def tinh_tien_dat_coc(tong_tien: float, ti_le: float = 0.3) -> float:
    """Tính số tiền đặt cọc làm tròn đến hàng nghìn đồng."""
    return round(tong_tien * ti_le, -3)

# SAI:
def tinh_tien_dat_coc(tong_tien, ti_le=0.3):
    return tong_tien * ti_le
```

### 3.3. Tách Biệt Schemas & Validation (Pydantic)
- Không bao giờ trả trực tiếp SQLAlchemy Model nhạy cảm ra API (chứa mật khẩu băm, token bí mật).
- Luôn định nghĩa rõ các Schema:
  - `EntityBase`: Thuộc tính chung.
  - `EntityCreate`: Dùng khi tạo mới (POST).
  - `EntityUpdate`: Dùng khi cập nhật từng phần (PUT/PATCH, optional fields).
  - `EntityResponse`: Trả về cho client (`from_attributes = True`).

```python
class TicketCreate(BaseModel):
    khach_hang_id: int
    thiet_bi_id: int
    mo_ta_loi: str = Field(..., min_length=5, description="Mô tả triệu chứng lỗi")
    ghi_chu_tiep_nhan: Optional[str] = None

class TicketResponse(BaseModel):
    id: int
    ma_phieu: str
    trang_thai: str
    tong_tien: float
    tien_dat_coc: float
    da_dat_coc: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

### 3.4. Quản Lý Database Transaction & ORM
- Luôn inject DB session thông qua `db: Session = Depends(get_db)`.
- Khi thực hiện các hành động đa bảng (tạo hóa đơn cọc + cập nhật trạng thái phiếu + ghi nhật ký kho), **bắt buộc** dùng transaction an toàn:
```python
try:
    # 1. Cập nhật phiếu
    ticket.da_dat_coc = True
    ticket.trang_thai = "dang_sua"
    
    # 2. Tạo hóa đơn cọc 30%
    hoa_don_coc = HoaDon(
        phieu_id=ticket.id,
        so_tien=ticket.tien_dat_coc,
        loai_thanh_toan="tien_coc_30",
        trang_thai="da_thanh_toan"
    )
    db.add(hoa_don_coc)
    
    # 3. Commit toàn bộ
    db.commit()
    db.refresh(ticket)
except Exception as e:
    db.rollback()
    logger.error(f"Lỗi khi xử lý cọc phiếu {ticket.id}: {str(e)}")
    raise HTTPException(status_code=500, detail="Lỗi giao dịch cơ sở dữ liệu")
```

---

## 4. QUY CHUẨN FRONTEND (HTML / JAVASCRIPT / CSS)

### 4.1. Cấu Trúc HTML5 & Ngữ Nghĩa
- Sử dụng đúng thẻ ngữ nghĩa: `<header>`, `<main>`, `<section>`, `<nav>`, `<aside>`, `<footer>`.
- Các phần tử tương tác (button, input, select) **bắt buộc** có `id` hoặc `name` tường minh:
  ```html
  <!-- CHUẨN -->
  <button id="btn-submit-deposit" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
      Xác Nhận Thu Cọc 30%
  </button>
  
  <!-- SAI -->
  <div onclick="submit()" class="btn">Thu tiền</div>
  ```

### 4.2. Quy Chuẩn JavaScript (ES6+ & Async/Await)
- Không dùng `var`, chỉ dùng `const` (mặc định) hoặc `let` (khi cần gán lại).
- Xử lý bất đồng bộ bắt buộc dùng `async/await` kèm khối `try...catch` và thông báo lỗi trực quan cho người dùng (Toast/Alert):
```javascript
// CHUẨN:
async function handleConfirmDeposit(ticketId, amount) {
    try {
        showLoadingSpinner();
        const response = await fetch(`/api/tickets/${ticketId}/deposit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`
            },
            body: JSON.stringify({ tien_dat_coc: amount })
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Không thể xác nhận đặt cọc');
        }
        
        showToast('Thu cọc 30% thành công!', 'success');
        reloadTicketDetails(ticketId);
    } catch (err) {
        showToast(`Lỗi: ${err.message}`, 'error');
    } finally {
        hideLoadingSpinner();
    }
}
```

### 4.3. Phòng Chống XSS Trên Giao Diện
- Không gán trực tiếp chuỗi chưa kiểm tra vào `.innerHTML`.
- Ưu tiên dùng `.textContent` hoặc hàm sanitize an toàn:
```javascript
// CHUẨN (chống XSS):
const customerNameEl = document.getElementById('customer-name');
customerNameEl.textContent = ticket.khach_hang_ten;

// NGUY HIỂM (cấm sử dụng nếu ticket.khach_hang_ten do khách tự nhập):
// customerNameEl.innerHTML = ticket.khach_hang_ten;
```

---

## 5. QUY CHUẨN XỬ LÝ NGHIỆP VỤ ĐẶC THÙ (BUSINESS RULES)

### 5.1. Luồng Tiền Cọc 30% & Quyết Toán 70%
1. **Lập Báo Giá**: KTV kiểm tra máy và chọn linh kiện + tiền công.
   $$\text{tong\_tien} = \sum (\text{gia\_linh\_kien} \times \text{so\_luong}) + \text{tien\_cong}$$
2. **Tính Tiền Cọc**: 
   $$\text{tien\_dat\_coc} = \text{round}(\text{tong\_tien} \times 0.3, -3)$$
3. **Điều Kiện Sửa**: Chỉ khi `da_dat_coc == True` thì KTV mới được bấm **"Bắt đầu sửa chữa"**.
4. **Quyết Toán 70%**: Khi hoàn thành và khách đến lấy máy:
   $$\text{tien\_con\_lai} = \text{tong\_tien} - \text{tien\_dat\_coc}$$
   Lễ tân hoặc Thu ngân thu 70% còn lại và in phiếu bàn giao.

### 5.2. Luồng Chống Bịa Đặt Dữ Liệu AI (Anti-Hallucination)
- Mọi câu trả lời của Chatbot về giá linh kiện hoặc dịch vụ **phải được Grounding** từ cơ sở dữ liệu `linh_kien` hiện tại.
- Nếu không tìm thấy thông tin phù hợp trong danh mục, AI **bắt buộc** trả lời:
  > *"Hiện tại trung tâm chưa có sẵn linh kiện này hoặc giá chưa được cập nhật chính thức. Quý khách vui lòng liên hệ trực tiếp hotline hoặc bàn tiếp nhận để kỹ thuật viên kiểm tra chi tiết."*
- Cấm AI tự đoán khoảng giá khi không có trong bảng giá.

---

## 6. QUY CHUẨN BẢO MẬT & KIỂM THỬ (SECURITY & TESTING)

### 6.1. Bảo Mật Dữ Liệu
- **Mật Khẩu**: Băm bằng `passlib` với thuật toán `bcrypt` (độ dài work factor tối thiểu 12).
- **JWT Secret**: Lưu trữ trong `.env`, không commit vào Git.
- **Role-Based Access Control (RBAC)**: Mỗi endpoint quản trị phải có Dependency kiểm tra Role:
  ```python
  @router.post("/payroll/approve")
  def approve_payroll(user: User = Depends(require_roles(["ke_toan", "admin"]))):
      ...
  ```

### 6.2. Kiểm Thử Tự Động (Automated Testing Checklist)
Trước khi bàn giao hoặc merge code, phải vượt qua:
- [ ] 100% test cases trong `tests/` pass (`pytest -v`).
- [ ] Không có lỗi cú pháp hoặc import chưa dùng (`flake8` / `ruff`).
- [ ] Endpoint mới phải có tài liệu Swagger hiển thị đầy đủ tại `/docs`.
- [ ] Không có API key hay credentials lộ trong mã nguồn.

---

## 7. ĐIỀU KIỆN DỪNG CỦA AI (STOPPING CONDITIONS)

Theo chuẩn AI-Augmented SDLC, AI Agent **phải dừng lại và yêu cầu người dùng làm rõ** nếu:
1. Yêu cầu nghiệp vụ mâu thuẫn với quy tắc đặt cọc 30% hoặc phân quyền 5 vai trò.
2. Thiếu thông tin trường dữ liệu trong CSDL cần thiết để thực thi tính năng.
3. Mã nguồn bị xung đột nghiêm trọng (Merge Conflict) hoặc thư viện bên thứ 3 không tương thích.

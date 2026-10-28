---
name: testing
description: >
  Kiểm thử toàn diện hệ thống FrogHippo Phone theo acceptance criteria đã phê duyệt.
  Bao gồm: kiểm thử trạng thái phiếu, luồng cọc 30%/70%, AI anti-hallucination,
  bảng lương, phân quyền, và chatbot. Không sửa test chỉ để pass.
---

# Testing Skill — FrogHippo Phone

## Objective

Kiểm thử có hệ thống theo requirements đã phê duyệt, phát hiện lỗi logic và lỗi tích hợp,
đặc biệt tập trung vào state machine phiếu, luồng tài chính và AI behavior.

## Inputs

- `docs/requirements.md` — FR cần test
- `docs/acceptance-criteria.md` — AC làm chuẩn
- `docs/business-rules.md` — BR cần verify
- Server đang chạy: `http://127.0.0.1:8000`
- MySQL: `quan_ly_sua_chua`

## Test Categories

### CAT-1: Authentication & Authorization

```
TC-AUTH-001: Đăng nhập đúng tài khoản Admin → 200 + token
TC-AUTH-002: Đăng nhập sai mật khẩu → 401
TC-AUTH-003: Tài khoản bị khóa → 403 "Tài khoản đã bị tạm khóa"
TC-AUTH-004: KTV không thể truy cập /api/ke-toan/* → 403
TC-AUTH-005: Không có token → route protected trả 401
```

### CAT-2: State Machine Phiếu Sửa Chữa

Trạng thái hợp lệ:
```
KhoiTao → DangKiemTra → ChoLinhKien → DangSua → DaSuaXong → DaThanhToan
```

```
TC-STATE-001: KhoiTao → DangKiemTra ✓ PASS
TC-STATE-002: DangSua → DaSuaXong ✓ PASS
TC-STATE-003: KhoiTao → DaThanhToan (nhảy vọt) → 422 REJECTED
TC-STATE-004: DaThanhToan → DangSua (rollback) → 422 REJECTED
TC-STATE-005: Xóa phiếu DaSuaXong → 400 "Không được xóa"
TC-STATE-006: Xóa phiếu DaThanhToan → 400 "Không được xóa"
```

### CAT-3: Luồng Tài Chính Cọc 30% / Quyết Toán 70%

```
TC-FIN-001: Tạo phiếu → KTV thêm LK → GET chi_tiet → tính tong_hoa_don đúng
TC-FIN-002: Thu cọc 30% → tienDatCoc = round(tong * 0.3)
TC-FIN-003: daDatCoc = True sau khi thu cọc
TC-FIN-004: Thu cọc lần 2 cùng phiếu → 400 "Đã đặt cọc rồi"
TC-FIN-005: Quyết toán khi phiếu chưa DaSuaXong → 400 "Phiếu chưa hoàn thành"
TC-FIN-006: tienQuyetToan = tong_hoa_don - tienDatCoc
TC-FIN-007: Tạo hóa đơn sau quyết toán → INSERT hoa_don thành công
TC-FIN-008: Trạng thái phiếu → DaThanhToan sau quyết toán

Script kiểm thử tự động:
```
```powershell
# TC-FIN-002: Kiểm tra tienDatCoc đúng
$resp = Invoke-WebRequest -Uri "http://localhost:8000/api/le-tan/thu-coc/PS001" `
    -Method POST -ContentType "application/json" `
    -Body '{"phuongThuc":"TienMat","tienKhachDua":500000}' -UseBasicParsing
$data = $resp.Content | ConvertFrom-Json
Write-Host "tienDatCoc:" $data.tienDatCoc
Write-Host "Expected: ~30% of" $data.tongHoaDon
```

### CAT-4: AI Anti-Hallucination (BẮT BUỘC)

```
TC-AI-001: Hỏi linh kiện CÓ trong DB → Trả lời với giá đúng từ DB
TC-AI-002: Hỏi linh kiện KHÔNG có trong DB → "Không tìm thấy", KHÔNG bịa giá
TC-AI-003: Hỏi "iPhone 99 Ultra" (sản phẩm giả) → Từ chối, KHÔNG tạo ra
TC-AI-004: DB trống linh kiện → Chatbot thông báo "hiện chưa có linh kiện"
TC-AI-005: Thời gian phản hồi AI < 5 giây (NFR-001)
TC-AI-006: Mất kết nối AI API → Fallback graceful, không crash server
```

### CAT-5: Bảng Lương Kế Toán

```
TC-KT-001: Tạo bảng lương tháng có nhân viên → INSERT bang_luong per NV
TC-KT-002: Tạo bảng lương tháng đã tồn tại → 400 "Đã có bảng lương"
TC-KT-003: Thực lĩnh = luongCoBan + thuong + phuCap - khauTru
TC-KT-004: Phát lương → trangThai = 'DA_PHAT', ngayPhat được ghi
TC-KT-005: Phát lương đã phát → 400 "Đã phát lương rồi"
TC-KT-006: GET bang-luong?thang=2026-10 → chỉ trả tháng 10
```

### CAT-6: Linh Kiện Kho

```
TC-LK-001: Thêm linh kiện soLuong=0 vào phiếu → 400 "Hết hàng"
TC-LK-002: Thêm linh kiện hợp lệ → soLuongTon giảm
TC-LK-003: Cảnh báo kho khi soLuongTon <= 3 → Admin nhìn thấy badge
TC-LK-004: Xóa linh kiện đang dùng trong phiếu active → 400 REJECTED
```

### CAT-7: Cổng Khách Hàng

```
TC-KH-001: Tra cứu bằng mã phiếu hợp lệ → Trả thông tin đầy đủ
TC-KH-002: Tra cứu mã phiếu không tồn tại → 404 "Không tìm thấy"
TC-KH-003: Duyệt báo giá → duyetBaoGia = True trong DB
TC-KH-004: Từ chối báo giá → ghi chú lý do
TC-KH-005: Đánh giá 1-5 sao → INSERT danh_gia_dich_vu thành công
TC-KH-006: Chatbot widget mở/đóng → UI responsive
TC-KH-007: Chatbot call /api/le-tan/chatbot-linh-kien → 200 + reply
```

## Test Execution Format

Với mỗi test case ghi lại:
```
TC-ID    : TC-FIN-002
Name     : Thu cọc 30% tính đúng
Precond  : Phiếu PS001 tồn tại, có chi tiết LK tổng 1.000.000đ
Steps    : POST /api/le-tan/thu-coc/PS001 {"phuongThuc":"TienMat"}
Expected : tienDatCoc = 300.000, daDatCoc = true, tienConLai70 = 700.000
Actual   : [kết quả thực tế]
Status   : PASSED / FAILED
Bug      : [mô tả nếu FAILED]
```

## Defect Format

```
BUG-ID   : BUG-001
Title    : Thu cọc lần 2 không bị từ chối
Severity : HIGH
TC       : TC-FIN-004
Reproduce: POST /api/le-tan/thu-coc/PS001 lần 2
Expected : 400 "Đã đặt cọc rồi"
Actual   : 200 và cọc thêm lần nữa
Fix      : Kiểm tra daDatCoc trong route trước khi xử lý
```

## Rules — BẮT BUỘC

- ❌ KHÔNG sửa test để nó pass khi logic sai
- ❌ KHÔNG bỏ qua test AI anti-hallucination
- ❌ KHÔNG khai báo PASS khi chưa thực sự chạy test
- ✅ Chạy test trên server thật (không mock toàn bộ)
- ✅ Ghi rõ ACTUAL result dù pass hay fail
- ✅ Bug phải có reproduce steps

## Outputs

```
docs/test-plan.md      — Danh sách test cases + preconditions
docs/test-report.md    — Kết quả thực tế, pass/fail rate
docs/bug-report.md     — Danh sách bug phát hiện + severity
```

## Coverage Target

| Category | Test Cases | Target Pass Rate |
|---|---|---|
| Auth & Authorization | 5 | 100% |
| State Machine | 6 | 100% |
| Tài Chính 30%/70% | 8 | 100% |
| AI Anti-Hallucination | 6 | 100% |
| Bảng Lương | 6 | 100% |
| Linh Kiện | 4 | 100% |
| Cổng Khách Hàng | 7 | 100% |
| **Tổng** | **42** | **≥ 95%** |

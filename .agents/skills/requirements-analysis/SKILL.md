---
name: requirements-analysis
description: >
  Phân tích yêu cầu phần mềm cho hệ thống quản lý trung tâm sửa chữa điện thoại FrogHippo Phone.
  Chuyển đổi yêu cầu nghiệp vụ thành yêu cầu chức năng có cấu trúc, user stories và acceptance criteria
  theo đúng bối cảnh dự án (4 vai trò: Admin, Lễ Tân, KTV, Thu Ngân, Kế Toán).
---

# Requirements Analysis Skill — FrogHippo Phone

## Bối Cảnh Dự Án

Hệ thống quản lý trung tâm sửa chữa điện thoại FrogHippo Phone bao gồm:
- **Backend**: FastAPI (Python) + SQLAlchemy ORM + MySQL
- **Frontend**: HTML/CSS + Vanilla JS + Tailwind CSS
- **AI Engine**: Google Gemini API / OpenAI API (có fallback)
- **Vai trò chính**: Admin, Lễ Tân, Kỹ Thuật Viên (KTV), Thu Ngân, Kế Toán
- **Cổng Khách Hàng**: Tra cứu tiến độ trực tuyến, đánh giá dịch vụ

## Objective

Phân tích có hệ thống các yêu cầu phần mềm từ tài liệu nghiệp vụ để tạo ra đặc tả phù hợp
cho các giai đoạn thiết kế kiến trúc, CSDL, triển khai và kiểm thử tiếp theo.

## Inputs

Đọc các tài liệu sau khi có sẵn:
- `docs/customer-requirement.md` — Yêu cầu khách hàng
- `docs/business-rules.md` — Quy tắc nghiệp vụ
- `tai_lieu_skill/NHOMS38.docx` — Báo cáo dự án gốc (bối cảnh đầy đủ)
- Tài liệu hiện trạng vận hành thực tế

## Process

### 1. Xác định Tác Nhân (Actors)

Xác định tất cả tác nhân trong hệ thống FrogHippo Phone:
- Admin (Quản lý): quyền toàn hệ thống
- Lễ Tân: tiếp nhận, lập phiếu, thu cọc, soạn tin AI
- Kỹ Thuật Viên (KTV): kiểm tra, báo giá, cập nhật trạng thái
- Thu Ngân: thu tiền, lập hóa đơn, chốt ca
- Kế Toán: phát lương, đối soát dòng tiền kho
- Khách Hàng (external): tra cứu online, đánh giá, duyệt báo giá

### 2. Yêu Cầu Chức Năng (FR)

Phân loại yêu cầu theo nhóm chức năng, sử dụng ID dạng `FR-XXX`:
```
FR-001 đến FR-020: Quản lý phiếu sửa chữa & luồng trạng thái
FR-021 đến FR-040: Quản lý linh kiện & kho
FR-041 đến FR-060: Quản lý nhân viên & phân quyền
FR-061 đến FR-080: Thanh toán & hóa đơn (bao gồm cọc 30% / quyết toán 70%)
FR-081 đến FR-100: AI tích hợp (chẩn đoán, soạn tin, chatbot)
FR-101 đến FR-120: Cổng khách hàng (tra cứu, đánh giá, duyệt báo giá)
FR-121 đến FR-140: Kế toán (lương, dòng tiền)
FR-141 đến FR-160: Báo cáo & thống kê
```

### 3. Yêu Cầu Phi Chức Năng (NFR)

```
NFR-001: Thời gian phản hồi AI API < 5 giây
NFR-002: AI KHÔNG được bịa dữ liệu không có trong CSDL (anti-hallucination)
NFR-003: API key AI (Gemini/OpenAI) KHÔNG xuất hiện trong source code
NFR-004: Mật khẩu nhân viên được mã hóa hash
NFR-005: Bảo vệ thông tin cá nhân khách hàng (SĐT, họ tên)
NFR-006: Hệ thống hoạt động ổn định với MySQL trên localhost
NFR-007: Giao diện responsive, tải < 3 giây
NFR-008: Fallback graceful khi AI API không khả dụng
```

### 4. Quy Tắc Nghiệp Vụ Đặc Thù (Business Rules)

```
BR-001: Khách đặt cọc 30% tổng hóa đơn (tính từ báo giá KTV) trước khi KTV tiến hành sửa
BR-002: Thu 70% còn lại khi khách đến nhận máy (sau khi KTV báo DaSuaXong)
BR-003: Phiếu không thể xóa khi ở trạng thái DaSuaXong hoặc DaThanhToan
BR-004: Chỉ tạo hóa đơn khi phiếu ở trạng thái DaSuaXong
BR-005: Chatbot chỉ trả lời giá linh kiện CÓ THẬT trong bảng linh_kien
BR-006: Linh kiện soLuongTon = 0 không được gán vào phiếu sửa
BR-007: Mỗi nhân viên chỉ có 1 ca làm việc đang mở tại 1 thời điểm
BR-008: Lương được tính: LuongCoBan + Thuong(theo phiếu) + PhuCap - KhauTru
```

### 5. Phân Biệt Yêu Cầu vs Giả Định

Ghi rõ:
- **Yêu cầu xác nhận**: đã có trong tài liệu dự án
- **Giả định**: chưa được xác nhận, cần review
- **Thiếu thông tin**: câu hỏi cần hỏi stakeholder

Ví dụ giả định cần kiểm tra:
- `ASM-001`: Tiền công thợ mặc định 150.000 đ/phiếu (cần xác nhận)
- `ASM-002`: Chatbot hoạt động không có auth (tra cứu public)
- `ASM-003`: Lễ Tân có thể xem nhưng không sửa phiếu của KTV

### 6. Luồng Nghiệp Vụ Chính (Business Flows)

Mô tả luồng từ đầu đến cuối:
```
LUỒNG CHÍNH:
Khách đến → Lễ Tân lập phiếu
→ KTV kiểm tra & báo giá (nhập linh kiện)
→ Lễ Tân thu cọc 30% + AI soạn tin báo giá
→ KTV sửa chữa → Cập nhật DaSuaXong
→ Lễ Tân gửi tin báo hoàn thành
→ Khách đến → Lễ Tân thu 70% → tạo hóa đơn
→ KTV lập phiếu bảo hành
→ Kế Toán đối soát + phát lương cuối tháng
```

### 7. User Stories

Format chuẩn: `As a <role>, I want <capability>, so that <benefit>.`

### 8. Acceptance Criteria

Mỗi user story quan trọng cần có tiêu chí kiểm thử cụ thể và có thể đo lường.

### 9. Traceability Matrix

Mỗi user story phải traceable đến ít nhất 1 FR hoặc BR.

### 10. Phát Hiện Mâu Thuẫn & Khoảng Trống

Ghi lại mọi:
- Yêu cầu mâu thuẫn
- Yêu cầu chưa rõ ràng
- Thiếu thông tin từ khách hàng

## Rules — BẮT BUỘC TUÂN THỦ

- ❌ KHÔNG viết source code
- ❌ KHÔNG thiết kế database
- ❌ KHÔNG thiết kế kiến trúc
- ❌ KHÔNG tự bịa thêm yêu cầu không có trong tài liệu gốc
- ✅ Phân biệt rõ yêu cầu thực tế vs giả định
- ✅ Ghi rõ thông tin còn thiếu cần xác nhận

## Outputs

Tạo hoặc cập nhật:
```
docs/requirements.md          — FR + NFR đầy đủ với ID
docs/user-stories.md          — User stories theo vai trò  
docs/acceptance-criteria.md   — AC có thể test được
docs/business-rules.md        — BR đặc thù dự án
docs/requirements-issues.md   — Mâu thuẫn, khoảng trống, giả định
```

## Verification — KIỂM TRA TRƯỚC KHI HOÀN THÀNH

- [ ] Tất cả FR có ID dạng FR-XXX
- [ ] Tất cả NFR có ID dạng NFR-XXX
- [ ] Tất cả BR có ID dạng BR-XXX
- [ ] Mọi user story traceable về FR/BR
- [ ] Acceptance criteria có thể kiểm thử được
- [ ] Không có FR nào tự thêm không có trong tài liệu gốc
- [ ] Luồng 30%/70% được đặc tả đầy đủ

## Human Gate

**KHÔNG được chuyển sang Architecture Design** khi chưa có:
```
Requirements Review
Reviewer: [Tên sinh viên / người dùng]
Status: APPROVED / NEEDS_REVISION
Checked:
  [X] FR đầy đủ và có ID
  [X] NFR phủ bảo mật + hiệu năng AI
  [X] Business Rules đặc thù (cọc 30/70%)
  [X] User Stories có AC
  [X] Không có hallucinated requirements
Approved for: Architecture Design
```

---
name: security-review
description: >
  Đánh giá và kiểm tra an toàn bảo mật toàn diện cho hệ thống FrogHippo Phone.
  Kiểm soát xác thực JWT, phân quyền đa vai trò RBAC, phòng chống SQL Injection,
  XSS, CSRF, bảo vệ thông tin cá nhân khách hàng (PII) và quản lý bí mật cấu hình API.
---

# Security Review Skill — FrogHippo Phone

## Mục Tiêu

Đảm bảo an toàn thông tin tuyệt đối cho hệ thống FrogHippo Phone, bảo vệ dữ liệu khách hàng (số điện thoại, thiết bị, lịch sử sửa chữa), dữ liệu tài chính (dòng tiền, lương, cọc), và API keys của dịch vụ AI (Gemini, OpenAI).

---

## Danh Mục Kiểm Tra An Toàn (Security Checklist)

### 1. Quản Lý Khóa Bí Mật & Cấu Hình (Secrets Management)
- [ ] **File `.env`**: Tuyệt đối không commit file `.env` chứa mật khẩu DB (`DB_PASSWORD`), JWT Secret Key (`SECRET_KEY`), hoặc AI Keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`) lên Git repository.
- [ ] **File `.gitignore`**: Kiểm tra đảm bảo `.env`, `*.log`, `__pycache__`, `.pytest_cache` được thêm vào `.gitignore`.
- [ ] **Hardcoded Secrets**: Không được để bất kỳ chuỗi token, mật khẩu hoặc secret key hardcode nào trong mã nguồn.

### 2. Xác Thực & Phân Quyền (Authentication & RBAC)
- [ ] **Băm Mật Khẩu**: Sử dụng thuật toán băm mạnh (`bcrypt` hoặc `argon2`) với salt. Tuyệt đối cấm lưu mật khẩu rõ (plain-text) hoặc dùng MD5/SHA1.
- [ ] **JWT Token Security**:
  - Token phải có thời hạn sống hợp lý (`exp`), ví dụ: Access Token 60-120 phút.
  - Sử dụng thuật toán ký an toàn (`HS256` hoặc `RS256`).
  - Kiểm tra chữ ký và thu hồi token khi đăng xuất (nếu có blacklist/Redis).
- [ ] **Kiểm Soát Quyền Theo Vai Trò (RBAC)**:
  - Khách hàng vãng lai chỉ có quyền tra cứu phiếu của chính mình (thông qua mã phiếu/SĐT).
  - Lễ tân không được quyền duyệt sửa lương hay sửa cấu hình hệ thống của Admin.
  - KTV chỉ được cập nhật trạng thái và linh kiện của phiếu mình phụ trách.
  - Kế toán chỉ thao tác các bảng tài chính, lương và kho.

### 3. Phòng Chống Tấn Công Web Phổ Biến (OWASP Top 10)
- [ ] **SQL Injection**: Tất cả truy vấn CSDL phải sử dụng SQLAlchemy ORM có tham số hóa (Parameterized queries). Cấm nối chuỗi SQL thô (`f"SELECT * FROM users WHERE..."`).
- [ ] **Cross-Site Scripting (XSS)**:
  - Dữ liệu hiển thị lên HTML từ người dùng (ghi chú bệnh máy, tên khách, tin nhắn chat) phải được encode an toàn (`textContent` hoặc sanitize).
  - Không gán trực tiếp dữ liệu chưa lọc vào `element.innerHTML`.
- [ ] **Cross-Origin Resource Sharing (CORS)**: Cấu hình `CORSMiddleware` với danh sách origin được phép cụ thể trong môi trường production, tránh dùng `allow_origins=["*"]` nếu có cookie credentials.
- [ ] **Rate Limiting**: Giới hạn tần suất gọi API (Rate Limiting) trên các endpoint nhạy cảm: `/api/auth/login`, `/api/chat/ask` (ngăn cản brute-force mật khẩu và spam tốn chi phí AI token).

### 4. Bảo Vệ Dữ Liệu Khách Hàng (Data Privacy & PII)
- [ ] **Số Điện Thoại & Địa Chỉ**: Che bớt thông tin nhạy cảm trên giao diện công cộng (ví dụ: màn hình tra cứu khách hàng chỉ hiển thị `098****123` thay vì toàn bộ SĐT).
- [ ] **Nhật Ký Hệ Thống (Audit Logs)**: Ghi log mọi hành động nhạy cảm (thay đổi giá tiền, phát lương, xóa phiếu, hủy hóa đơn cọc) kèm ID người thực hiện và timestamp.

---

## Mẫu Báo Cáo Đánh Giá Bảo Mật

```markdown
# Báo Cáo Đánh Giá Bảo Mật (Security Audit Report)

## 1. Kết Quả Tổng Thể
- **Số lỗ hổng nghiêm trọng (Critical)**: 0
- **Số cảnh báo cần lưu ý (Medium/High)**: 0
- **Trạng thái sẵn sàng (Deployment Readiness)**: Sẵn sàng / Chưa sẵn sàng

## 2. Chi Tiết Phát Hiện & Khắc Phục
| ID | Hạng mục | Rủi ro | Mức độ | Trạng thái | Giải pháp đã áp dụng |
|---|---|---|---|---|---|
| SEC-01 | Quản lý Secrets | Lộ API key trong code | 🔴 Cao | Đã sửa | Chuyển sang biến môi trường `.env` |
| SEC-02 | Auth | Session không hết hạn | 🟡 Vừa | Đã sửa | Đặt `ACCESS_TOKEN_EXPIRE_MINUTES = 120` |
| SEC-03 | Anti-Spam | Chatbot bị spam token | 🟡 Vừa | Đã sửa | Thêm IP rate limit cho endpoint chat |
```

---
name: documentation
description: >
  Tạo, cập nhật và duy trì tài liệu kỹ thuật và tài liệu người dùng cho FrogHippo Phone.
  Bao gồm: API Documentation (Swagger/OpenAPI), Sơ đồ kiến trúc/ERD, Hướng dẫn vận hành
  theo từng vai trò (Lễ tân, KTV, Thu ngân, Kế toán, Admin), và Báo cáo nghiệm thu.
---

# Documentation Skill — FrogHippo Phone

## Mục Tiêu

Cung cấp bộ tài liệu toàn diện, chuẩn mực và dễ hiểu cho cả đội ngũ phát triển kỹ thuật và người dùng nghiệp vụ tại trung tâm sửa chữa FrogHippo Phone.

---

## Các Loại Tài Liệu Cần Quản Lý

### 1. Tài Liệu Kỹ Thuật (Technical Documentation)
- **Kiến Trúc Hệ Thống**: Sơ đồ C4 model (Context, Container, Component) mô tả FastAPI + MySQL + Frontend SPA/Multi-page + Gemini/OpenAI AI Engine.
- **Mô Hình Cơ Sở Dữ Liệu (ERD)**: Sơ đồ quan hệ thực thể của 12+ bảng dữ liệu (`nguoi_dung`, `khach_hang`, `thiet_bi`, `phieu_sua_chua`, `chi_tiet_sua_chua`, `linh_kien`, `hoa_don`, `bang_luong`, `nhat_ky_kho`, `danh_gia`, v.v.).
- **API Reference**: Swagger UI (`/docs`) và Redoc (`/redoc`) với đầy đủ mô tả endpoint, tham số request, ví dụ response, mã lỗi HTTP chuẩn (200, 201, 400, 401, 403, 404, 422, 500).
- **Quy Trình Triển Khai (Deployment Guide)**: Hướng dẫn cài đặt môi trường ảo Python (`venv`), cấu hình file `.env`, migrate CSDL, và chạy server với Uvicorn.

### 2. Tài Liệu Hướng Dẫn Vận Hành (User Manual by Role)
- **Dành cho Lễ Tân**:
  - Hướng dẫn tiếp nhận máy và lập phiếu sửa chữa.
  - Sử dụng AI để soạn tin nhắn SMS/Zalo/Email tự động gửi khách.
  - Thu tiền đặt cọc 30% khi KTV báo giá và in phiếu biên nhận cọc.
  - Trả máy và phối hợp thu ngân quyết toán 70% còn lại.
- **Dành cho Kỹ Thuật Viên (KTV)**:
  - Tiếp nhận thiết bị được phân công.
  - Kiểm tra bệnh, chẩn đoán lỗi bằng AI hỗ trợ.
  - Lập bảng báo giá linh kiện và công thợ.
  - Cập nhật tiến độ sửa chữa theo thời gian thực.
- **Dành cho Thu Ngân**:
  - Quản lý hóa đơn thanh toán (cọc 30%, quyết toán 70%).
  - Chốt ca và in báo cáo doanh thu theo ngày.
- **Dành cho Kế Toán**:
  - Tính toán và phát lương nhân viên/KTV kèm bảng lương chi tiết.
  - Quản lý dòng tiền vào/ra kho linh kiện, đối soát chi phí nhập hàng.
- **Dành cho Khách Hàng**:
  - Cổng tra cứu tiến độ sửa chữa trực tuyến bằng số điện thoại hoặc mã phiếu.
  - Tra cứu giá linh kiện và chat với AI tư vấn.
  - Gửi đánh giá sao và phản hồi sau sửa chữa.

---

## Nguyên Tắc Soạn Thảo

1. **Rõ Ràng & Trực Quan**: Sử dụng bảng biểu, danh sách kiểm tra (checkboxes), và sơ đồ Mermaid bất cứ khi nào có thể.
2. **Đồng Bộ Với Mã Nguồn**: Mọi thay đổi trong API endpoint, trường dữ liệu trong DB, hoặc quy tắc nghiệp vụ phải được phản ánh ngay vào tài liệu.
3. **Hình Ảnh Minh Họa**: Đính kèm ảnh chụp màn hình thực tế (Screenshots) của các giao diện để người dùng dễ hình dung.

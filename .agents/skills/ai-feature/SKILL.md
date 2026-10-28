---
name: ai-feature
description: >
  Tích hợp và quản lý các tính năng Trí tuệ Nhân tạo (AI) cho hệ thống FrogHippo Phone.
  Bao gồm: Chẩn đoán lỗi sơ bộ, Soạn tin nhắn tự động (Zalo/SMS/Email) cho Lễ tân,
  Chatbot tư vấn linh kiện và giá thành cam kết KHÔNG BỊA CHUYỆN (Grounding / Anti-hallucination),
  và cơ chế Fallback giữa Gemini API / OpenAI API.
---

# AI Feature Skill — FrogHippo Phone

## Bối Cảnh & Mục Tiêu

Hệ thống FrogHippo Phone sử dụng AI để hỗ trợ vận hành trung tâm sửa chữa ở 3 điểm chạm cốt lõi:
1. **Tại Bàn Tiếp Nhận / Lễ Tân**: AI tự động tạo bản nháp tin nhắn thông báo (Zalo / SMS / Email) khi nhận máy, khi KTV báo giá cọc 30%, hoặc khi sửa xong.
2. **Tại Phòng Kỹ Thuật**: AI gợi ý chẩn đoán nguyên nhân hư hỏng dựa trên mô tả triệu chứng và model máy.
3. **Tại Kênh Tư Vấn Khách Hàng (Chatbot)**: Chatbot hỏi đáp giá linh kiện và dịch vụ, **tuyệt đối không bịa đặt** (Anti-hallucination) dựa trên dữ liệu thực tế từ Database linh kiện của cửa hàng.

---

## Kiến Trúc AI Engine

- **Engine chính**: Google Gemini API (`gemini-1.5-flash` hoặc `gemini-2.0-flash`)
- **Engine dự phòng (Fallback)**: OpenAI API (`gpt-4o-mini`)
- **Dữ liệu nguồn (Grounding Source)**: Bảng `linh_kien` (tên, giá_bán, tồn_kho, model tương thích) và bảng `bang_gia_dich_vu`
- **File triển khai backend**: `ai_service.py` hoặc router `routers/ai_router.py`

---

## Nguyên Tắc Vàng (Strict Rules)

> [!CAUTION]
> **QUY TẮC CHỐNG BỊA CHUYỆN (ANTI-HALLUCINATION)**:
> 1. Chatbot **CHỈ ĐƯỢC** báo giá và thông tin linh kiện có trong cơ sở dữ liệu thực tế được truyền vào context/prompt.
> 2. Nếu linh kiện **không có trong kho hoặc không tìm thấy trong DB**, AI **PHẢI** trả lời rõ ràng: *"Hiện tại cửa hàng không có sẵn linh kiện này hoặc chưa có giá niêm yết chính thức. Quý khách vui lòng liên hệ trực tiếp hotline hoặc lễ tân để được hỗ trợ kiểm tra đặt hàng."*
> 3. Tuyệt đối không tự suy diễn giá tiền (ví dụ: không được tự bịa "màn hình iPhone 15 giá tầm 2-3 triệu" nếu DB không có).

---

## Quy Trình Tích Hợp AI

### 1. Chuẩn Bị Context / Grounding Data
Trước khi gọi AI Chatbot hoặc AI Báo giá:
1. Query cơ sở dữ liệu `LinhKien` với các trường: `ten_linh_kien`, `loai`, `gia_ban`, `so_luong_ton`, `model_tuong_thich`.
2. Format dữ liệu thành JSON hoặc bảng Markdown thu gọn làm `Grounding Knowledge Base`.
3. Nhúng dữ liệu này vào System Prompt kèm chỉ thị ràng buộc nghiêm ngặt.

### 2. Cấu Trúc System Prompt Cho Chatbot Tra Cứu Linh Kiện
```text
Bạn là Trợ lý ảo tư vấn dịch vụ của Trung tâm sửa chữa FrogHippo Phone.
Nhiệm vụ: Tư vấn chi phí sửa chữa và tình trạng linh kiện cho khách hàng.

NGUỒN DỮ LIỆU THỰC TẾ CỦA CỬA HÀNG:
{inventory_knowledge_base}

QUY TẮC BẮT BUỘC:
1. CHỈ sử dụng thông tin trong NGUỒN DỮ LIỆU trên để trả lời về giá và tình trạng hàng.
2. Nếu linh kiện khách hỏi không có trong danh sách, hãy thông báo lịch sự rằng cửa hàng chưa có sẵn hoặc cần kiểm tra thêm, KHÔNG ĐƯỢC TỰ BỊA GIÁ.
3. Luôn thông báo mức đặt cọc 30% đối với linh kiện cần thay thế theo quy định của trung tâm.
4. Giọng điệu chuyên nghiệp, lịch sự, thân thiện.
```

### 3. Cấu Trúc Prompt Soạn Tin Nhắn Tự Động (Lễ Tân)
Tạo tin nhắn đa kênh (Zalo, SMS, Email) dựa trên trạng thái phiếu:
- **Sự kiện 1: Nhận máy & Lập phiếu**: Gửi mã phiếu, model máy, tình trạng tiếp nhận sơ bộ.
- **Sự kiện 2: Báo giá & Yêu cầu cọc 30%**: Báo chi tiết linh kiện cần thay, tổng dự toán, số tiền cọc 30% cần thanh toán trước khi KTV tiến hành sửa.
- **Sự kiện 3: Sửa chữa hoàn tất**: Báo máy đã sẵn sàng nhận, số tiền 70% còn lại cần thanh toán, thời gian làm việc của cửa hàng.

### 4. Cơ Chế Xử Lý Lỗi & Fallback
```python
async def call_ai_service(prompt: str, system_instruction: str) -> str:
    try:
        # Thử Gemini trước
        return await call_gemini(prompt, system_instruction)
    except Exception as gemini_err:
        logger.warning(f"Gemini API failed: {gemini_err}. Switching to OpenAI fallback...")
        try:
            return await call_openai(prompt, system_instruction)
        except Exception as openai_err:
            logger.error(f"Both AI providers failed: {openai_err}")
            return "Hệ thống AI đang bảo trì. Vui lòng liên hệ nhân viên để được hỗ trợ trực tiếp."
```

---

## Kiểm Tra & Xác Nhận (Checklist)

- [ ] Chatbot trả lời chính xác giá khi linh kiện có trong DB.
- [ ] Chatbot từ chối báo giá / chuyển hướng đúng khi linh kiện KHÔNG có trong DB (Anti-hallucination test passed).
- [ ] Tin nhắn tự động cho Lễ tân có đầy đủ thông tin: Mã phiếu, Khách hàng, Thiết bị, Tiền cọc 30% hoặc Số dư 70%.
- [ ] Có form xem trước và nút Duyệt/Chỉnh sửa trước khi gửi cho khách.
- [ ] Log lại mọi tương tác AI để audit chất lượng và chi phí token.

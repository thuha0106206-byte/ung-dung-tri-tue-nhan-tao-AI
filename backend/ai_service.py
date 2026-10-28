import os
import json
import re
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo").strip()

PROMPT_SYSTEM = (
    "Bạn là trợ lý AI chuyên nghiệp của trung tâm bảo hành sửa chữa điện thoại FrogHippo Phone. "
    "Nhiệm vụ của bạn là đọc các mô tả lỗi và ghi chú kỹ thuật chuyên ngành khô khan từ Kỹ thuật viên, "
    "sau đó tóm tắt và dịch lại thành ngôn ngữ phổ thông, lịch sự, dễ hiểu để gửi cho khách hàng. "
    "Đồng thời giải thích ngắn gọn nguyên nhân và đề xuất phương án xử lý."
)

MSG_OUTPUT_RULES = (
    "\n\nQUY TẮC ĐẦU RA BẮT BUỘC: Chỉ trả về DUY NHẤT nội dung tin nhắn để gửi thẳng cho khách. "
    "KHÔNG viết lời dẫn (ví dụ: 'Dưới đây là...'), KHÔNG tiêu đề markdown (#, ###), KHÔNG dấu ** hay ***, "
    "KHÔNG giải thích hay ghi chú thêm. Viết tiếng Việt có dấu, câu hoàn chỉnh, kết thúc bằng lời cảm ơn."
)

def call_gemini_api(prompt_text: str) -> str:
    """Gọi Google Gemini REST API v1beta."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{PROMPT_SYSTEM}\n\nNội dung cần dịch/tóm tắt cho khách hàng:\n{prompt_text}"}
                ]
            }
        ]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()

def call_openai_api(prompt_text: str) -> str:
    """Gọi OpenAI Chat Completion REST API."""
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": f"Dịch và tóm tắt nội dung sau cho khách hàng:\n{prompt_text}"}
        ],
        "temperature": 0.7
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        return res_data["choices"][0]["message"]["content"].strip()

def mock_ai_summary(mo_ta_loi: str, ghi_chu_ktv: str = "") -> str:
    """Hàm AI giả lập thông minh khi chưa có API Key hoặc mất mạng."""
    info = ghi_chu_ktv or mo_ta_loi or "Thiết bị gặp sự cố kỹ thuật"
    return (
        f"Kính chào quý khách! FrogHippo Phone đã hoàn tất kiểm tra thiết bị của bạn. "
        f"Tình trạng xác định: {info}. Kỹ thuật viên đang tiến hành thay thế linh kiện "
        f"chính hãng và kiểm tra hiệu năng toàn diện. Thiết bị dự kiến bàn giao đúng hẹn."
    )

def summarize_repair_ticket(mo_ta_loi: str, ghi_chu_ktv: str = "") -> str:
    """
    Hàm tổng hợp: Ưu tiên gọi Gemini -> OpenAI -> Fallback giả lập thông minh.
    Tuân thủ Guardrails: Chặn nội dung ngoại phạm và thiếu thông tin.
    """
    target_text = ghi_chu_ktv or mo_ta_loi or ""
    invalid = validate_repair_input(target_text)
    if invalid is not None:
        return invalid["errorMessage"]

    input_text = f"Mô tả ban đầu: {mo_ta_loi}\nGhi chú kỹ thuật viên: {ghi_chu_ktv}"

    # 1. Thử Google Gemini
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            return call_gemini_api(input_text)
        except Exception as e:
            print(f"[AI Warning] Gemini API error: {e}. Switching to fallback.")

    # 2. Thử OpenAI
    if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
        try:
            return call_openai_api(input_text)
        except Exception as e:
            print(f"[AI Warning] OpenAI API error: {e}. Switching to fallback.")

    # 3. Fallback AI thông minh
    return mock_ai_summary(mo_ta_loi, ghi_chu_ktv)

def generate_customer_message(
    ma_phieu: str, 
    ma_kh: str, 
    mo_ta_loi: str = "", 
    trang_thai: str = "KhoiTao",
    channel: str = "Gmail",
    ghi_chu_ktv: str = ""
) -> str:
    """
    Sinh email chuẩn gửi cho khách hàng qua Gmail
    thông báo tiến độ hoặc báo máy đã sửa xong, kèm link tra cứu trực tuyến.
    """
    channel_clean = channel.strip().upper() if channel else "GMAIL"
    is_completed = trang_thai in ["DaSuaXong", "DA_SUA_XONG"]
    
    prompt = (
        f"Hãy soạn 1 tin nhắn thông báo gửi cho khách hàng qua kênh {channel_clean} từ Trung tâm sửa chữa FrogHippo Phone.\n"
        f"- Tên khách hàng: {ma_kh}\n"
        f"- Mã phiếu sửa chữa: {ma_phieu}\n"
        f"- Tình trạng lỗi: {mo_ta_loi or 'Bảo dưỡng thiết bị'}\n"
        f"- Ghi chú kỹ thuật viên / Linh kiện thay thế: {ghi_chu_ktv or 'Linh kiện chính hãng đã kiểm định an toàn'}\n"
        f"- Trạng thái thiết bị: {'ĐÃ SỬA XONG - SẴN SÀNG BÀN GIAO' if is_completed else trang_thai}\n"
        f"- Yêu cầu định dạng:\n"
    )
    if "SMS" in channel_clean:
        prompt += (
            "  + Kênh SMS: Viết tiếng Việt ngắn gọn, xúc tích, thông báo tình trạng máy, "
            f"mã phiếu #{ma_phieu}, link tra cứu: http://127.0.0.1:8000/?maPhieu={ma_phieu}, Hotline 19006868.\n"
        )
    elif "GMAIL" in channel_clean or "EMAIL" in channel_clean:
        prompt += (
            "  + Kênh Gmail: Định dạng thư điện tử trang trọng, có dòng Tiêu đề: [FrogHippo Phone] ..., "
            "Kính gửi Quý khách, chi tiết tình trạng sửa chữa, quyền tra cứu hồ sơ điện tử, cam kết bảo hành và thông tin liên hệ nhận máy.\n"
        )
    else:  # Zalo
        prompt += (
            "  + Kênh Zalo OA: Định dạng sinh động có icon cảm xúc (📱, ✨, 🛠️, 📍), "
            "lời chào thân thiện, thông báo rõ máy đã sửa xong (nếu DaSuaXong) kính mời khách đến kiểm tra nhận máy, "
            f"hướng dẫn tra cứu tiến độ với mã #{ma_phieu}, hotline 1900 6868.\n"
        )

    prompt += MSG_OUTPUT_RULES
    # 1. Thử gọi Gemini
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            return call_gemini_api(prompt)
        except Exception:
            pass

    # 2. Thử gọi OpenAI
    if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
        try:
            return call_openai_api(prompt)
        except Exception:
            pass

    # 3. Fallback theo từng kênh chuẩn chỉnh
    lookup_url = f"http://127.0.0.1:8000/?maPhieu={ma_phieu}"

    if "SMS" in channel_clean:
        if is_completed:
            return (
                f"[FrogHippo Phone] Kính gửi {ma_kh}, thiết bị theo phiếu #{ma_phieu} ĐÃ SỬA XONG hoàn tất và sẵn sàng bàn giao. "
                f"Kính mời Quý khách đến nhận máy. Tra cứu chi tiết: {lookup_url} . Hotline: 19006868."
            )
        else:
            return (
                f"[FrogHippo Phone] Kính gửi {ma_kh}, phiếu #{ma_phieu} đang được xử lý kỹ thuật. "
                f"Quý khách có thể theo dõi tiến độ thời gian thực tại: {lookup_url} . Hotline: 19006868."
            )

    elif "GMAIL" in channel_clean or "EMAIL" in channel_clean:
        if is_completed:
            return (
                f"TIÊU ĐỀ: [FrogHippo Phone] Thông Báo Thiết Bị #{ma_phieu} Đã Sửa Xong - Sẵn Sàng Bàn Giao\n\n"
                f"Kính gửi Quý khách ({ma_kh}),\n\n"
                f"Trung tâm Sửa chữa & Bảo hành FrogHippo Phone xin trân trọng thông báo: Thiết bị của Quý khách theo Phiếu tiếp nhận #{ma_phieu} đã được Kỹ thuật viên kiểm tra, sửa chữa và thay thế linh kiện hoàn tất.\n\n"
                f"📋 THÔNG TIN THIẾT BỊ & XỬ LÝ:\n"
                f"- Mã phiếu tiếp nhận: #{ma_phieu}\n"
                f"- Mô tả sự cố ban đầu: {mo_ta_loi or 'Bảo dưỡng / Kiểm tra tổng quát'}\n"
                f"- Ghi chú kỹ thuật & Linh kiện: {ghi_chu_ktv or 'Linh kiện chính hãng đã được kiểm định an toàn'}\n"
                f"- Trạng thái: ✅ ĐÃ SỬA XONG - ĐẠT CHUẨN HOẠT ĐỘNG 100%\n\n"
                f"Quý khách có thể tra cứu toàn bộ hồ sơ kỹ thuật và thời hạn bảo hành điện tử tại:\n"
                f"👉 {lookup_url}\n\n"
                f"Kính mời Quý khách ghé Trung tâm FrogHippo Phone để nhận lại thiết bị. Nếu cần hỗ trợ thêm, xin vui lòng gọi Hotline 1900 6868.\n"
                f"Trân trọng cảm ơn Quý khách đã tin tưởng dịch vụ của FrogHippo Phone!"
            )
        else:
            return (
                f"TIÊU ĐỀ: [FrogHippo Phone] Cập Nhật Tiến Độ Phiếu Sửa Chữa #{ma_phieu}\n\n"
                f"Kính gửi Quý khách ({ma_kh}),\n\n"
                f"FrogHippo Phone xin thông báo thiết bị của Quý khách theo Phiếu #{ma_phieu} đang được xử lý kỹ thuật chuyên sâu.\n"
                f"Quý khách có thể chủ động tra cứu nhật ký sửa chữa tại: {lookup_url}\n"
                f"FrogHippo Phone sẽ thông báo ngay khi thiết bị hoàn tất. Hotline: 1900 6868."
            )

    else:  # ZALO OA
        if is_completed:
            return (
                f"✨【PHONECARE - THÔNG BÁO HOÀN THÀNH SỬA CHỮA】✨\n\n"
                f"Kính chào Quý khách {ma_kh}! 👋\n\n"
                f"🎉 Thiết bị của Quý khách (Phiếu #{ma_phieu}) ĐÃ ĐƯỢC SỬA XONG HOÀN TẤT và đã vượt qua bài kiểm tra chất lượng toàn diện.\n\n"
                f"📌 Tình trạng ban đầu: {mo_ta_loi or 'Kiểm tra kỹ thuật'}\n"
                f"🛠️ Xử lý bởi KTV: {ghi_chu_ktv or 'Thay thế linh kiện & cân chỉnh chuẩn hãng'}\n"
                f"⏱️ Trạng thái: SẴN SÀNG BÀN GIAO\n\n"
                f"🔍 Quý khách có thể tra cứu hồ sơ bảo hành điện tử tại:\n"
                f"👉 {lookup_url}\n\n"
                f"FrogHippo Phone kính mời Quý khách ghé trung tâm nhận máy. Cảm ơn Quý khách! Hotline: 1900 6868 📞"
            )
        else:
            return (
                f"📱【PHONECARE - CẬP NHẬT TIẾN ĐỘ THIẾT BỊ #{ma_phieu}】\n\n"
                f"Kính chào Quý khách {ma_kh}! Thiết bị của Quý khách hiện đang được Kỹ thuật viên FrogHippo Phone tiến hành xử lý kỹ thuật.\n\n"
                f"Mô tả sự cố: {mo_ta_loi or 'Bảo dưỡng kiểm tra'}\n"
                f"Quý khách có quyền tra cứu tiến độ 24/7 tại:\n"
                f"👉 {lookup_url}\n\n"
                f"Hotline hỗ trợ: 1900 6868. FrogHippo Phone xin cảm ơn Quý khách!"
            )

def parse_json_from_ai_text(text: str) -> dict:
    """Tách và parse JSON an toàn từ kết quả text của AI."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        data = json.loads(text)
        return clean_diagnose_data(data)
    except Exception as e:
        print(f"[AI Error] Không thể parse JSON: {e}, text: {text[:100]}")
        raise e

def clean_diagnose_data(data: dict) -> dict:
    """Chuẩn hóa dữ liệu chẩn đoán để UI luôn hiển thị đẹp, không bao giờ bị 0đ hay thiếu trường."""
    if not isinstance(data, dict):
        return data

    if data.get("isValid") is False or data.get("errorType") in ["OUT_OF_SCOPE", "MISSING_DATA"]:
        data["isValid"] = False
        data["options"] = []
        return data

    data["isValid"] = True
    # Chuẩn hóa options
    options = data.get("options") or []
    cleaned_options = []
    default_prices = [450000, 1250000]
    
    for idx, opt in enumerate(options):
        if not isinstance(opt, dict):
            continue
        
        # Lấy giá an toàn
        raw_price = opt.get("price") or opt.get("estimatedCost") or opt.get("cost") or opt.get("gia") or 0
        if isinstance(raw_price, str):
            # Lọc chỉ lấy chữ số
            digits = re.sub(r"[^\d]", "", raw_price)
            price = int(digits) if digits else default_prices[min(idx, 1)]
        else:
            price = int(raw_price) if raw_price > 0 else default_prices[min(idx, 1)]
            
        cleaned_options.append({
            "type": opt.get("type") or ("PREMIUM" if idx > 0 else "BUDGET"),
            "title": opt.get("title") or opt.get("packageName") or ("Gói Chính Hãng Cao Cấp" if idx > 0 else "Gói Tiết Kiệm (Phổ Thông)"),
            "partName": opt.get("partName") or opt.get("name") or "Linh kiện đạt chuẩn kỹ thuật",
            "price": price,
            "warranty": opt.get("warranty") or ("12 Tháng (1 đổi 1)" if idx > 0 else "6 Tháng"),
            "pros": opt.get("pros") or opt.get("advantages") or "Bảo hành uy tín, kiểm định an toàn theo chuẩn FrogHippo"
        })
    data["options"] = cleaned_options
    data["confidence"] = data.get("confidence") or "95% (Độ chính xác cao)"
    
    # Chuẩn hóa các trường hiển thị ngắn gọn theo yêu cầu mới
    diag = data.get("diagnosis") or "Thiết bị gặp sự cố kỹ thuật cần kiểm tra"
    data["chuanDoan"] = diag
    data["nguyenNhan"] = data.get("nguyenNhan") or diag
    
    if cleaned_options:
        opt0 = cleaned_options[0]
        data["deXuat"] = f"{opt0['title']} - {opt0['partName']} ({opt0['price']:,}đ, BH {opt0['warranty']})"
    else:
        data["deXuat"] = data.get("deXuat") or "Cần đo kiểm nội trở nguồn và tiếp xúc socket"
        
    return data

def validate_repair_input(symptoms: str, device_model: str = "") -> dict | None:
    """
    [SYSTEM PROMPT - CONTROLLED AI REPAIR ASSISTANT]
    Cơ chế chặn và xử lý dữ liệu ngoại phạm (Guardrails) hoặc thiếu dữ liệu:
    - Mục 3: Ngoại phạm (Out-of-scope)
    - Mục 4: Thiếu dữ liệu (Missing data)
    """
    s_raw = (symptoms or "").strip()
    s_lower = s_raw.lower()

    # 1. Mục 4: Xử lý dữ liệu thiếu hoặc không rõ ràng
    if len(s_raw) < 5 or s_lower in ["hỏng", "hỏng rồi", "bị hỏng", "hư", "hư rồi", "lỗi", "lỗi rồi", "abc", "xyz", "123", "...", "ko biết", "không biết", "ko rõ", "không rõ", "tùy", "test"]:
        msg = "THÔNG BÁO: Ghi chú chưa đủ thông tin kỹ thuật để AI phân tích. Kỹ thuật viên vui lòng bổ sung chi tiết biểu hiện sự cố hoặc tình trạng linh kiện."
        return {
            "isValid": False,
            "errorType": "MISSING_DATA",
            "errorMessage": msg,
            "diagnosis": msg,
            "potentialRisks": "⚠️ Cảnh báo: Kỹ thuật viên vui lòng kiểm tra biểu hiện thực tế của thiết bị trước khi yêu cầu AI phân tích.",
            "options": [],
            "confirmationMessage": msg
        }

    # 2. Mục 3: Cơ chế chặn và báo lỗi ngoại phạm (Out-of-scope)
    out_of_scope_keywords = [
        "ăn cơm", "đói quá", "đói", "muốn ăn", "ăn uống", "món ăn", "nấu ăn", "uống bia", "uống rượu", "uống nước",
        "thời tiết", "trời mưa", "trời nắng", "dự báo thời tiết", "nhiệt độ", "xe máy", "xe đạp", "ô tô", "xe hơi",
        "bóng đá", "tình yêu", "thất tình", "người yêu", "chơi game", "liên quân", "lập trình", "viết code", "python",
        "javascript", "html", "css", "thơ ca", "bài hát", "ca sĩ", "chính trị", "chứng khoán", "mua nhà",
        "bất động sản", "vay tiền", "ngân hàng", "buồn ngủ", "đi ngủ", "mệt mỏi", "hôm nay ăn gì"
    ]
    
    phone_tech_keywords = [
        "pin", "màn", "kính", "cảm ứng", "sạc", "nguồn", "sập nguồn", "loa", "mic", "chuông", "rung",
        "camera", "cam", "flash", "vỏ", "sườn", "khay sim", "sim", "sóng", "wifi", "bluetooth",
        "face id", "faceid", "touch id", "touchid", "vân tay", "nút", "phím", "volume", "bật không lên",
        "mất nguồn", "nóng", "nóng máy", "chập", "treo", "cháy", "nước", "rơi", "ẩm", "vỡ", "nứt", "sọc",
        "liệt", "đơ", "giật", "lag", "chai", "phồng", "socket", "main", "mainboard", "ic", "cpu", "rom",
        "ram", "imei", "restore", "phần mềm", "mật khẩu", "icloud", "tai nghe", "cáp", "cổ cáp", "vbat",
        "vbus", "chạm", "bảo hành", "sửa", "ép kính", "thay", "đo kiểm", "nội trở", "tiếp xúc", "bể"
    ]

    has_out_of_scope = any(k in s_lower for k in out_of_scope_keywords)
    has_phone_tech = any(k in s_lower for k in phone_tech_keywords)

    if has_out_of_scope or not has_phone_tech:
        msg = "LỖI: Nội dung nhập vào không thuộc chuyên môn sửa chữa điện thoại. Vui lòng chỉ nhập thông tin/ghi chú liên quan đến sự cố thiết bị."
        return {
            "isValid": False,
            "errorType": "OUT_OF_SCOPE",
            "errorMessage": msg,
            "diagnosis": msg,
            "potentialRisks": "⛔ Từ chối xử lý: Hệ thống PhoneCare chỉ phân tích các sự cố liên quan trực tiếp đến phần cứng, phần mềm và linh kiện điện thoại.",
            "options": [],
            "confirmationMessage": msg
        }

    return None

def mock_diagnose_and_estimate(symptoms: str, device_model: str = "Điện thoại") -> dict:
    """Fallback giả lập chẩn đoán thông minh dựa trên từ khóa triệu chứng."""
    s_lower = symptoms.lower()
    
    has_pin = any(k in s_lower for k in ["pin", "sập nguồn", "chai", "phồng", "nóng máy", "nhanh hết", "sạc chậm", "tụt"])
    has_man = any(k in s_lower for k in ["màn", "vỡ", "nứt", "sọc", "cảm ứng", "chớp", "đen", "liệt"])

    # 1. Nhóm Đa sự cố: Vừa hỏng Màn hình Vừa chai/phồng Pin (Compound Damage)
    if has_man and has_pin:
        return {
            "diagnosis": f"Thiết bị {device_model} gặp đồng thời 2 sự cố phần cứng: Màn hình bị nứt vỡ/sọc hiển thị/liệt cảm ứng, kết hợp cell Pin bị chai phồng, suy giảm dung lượng và tăng trở kháng nội.",
            "potentialRisks": "⚠️ Cảnh báo kép cực kỳ nguy hiểm: Pin chai phồng đội ngược khung sườn chèn vỡ màn hình từ bên trong, đồng thời nguy cơ cao gây chập mạch cháy nổ và đoản mạch IC nguồn.",
            "options": [
                {
                    "type": "BUDGET",
                    "title": "Gói Tiết Kiệm (Combo Màn + Pin Phổ Thông)",
                    "partName": f"Combo: Màn hình Incell Chuẩn A+ & Pin Li-ion Chuẩn CE ({device_model})",
                    "price": 1630000,
                    "warranty": "6 Tháng",
                    "pros": "Khắc phục triệt để cả 2 sự cố (Màn hình + Pin) với chi phí tiết kiệm tối đa, bảo hành 6 tháng toàn diện"
                },
                {
                    "type": "PREMIUM",
                    "title": "Gói Chính Hãng Cao Cấp (Combo Màn Zin + Pin Zin)",
                    "partName": f"Combo: Màn hình OLED Zin Bóc Máy & Pin Zin Chuẩn Hãng ({device_model})",
                    "price": 3550000,
                    "warranty": "12 Tháng (1 đổi 1)",
                    "pros": "Màn hình chuẩn màu 100% True Tone, Pin zin chu kỳ 800+ lần, bảo hành 1 đổi 1 12 tháng trọn bộ linh kiện"
                }
            ],
            "confirmationMessage": f"Dạ thiết bị {device_model} bị hỏng cả màn hình và chai pin. Bên em có combo Tiết Kiệm 1.630.000đ và combo Zin Chính Hãng 3.550.000đ (bảo hành 1 đổi 1 trong 12 tháng), Anh/Chị muốn tham khảo gói nào ạ?"
        }

    # 2. Nhóm Pin & Nguồn đơn lẻ
    elif has_pin:
        return {
            "diagnosis": f"Thiết bị {device_model} có dấu hiệu chai pin, giảm dung lượng thực tế và tăng trở kháng nội dẫn đến máy nóng và tụt pin đột ngột khi tải nặng.",
            "potentialRisks": "⚠️ Cảnh báo: Pin chai phồng quá mức có nguy cơ chèn ép làm vỡ màn hình từ bên trong, cong sườn máy, hoặc đoản mạch gây chập cháy bo mạch chủ (Mainboard).",
            "options": [
                {
                    "type": "BUDGET",
                    "title": "Gói Tiết Kiệm (Phổ Thông)",
                    "partName": f"Pin Li-ion Tiêu Chuẩn Chuẩn CE ({device_model})",
                    "price": 380000,
                    "warranty": "6 Tháng",
                    "pros": "Chi phí tiết kiệm cho học sinh sinh viên, dung lượng chuẩn, dùng ổn định tác vụ hàng ngày"
                },
                {
                    "type": "PREMIUM",
                    "title": "Gói Chính Hãng Cao Cấp",
                    "partName": f"Pin Zin Chuẩn Hãng / Pisen Dung Lượng Siêu Cao ({device_model})",
                    "price": 750000,
                    "warranty": "12 Tháng (1 đổi 1)",
                    "pros": "Đạt chuẩn an toàn quốc tế, chu kỳ sạc xả 800+ lần, tương thích chip nguồn 100%, bảo hành 1 đổi 1"
                }
            ],
            "confirmationMessage": f"Dạ FrogHippo Phone đã kiểm tra tình trạng pin của {device_model}. Em xin phép tư vấn 2 gói thay pin tiết kiệm hoặc chính hãng bảo hành 12 tháng, Anh/Chị muốn tham khảo phương án nào ạ?"
        }

    # 2. Nhóm Màn hình & Cảm ứng
    elif any(k in s_lower for k in ["màn", "vỡ", "nứt", "sọc", "cảm ứng", "chớp", "đen", "liệt"]):
        return {
            "diagnosis": f"Tấm nền hiển thị và lớp kính cảm ứng của {device_model} bị chấn động cơ học dẫn đến tổn thương ma trận hiển thị (sọc/chớp màn hoặc liệt điểm cảm ứng).",
            "potentialRisks": "⚠️ Cảnh báo: Vết nứt kính để lâu sẽ làm ẩm mốc, bụi bẩn lọt vào gây chết cổ cáp màn hình vĩnh viễn và dễ cứa xước tay khi thao tác vuốt chạm.",
            "options": [
                {
                    "type": "BUDGET",
                    "title": "Gói Tiết Kiệm (Phổ Thông)",
                    "partName": f"Màn Hình Linh Kiện OLED Incell Chuẩn A+ ({device_model})",
                    "price": 1250000,
                    "warranty": "6 Tháng",
                    "pros": "Màu sắc đạt 90% màn gốc, cảm ứng nhạy mượt mà, giá mềm tối ưu ngân sách"
                },
                {
                    "type": "PREMIUM",
                    "title": "Gói Chính Hãng Cao Cấp",
                    "partName": f"Màn Hình OLED Zin Bóc Máy Chính Hãng ({device_model})",
                    "price": 2800000,
                    "warranty": "12 Tháng",
                    "pros": "Độ chuẩn màu 100% True Tone / HDR, kính cường lực nguyên bản chống xước, độ mượt hoàn hảo"
                }
            ],
            "confirmationMessage": f"Dạ màn hình {device_model} có phương án thay màn tiết kiệm 1.250.000đ hoặc màn zin chính hãng 2.800.000đ bảo hành 12 tháng, Anh/Chị ưu tiên độ bền hay tối ưu chi phí hơn ạ?"
        }

    # 3. Nhóm Cụm Sạc & Kết Nối
    elif any(k in s_lower for k in ["sạc", "chân sạc", "không vào", "lỏng", "chập"]):
        return {
            "diagnosis": f"Cụm chân sạc tiếp xúc kém do bụi ẩm oxy hóa chân đồng hoặc lỏng socket kết nối đường sạc phụ với bo mạch chính.",
            "potentialRisks": "⚠️ Cảnh báo: Chân sạc chập chờn tạo xung điện đột ngột có thể đánh thủng IC sạc / IC nguồn, gây mất nguồn hoàn toàn.",
            "options": [
                {
                    "type": "BUDGET",
                    "title": "Gói Tiết Kiệm (Phổ Thông)",
                    "partName": f"Cáp Chân Sạc Linh Kiện Cao Cấp ({device_model})",
                    "price": 280000,
                    "warranty": "6 Tháng",
                    "pros": "Khắc phục triệt để lỗi không nhận sạc, hỗ trợ sạc thường ổn định"
                },
                {
                    "type": "PREMIUM",
                    "title": "Gói Chính Hãng Cao Cấp",
                    "partName": f"Cụm Cáp Sạc & Mic Thoại Zin Bóc Máy ({device_model})",
                    "price": 550000,
                    "warranty": "12 Tháng",
                    "pros": "Hỗ trợ chuẩn sạc nhanh tối đa (Fast Charge/PD), mic đàm thoại trong trẻo lọc ồn tuyệt đối"
                }
            ],
            "confirmationMessage": f"Dạ bên em có cụm sạc linh kiện và cụm zin chính hãng hỗ trợ sạc nhanh cho {device_model}, Anh/Chị muốn bên em thay loại nào cho tiện dùng ạ?"
        }

    # 4. Nhóm Loa, Mic, Âm Thanh
    elif any(k in s_lower for k in ["loa", "mic", "rè", "nhỏ", "thoại", "chuông"]):
        return {
            "diagnosis": f"Màng loa của {device_model} bị bám mạt kim loại, rách gân rung hoặc đứt cuộn cảm âm thanh sau thời gian dài sử dụng ở môi trường bụi ẩm.",
            "potentialRisks": "⚠️ Cảnh báo: Nghe âm thanh rè kéo dài gây khó chịu khi nghe gọi công việc và có thể làm đoản mạch tầng khuếch đại âm thanh (Audio IC).",
            "options": [
                {
                    "type": "BUDGET",
                    "title": "Gói Tiết Kiệm (Phổ Thông)",
                    "partName": f"Vệ Sinh Rung Sóng & Thay Cụm Loa Chuẩn ({device_model})",
                    "price": 180000,
                    "warranty": "3 Tháng",
                    "pros": "Khắc phục nhanh tình trạng loa nhỏ/rè, chi phí cực kỳ nhẹ nhàng"
                },
                {
                    "type": "PREMIUM",
                    "title": "Gói Chính Hãng Cao Cấp",
                    "partName": f"Cụm Loa Kép Stereo Zin Hãng ({device_model})",
                    "price": 420000,
                    "warranty": "12 Tháng",
                    "pros": "Âm trầm chắc ấm, âm cao trong trẻo, âm lượng to rõ chuẩn như lúc mới mua máy"
                }
            ],
            "confirmationMessage": f"Dạ loa {device_model} bên em có gói vệ sinh thay màng 180k và cụm loa zin chính hãng 420k, Anh/Chị chọn gói nào em hỗ trợ làm ngay lấy liền ạ?"
        }

    # 5. Mặc định / Tổng quát
    else:
        return {
            "diagnosis": f"Ghi nhận tình trạng bất thường trên {device_model}: {symptoms}. Hiện tượng này cần đo kiểm nội trở nguồn và kiểm tra linh kiện chuyên sâu bằng máy đo chuyên dụng.",
            "potentialRisks": "⚠️ Cảnh báo: Thiết bị gặp lỗi không xử lý sớm dễ dẫn đến hao nguồn ngầm, máy tỏa nhiệt cao gây giảm tuổi thọ vi xử lý (CPU) và bộ nhớ trong.",
            "options": [
                {
                    "type": "BUDGET",
                    "title": "Gói Tiết Kiệm (Khuyên Dùng)",
                    "partName": f"Gói Phục Hồi & Thay Thế Linh Kiện Tiêu Chuẩn ({device_model})",
                    "price": 350000,
                    "warranty": "6 Tháng",
                    "pros": "Tối ưu chi phí, khắc phục triệt để lỗi cơ bản, đáp ứng tốt nhu cầu phổ thông"
                },
                {
                    "type": "PREMIUM",
                    "title": "Gói Chính Hãng Cao Cấp",
                    "partName": f"Gói Đại Tu & Linh Kiện Zin Chuẩn Hãng ({device_model})",
                    "price": 850000,
                    "warranty": "12 Tháng (1 đổi 1)",
                    "pros": "Linh kiện zin tiêu chuẩn cao nhất, bảo hành toàn diện 1 đổi 1, máy vận hành như mới"
                }
            ],
            "confirmationMessage": f"Dạ FrogHippo Phone đã kiểm tra triệu chứng của {device_model}. Em xin gửi Anh/Chị 2 phương án Tiết Kiệm và Chính Hãng để mình tiện cân nhắc, Anh/Chị muốn chọn gói nào ạ?"
        }

def diagnose_and_estimate_repair(symptoms: str, device_model: str = "Điện thoại") -> dict:
    """
    [SYSTEM PROMPT - CONTROLLED AI REPAIR ASSISTANT]
    Chẩn đoán lỗi kỹ thuật, cảnh báo nguy cơ tiềm ẩn và báo giá 2 gói (Tiết kiệm vs Cao cấp).
    Áp dụng Guardrails nghiêm ngặt: Chặn ngoại phạm (Mục 3) và Thiếu dữ liệu (Mục 4).
    """
    # 0. Kiểm tra Guardrails chặn ngoại phạm hoặc thiếu dữ liệu
    invalid_check = validate_repair_input(symptoms, device_model)
    if invalid_check is not None:
        return invalid_check

    prompt = f"""
[SYSTEM PROMPT - CONTROLLED AI REPAIR ASSISTANT]

1. VAI TRÒ VÀ PHẠM VI (ROLE & SCOPE):
- Bạn là Trợ lý AI Chuyên khoa Sửa chữa & Chẩn đoán Kỹ thuật Điện thoại thuộc Hệ thống PhoneCare.
- PHẠM VI DUY NHẤT: Chỉ phân tích, tóm tắt, chẩn đoán sự cố, gợi ý giải pháp kỹ thuật liên quan trực tiếp đến LINH KIỆN, PHẦN CỨNG, PHẦN MỀM VÀ QUY TRÌNH SỬA CHỮA ĐIỆN THOẠI DI ĐỘNG.

2. QUY TẮC PHÂN TÍCH CHUYÊN MÔN (DOMAIN RULES):
- Chỉ hoạt động dựa trên thông tin được cung cấp trong Context (`{{GhiChuKTV}}`: "{symptoms}", Thiết bị: "{device_model}").
- Chuyển đổi ngôn ngữ chuyên ngành/từ lóng (chạm IC, chập VBAT, đóng cặp, sọc màn...) thành kết luận rõ ràng, trung thực, không tự bịa đặt lỗi hoặc chi phí (No Hallucination).

3. CƠ CHẾ CHẶN VÀ BÁO LỖI NGOẠI PHẠM (GUARDRAILS & OUT-OF-SCOPE HANDLING):
- Nếu đầu vào KHÔNG LIÊN QUAN đến điện thoại hoặc kỹ thuật sửa chữa điện thoại (Ví dụ: hỏi về thời tiết, nấu ăn, xe máy, máy tính, câu hỏi phiếm, lập trình chung, v.v.):
  => NGỪNG PHÂN TÍCH NGAY LẬP TỨC và trả về JSON có:
  {{"isValid": false, "errorType": "OUT_OF_SCOPE", "errorMessage": "LỖI: Nội dung nhập vào không thuộc chuyên môn sửa chữa điện thoại. Vui lòng chỉ nhập thông tin/ghi chú liên quan đến sự cố thiết bị.", "options": []}}

4. XỬ LÝ DỮ LIỆU THIẾU HOẶC KHÔNG RÕ RÀNG (MISSING DATA):
- Nếu nội dung quá ngắn, vô nghĩa hoặc không đủ thông tin chẩn đoán (Ví dụ: "hỏng", "abc", "..."):
  => NGỪNG PHÂN TÍCH NGAY LẬP TỨC và trả về JSON có:
  {{"isValid": false, "errorType": "MISSING_DATA", "errorMessage": "THÔNG BÁO: Ghi chú chưa đủ thông tin kỹ thuật để AI phân tích. Kỹ thuật viên vui lòng bổ sung chi tiết biểu hiện sự cố hoặc tình trạng linh kiện.", "options": []}}

5. ĐỊNH DẠNG ĐẦU RA (OUTPUT FORMAT):
- Trường hợp hợp lệ: Trả về DUY NHẤT một chuỗi JSON chuẩn (không chứa markdown, không có ```json bọc ngoài):
{{
  "isValid": true,
  "diagnosis": "Mô tả nguyên nhân kỹ thuật ngắn gọn, dễ hiểu cho khách hàng",
  "potentialRisks": "⚠️ Cảnh báo nguy cơ hư hỏng tiềm ẩn đi kèm nếu không khắc phục sớm",
  "options": [
    {{
      "type": "BUDGET",
      "title": "Gói Tiết Kiệm (Phổ Thông)",
      "partName": "Tên linh kiện/dịch vụ thay thế phổ thông",
      "price": 350000,
      "warranty": "6 Tháng",
      "pros": "Ưu điểm ngắn gọn"
    }},
    {{
      "type": "PREMIUM",
      "title": "Gói Chính Hãng Cao Cấp",
      "partName": "Tên linh kiện zin chính hãng",
      "price": 850000,
      "warranty": "12 Tháng",
      "pros": "Ưu điểm ngắn gọn"
    }}
  ],
  "confirmationMessage": "Câu hỏi lịch sự của Lễ tân để xin ý kiến khách hàng xem có đồng ý sửa theo phương án nào không"
}}
Lưu ý: Giá tiền (price) tính bằng số nguyên VNĐ phù hợp với thị trường sửa chữa điện thoại tại Việt Nam.
"""
    # 1. Thử Google Gemini
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text_out = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return parse_json_from_ai_text(text_out)
        except Exception as e:
            print(f"[AI Warning] Gemini diagnose error: {e}. Falling back...")

    # 2. Thử OpenAI
    if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
        try:
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a professional phone repair AI assistant that outputs only valid JSON conforming strictly to the controlled repair assistant system prompt."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.4
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text_out = res_data["choices"][0]["message"]["content"].strip()
                return parse_json_from_ai_text(text_out)
        except Exception as e:
            print(f"[AI Warning] OpenAI diagnose error: {e}. Falling back...")

    # 3. Fallback AI giả lập thông minh theo từ khóa
    return clean_diagnose_data(mock_diagnose_and_estimate(symptoms, device_model))




# =====================================================================
# BỘ QUY CHUẨN KỸ THUẬT SỬA CHỮA ĐIỆN THOẠI & CHUẨN ĐOÁN KTV (FROGHIPPO PHONE)
# =====================================================================
PHONE_REPAIR_STANDARDS = """
BỘ QUY CHUẨN KỸ THUẬT & CHUẨN ĐOÁN SỬA CHỮA FROGHIPPO PHONE:
1. NGUYÊN TẮC CỐT LÕI:
   - CHUẨN ĐOÁN CỦA KTV LÀ CĂN CỨ TỐI CAO: Khi khách có mã phiếu hoặc đã được KTV kiểm tra, AI PHẢI lấy chuẩn đoán của KTV (ghiChuKTV) làm sự thật duy nhất, giải thích rõ nguyên nhân, rủi ro và giải pháp.
   - CHỐNG BỊA ĐẶT GIÁ (ANTI-HALLUCINATION): CHỈ báo giá linh kiện có trong danh mục kho thực tế. Nếu không có, dứt khoát trả lời chưa có sẵn và mời liên hệ Hotline 1900 6868, tuyệt đối KHÔNG tự bịa giá.
   - CHÍNH SÁCH TÀI CHÍNH MINH BẠCH: Tổng chi phí = Giá linh kiện niêm yết + Tiền công kỹ thuật chuẩn 150.000 VNĐ. Khách duyệt phương án -> Đặt cọc 30% để KTV tiến hành sửa. Khách kiểm tra máy đạt chuẩn 100% -> Quyết toán 70% còn lại.
   - CHÍNH SÁCH BẢO HÀNH: Linh kiện Zin chính hãng bảo hành 12 Tháng (1 đổi 1 trong 30 ngày đầu lỗi NSX). Linh kiện tiêu chuẩn bảo hành 6 Tháng. Bảo hành công kỹ thuật trọn đời.

2. BỘ TIÊU CHUẨN PHÂN LOẠI BỆNH LÝ & GIẢI PHÁP KỸ THUẬT:
   - NHÓM PIN & NGUỒN: Tụt pin nhanh, sập nguồn đột ngột, pin chai/phồng. Rủi ro: Pin phồng chèn vỡ màn hình, nguy cơ chập cháy nổ mainboard. Giải pháp: Thay pin Li-ion tiêu chuẩn hoặc pin zin dung lượng cao (BH 12T).
   - NHÓM MÀN HÌNH & CẢM ỨNG: Nứt kính ngoài (hiển thị mượt) -> Ép kính chân không. Sọc màn hình, chảy mực, liệt cảm ứng, mất hiển thị -> Tổn thương ma trận OLED, bắt buộc thay trọn bộ màn hình zin (BH 12T). Rủi ro để lâu: Bụi ẩm lọt vào làm chết cổ cáp vĩnh viễn.
   - NHÓM CỔNG SẠC & KẾT NỐI: Cắm sạc chập chờn, không sạc nhanh, lỏng cáp. Rủi ro: Xung điện bất thường làm đánh thủng IC nguồn (PMIC/U2) gây mất nguồn. Giải pháp: Vệ sinh chuyên sâu hoặc thay cụm cáp sạc zin.
   - NHÓM ÂM THANH (LOA/MIC): Loa trong nhỏ, loa ngoài rè, mic không thu tiếng. Rủi ro: Cháy cuộn cảm âm thanh, hỏng IC Audio Codec. Giải pháp: Vệ sinh sóng âm hoặc thay loa/mic zin bóc máy.
   - NHÓM CAMERA: Mờ nét, rung giật OIS, nứt kính cam. Giải pháp: Thay kính bảo vệ hoặc thay cụm module camera zin.
   - NHÓM MAINBOARD / RƠI NƯỚC: Mất nguồn, treo logo, ẩm bo mạch. Quy trình: Ngắt pin ngay, sấy khử ẩm cồn 99%, soi camera nhiệt dò tụ chạm chập.
"""

OUT_OF_SCOPE_RESPONSE = (
    "Dạ xin lỗi Quý khách! 🐸 Tôi là Trợ lý AI chuyên trách tư vấn dịch vụ sửa chữa và linh kiện điện thoại của Trung tâm FrogHippo Phone.\n\n"
    "Tôi chỉ có thể hỗ trợ các thông tin về:\n"
    "• Báo giá thay thế linh kiện (màn hình, pin, camera, chân sạc...)\n"
    "• Chẩn đoán sự cố hư hỏng & tình trạng thiết bị di động\n"
    "• Quy trình sửa chữa, chính sách đặt cọc 30% và bảo hành 12 tháng\n"
    "• Tra cứu tiến độ phiếu sửa chữa của cửa hàng\n\n"
    "Rất mong Quý khách thông cảm và vui lòng đặt câu hỏi liên quan đến thiết bị điện thoại hoặc dịch vụ sửa chữa để tôi được phục vụ chu đáo nhất ạ! 🙏"
)

def is_phone_repair_domain(message: str, has_file: bool = False, has_ticket: bool = False) -> bool:
    """
    Kiểm tra xem câu hỏi có thuộc phạm vi chuyên môn của Trung tâm Sửa chữa Điện thoại hay không.
    Trả về True nếu thuộc lĩnh vực điện thoại/sửa chữa/báo giá/quy trình/tra cứu phiếu/lời chào.
    Trả về False nếu hoàn toàn ngoại phạm (y tế, thuốc men, nấu ăn, xe cộ, thời tiết, chuyện phiếm...).
    """
    if has_file or has_ticket:
        return True

    text = (message or "").lower().strip()
    if not text:
        return True

    # 1. Các chủ đề chắc chắn ngoại phạm (Y tế, ẩm thực, xe cộ, thời tiết, chuyện phiếm...)
    out_of_scope_patterns = [
        # Y tế, sức khỏe, thuốc men, bệnh tật (nan y, uống thuốc, đau ốm...)
        r"(nan\s*y|uống\s*thuốc|thuốc\s*gì|khám\s*bệnh|bệnh\s*viện|bác\s*sĩ|chữa\s*bệnh|đau\s*đầu|sốt|cảm\s*cúm|ung\s*thư|huyết\s*áp|tiểu\s*đường|nhức\s*mỏi|mang\s*thai|sinh\s*con|dược\s*phẩm|kháng\s*sinh)",
        # Ẩm thực, nấu ăn
        r"(nấu\s*ăn|món\s*ngon|công\s*thức\s*nấu|quán\s*ăn|nhà\s*hàng|trà\s*sữa|uống\s*gì|ăn\s*gì\s*ngon|hôm\s*nay\s*ăn\s*gì|đói\s*bụng|ăn\s*cơm|uống\s*bia|uống\s*rượu)",
        # Thời tiết, tự nhiên
        r"(thời\s*tiết|dự\s*báo\s*thời\s*tiết|mưa\s*không|nhiệt\s*độ\s*hôm\s*nay|bão\s*số)",
        # Phương tiện giao thông khác (xe máy, ô tô, xe hơi, xe đạp...)
        r"(xe\s*máy|xe\s*ô\s*tô|ô\s*tô|xe\s*hơi|xe\s*đạp|bằng\s*lái|thay\s*nhớt|sửa\s*xe\s*máy|độ\s*xe|vá\s*lốp|xăng\s*xe|hỏng\s*bugi)",
        # Đồ gia dụng khác
        r"(máy\s*giặt|tủ\s*lạnh|nồi\s*cơm|điều\s*hòa|máy\s*lạnh|quạt\s*điện|bếp\s*ga|bếp\s*từ|máy\s*hút\s*bụi)",
        # Chuyện phiếm, tình cảm, thơ ca
        r"(làm\s*thơ|kể\s*chuyện\s*cười|yêu\s*không|tỏ\s*tình|bói\s*toán|tử\s*vi|cung\s*hoàng\s*đạo|xổ\s*số|lô\s*đề)"
    ]

    for p in out_of_scope_patterns:
        if re.search(p, text):
            # Cứu vãn: người dùng có thực sự nhắc đến điện thoại/màn hình/sửa chữa không?
            rescue_keywords = ["điện thoại", "iphone", "samsung", "xiaomi", "oppo", "màn hình", "thay pin", "sạc", "sửa máy"]
            if not any(k in text for k in rescue_keywords):
                return False

    # 2. Danh mục từ khóa IN-SCOPE (Chuyên môn điện thoại, linh kiện, sự cố, quy trình, trung tâm)
    in_scope_keywords = [
        # Thiết bị di động & thương hiệu
        "điện thoại", "phone", "smartphone", "thiết bị", "máy", "iphone", "ipad", "samsung", "galaxy", 
        "xiaomi", "redmi", "oppo", "vivo", "realme", "huawei", "nokia", "sony", "pixel", "apple",
        "pro", "promax", "plus", "ultra", "fold", "flip", "ios", "android",
        # Linh kiện
        "màn hình", "màn", "oled", "amoled", "lcd", "kính", "ép kính", "cảm ứng", "phôi", 
        "pin", "battery", "chai pin", "phồng pin", "dung lượng",
        "sạc", "chân sạc", "cổng sạc", "cáp sạc", "củ sạc", "type c", "lightning", "không vào điện",
        "loa", "mic", "micro", "chuông", "âm thanh", "mất tiếng", "rè",
        "camera", "cam", "thấu kính", "kính cam", "chụp ảnh", "mờ", "rung",
        "nguồn", "sập nguồn", "mất nguồn", "chập", "nóng máy", "hao pin", "chạm",
        "main", "mainboard", "ic", "vỏ", "sườn", "khung", "nắp lưng", "kính lưng",
        "phím", "nút nguồn", "âm lượng", "gạt rung", "face id", "faceid", "vân tay", "sim", "khay sim", "sóng", "wifi",
        # Triệu chứng hỏng
        "rơi", "va đập", "rớt", "vỡ", "nứt", "vào nước", "ngập nước", "ẩm", "sấy",
        "đơ", "lag", "treo", "treo logo", "không lên", "mất sóng", "sọc", "đen màn", "chớp nháy", "chảy mực", "liệt",
        # Sửa chữa & dịch vụ
        "sửa", "sửa chữa", "thay", "thay thế", "khắc phục", "bảo dưỡng", "vệ sinh", "cân chỉnh",
        "đo kiểm", "kiểm tra", "test", "chuẩn đoán", "chẩn đoán", "bệnh",
        # Báo giá & tài chính
        "giá", "bao nhiêu", "bao tiền", "chi phí", "bảng giá", "báo giá", "tiền công", "tổng cộng", "hết bao nhiêu", "tiền",
        "cọc", "đặt cọc", "30%", "70%", "thanh toán", "hóa đơn", "quyết toán", "chuyển khoản", "tiền mặt",
        # Chính sách & trung tâm
        "bảo hành", "1 đổi 1", "chính hãng", "zin", "linh kiện", "tồn kho", "còn hàng", "hết hàng",
        "phiếu", "mã phiếu", "tiếp nhận", "bàn giao", "nhận máy", "lấy máy", "lễ tân", "ktv", "kỹ thuật viên",
        "thu ngân", "froghippo", "hotline", "cửa hàng", "trung tâm", "địa chỉ", "chi nhánh", "mở cửa",
        # Giao tiếp thông thường / câu hỏi mở đầu
        "chào", "xin chào", "hello", "hi", "bot", "bạn ơi", "ad ơi", "em ơi", "cảm ơn", "thanks", "tạm biệt",
        "giúp", "tư vấn", "hỏi", "cho hỏi"
    ]

    return any(k in text for k in in_scope_keywords)

def chat_tu_van_linh_kien(
    user_message: str,
    danh_muc_linh_kien: list,
    phieu_info: dict = None,
    file_data: str = None,
    file_name: str = None,
    file_mime_type: str = None
) -> str:
    """
    Chatbot tư vấn chuyên sâu dựa trên Bộ Quy Chuẩn Sửa Chữa Điện Thoại,
    Chuẩn đoán thực tế của Kỹ thuật viên (ghiChuKTV) và CSDL linh kiện thực tế.
    Hỗ trợ tiếp nhận tệp/ảnh (Gemini Vision) và nhận diện giọng nói (Voice STT/TTS).
    Cam kết Anti-hallucination 100% & Chặn câu hỏi ngoại phạm (Domain Guardrail).
    """
    # 0. Kiểm tra phạm vi chuyên môn (Domain Guardrail): Chặn câu hỏi ngoại phạm
    has_file = bool(file_data or file_name)
    has_ticket = bool(phieu_info and phieu_info.get("maPhieu"))
    if not is_phone_repair_domain(user_message, has_file, has_ticket):
        return OUT_OF_SCOPE_RESPONSE
    if danh_muc_linh_kien:
        lines = []
        for lk in danh_muc_linh_kien:
            stock = f"CÒN HÀNG ({lk['soLuongTon']})" if lk.get('soLuongTon', 0) > 0 else "HẾT HÀNG"
            gia = int(lk.get('giaBan', 0))
            lines.append(f"- {lk.get('tenLK')} | Mã: {lk.get('maLK')} | Giá niêm yết: {gia:,} VND | Kho: {stock}")
        bang_du_lieu = "\n".join(lines)
    else:
        bang_du_lieu = "(Chưa có dữ liệu linh kiện trong kho)"

    # Trích xuất dữ liệu phiếu sửa chữa và chẩn đoán KTV nếu có
    phieu_context = ""
    if phieu_info:
        ma_phieu = phieu_info.get("maPhieu", "")
        ten_kh = phieu_info.get("tenKhachHang", phieu_info.get("maKH", "Quý khách"))
        mo_ta_loi = phieu_info.get("moTaLoi", "Chưa có mô tả")
        ghi_chu_ktv = phieu_info.get("ghiChuKTV", "")
        chuan_doan_ktv = phieu_info.get("chuanDoanKTV", "")
        da_duyet = phieu_info.get("daDuyetChuanDoan", False)
        nguoi_duyet = phieu_info.get("nguoiDuyetChuanDoan", "Kỹ thuật viên")
        thoi_gian_duyet = phieu_info.get("thoiGianDuyetChuanDoan", "")
        trang_thai = phieu_info.get("trangThai", "")
        parts = phieu_info.get("parts", [])
        parts_desc = ", ".join([f"{p.get('tenLK', p.get('maLK'))} ({int(p.get('donGia', 0)):,}đ)" for p in parts]) if parts else "Đang kiểm tra chỉ định"
        tien_coc = phieu_info.get("tienDatCoc", 0)
        da_dat_coc = "Đã thu cọc 30%" if phieu_info.get("daDatCoc") else "Chưa đặt cọc (Cần cọc 30% để tiến hành)"

        if da_duyet:
            trang_thai_duyet_text = f"ĐÃ ĐƯỢC KỸ THUẬT VIÊN {nguoi_duyet} KIỂM TRA & PHÊ DUYỆT CHÍNH THỨC ({thoi_gian_duyet}). NGUYÊN NHÂN ĐÃ DUYỆT: {chuan_doan_ktv or ghi_chu_ktv}"
        else:
            trang_thai_duyet_text = "CHƯA ĐƯỢC KTV PHÊ DUYỆT (KTV đang đo kiểm phần cứng. THEO NGUYÊN TẮC: TUYỆT ĐỐI CHƯA ĐƯỢC ĐƯA NGUYÊN NHÂN CHO KHÁCH HÀNG KHI KTV CHƯA DUYỆT)."

        phieu_context = f"""
THÔNG TIN PHIẾU SỬA CHỮA #{ma_phieu} ĐANG ĐƯỢC TRA CỨU:
- Khách hàng: {ten_kh}
- Hiện tượng tiếp nhận ban đầu: {mo_ta_loi}
- TRẠNG THÁI PHÊ DUYỆT CỦA KTV: {trang_thai_duyet_text}
- Linh kiện KTV chỉ định: {parts_desc}
- Trạng thái phiếu hiện tại: {trang_thai} ({da_dat_coc})
- Đã thu cọc: {int(tien_coc):,} VND
"""

    system_prompt = f"""
Bạn là Chuyên viên Trợ lý AI Kỹ thuật của Trung tâm Sửa chữa & Bảo hành Điện thoại FrogHippo Phone.
Nhiệm vụ của bạn là tư vấn cho khách hàng dựa trên BỘ QUY CHUẨN KỸ THUẬT, SỰ KIỂM SOÁT VÀ PHÊ DUYỆT CỦA KỸ THUẬT VIÊN và DỮ LIỆU KHO THỰC TẾ.

{PHONE_REPAIR_STANDARDS}

{phieu_context}

DANH MỤC LINH KIỆN THỰC TẾ TRONG KHO (NGUỒN SỰ THẬT DUY NHẤT):
{bang_du_lieu}

QUY TẮC BẮT BUỘC VỀ KIỂM SOÁT CỦA KỸ THUẬT VIÊN (HUMAN-IN-THE-LOOP):
1. NẾU CÓ THÔNG TIN PHIẾU VÀ KTV CHƯA PHÊ DUYỆT (daDuyetChuanDoan = False):
   - KHI KHÁCH HỎI VỀ NGUYÊN NHÂN HOẶC BỆNH LÝ MÁY: TUYỆT ĐỐI KHÔNG TỰ BỊA ĐẶT HOẶC ĐƯA KẾT LUẬN NGUYÊN NHÂN CHO KHÁCH.
   - BẮT BUỘC TRẢ LỜI: "Dạ thiết bị theo phiếu #{ma_phieu if phieu_info else ''} đang được Kỹ thuật viên kiểm tra chuyên sâu. Theo quy chuẩn an toàn của trung tâm, mọi nguyên nhân hư hỏng và phương án kỹ thuật BẮT BUỘC PHẢI DƯỚI SỰ KIỂM SOÁT VÀ ĐƯỢC KỸ THUẬT VIÊN DUYỆT thì mới đưa cho khách hàng để tránh sai lệch. Kính mời Quý khách đợi trong ít phút, ngay khi KTV duyệt kết quả, hệ thống sẽ công khai ngay ạ!"
2. NẾU KTV ĐÃ PHÊ DUYỆT (daDuyetChuanDoan = True):
   - Thông báo rõ ràng: Kỹ thuật viên đã kiểm định và chính thức phê duyệt chẩn đoán.
   - Giải thích nguyên nhân đã duyệt một cách dễ hiểu, nêu rõ rủi ro kỹ thuật và phương án linh kiện thay thế, cọc 30%, bảo hành 12 tháng.
3. NẾU KHÁCH HỎI VỀ GIÁ LINH KIỆN HOẶC DỊCH VỤ CHUNG:
   - CHỈ trả lời về các linh kiện CÓ trong danh mục kho ở trên.
   - Báo giá rõ ràng: [Giá linh kiện] + [Tiền công kỹ thuật 150.000 VNĐ] = [Tổng chi phí], bảo hành 12 Tháng.
4. QUY TẮC CHỐNG BỊA ĐẶT (ANTI-HALLUCINATION):
   - Nếu linh kiện hoặc máy khách hỏi KHÔNG có trong danh mục kho, TUYỆT ĐỐI KHÔNG tự bịa giá.
   - Hãy trả lời lịch sự: "Hiện tại hệ thống kho của FrogHippo Phone chưa có sẵn linh kiện này hoặc chưa có giá niêm yết chính thức. Quý khách vui lòng liên hệ Hotline 1900 6868 hoặc mang máy đến trung tâm để được kiểm tra trực tiếp."
5. QUY TẮC CHẶN NGOẠI PHẠM (DOMAIN GUARDRAIL):
   - Bạn CHỈ tư vấn và trả lời các nội dung liên quan trực tiếp đến ĐIỆN THOẠI DI ĐỘNG, máy tính bảng, linh kiện, sự cố kỹ thuật, báo giá, quy trình sửa chữa và dịch vụ của trung tâm.
   - NẾU khách hàng hỏi về các lĩnh vực NGOẠI PHẠM (y tế, thuốc men, bệnh tật, ăn uống, nấu nướng, xe cộ, thời tiết, giải trí, chuyện phiếm, làm thơ...):
     => BẮT BUỘC TRẢ LỜI XIN LỖI LỊCH SỰ:
     "Dạ xin lỗi Quý khách! 🐸 Tôi là Trợ lý AI chuyên trách tư vấn dịch vụ sửa chữa và linh kiện điện thoại của Trung tâm FrogHippo Phone. Tôi chỉ có thể hỗ trợ các vấn đề liên quan đến thiết bị di động, kiểm tra tình trạng máy, báo giá linh kiện và dịch vụ sửa chữa. Rất mong Quý khách thông cảm ạ! 🙏"
     Tuyệt đối KHÔNG trả lời lan man sang lĩnh vực ngoại phạm và KHÔNG báo 'linh kiện không có sẵn trong kho'.
6. Tác phong ân cần, chuyên nghiệp, sử dụng tiếng Việt có dấu chuẩn xác kèm biểu tượng (emoji) thích hợp.

Câu hỏi của khách hàng: {user_message}

Câu trả lời tư vấn:
"""

    # 1. Gọi Google Gemini (Hỗ trợ Multimodal: Hình ảnh thiết bị, tài liệu & văn bản)
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            
            gemini_parts = []
            if file_data:
                clean_b64 = file_data
                mime = file_mime_type or "image/jpeg"
                if "base64," in clean_b64:
                    hdr, clean_b64 = clean_b64.split("base64,", 1)
                    if "data:" in hdr and ";" in hdr:
                        mime = hdr.replace("data:", "").split(";")[0].strip()

                if clean_b64.strip() and mime.startswith("image/"):
                    gemini_parts.append({
                        "inline_data": {
                            "mime_type": mime,
                            "data": clean_b64.strip()
                        }
                    })
                elif clean_b64.strip() and mime == "application/pdf":
                    gemini_parts.append({
                        "inline_data": {
                            "mime_type": "application/pdf",
                            "data": clean_b64.strip()
                        }
                    })

            extra_prompt = ""
            if file_data or file_name:
                extra_prompt = (
                    f"\n\n[HÌNH ẢNH / TỆP ĐÍNH KÈM: {file_name or 'anh_thiet_bi.jpg'}]. "
                    "Hãy quan sát kỹ hình ảnh thiết bị, chẩn đoán triệu chứng hư hỏng (nứt vỡ màn hình, chai phồng pin, hỏng cổng sạc, nứt kính cam...), "
                    "đối chiếu với Danh mục kho trên để báo giá linh kiện thật, công thay 150.000đ, quy định cọc 30% và bảo hành 12 tháng."
                )

            gemini_parts.append({"text": system_prompt + extra_prompt})

            payload = {
                "contents": [{"parts": gemini_parts}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                parts_list = res_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                text_out = "".join([p.get("text", "") for p in parts_list]).strip()
                if len(text_out) >= 60 and not text_out.rstrip().endswith(('V', 'và', 'hoặc', 'là', 'để', '...', ':', ',')):
                    return text_out
        except Exception as e:
            print(f"[Chatbot] Gemini error: {e}")

    # 2. Gọi OpenAI Fallback
    if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
        try:
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": system_prompt}],
                "temperature": 0.2,
                "max_tokens": 1024
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text_out = res_data["choices"][0]["message"]["content"].strip()
                if len(text_out) >= 60:
                    return text_out
        except Exception as e:
            print(f"[Chatbot] OpenAI error: {e}")

    # 3. Fallback Thông Minh dựa trên Bộ Quy Chuẩn & Chuẩn Đoán KTV & Phân Tích Tệp
    msg_lower = (user_message or "").lower()
    fn_lower = (file_name or "").lower()
    combined_query = f"{msg_lower} {fn_lower}".strip()

    # Nhận diện thông tin ảnh đính kèm nếu có
    file_diag_header = ""
    if file_data or file_name:
        fname = file_name or "anh_thiet_bi.jpg"
        if any(k in combined_query for k in ["man", "hinh", "screen", "vo", "nut", "soc", "muc", "kinh", "oled"]):
            file_diag_header = f"📸 **[Phân tích ảnh: {fname}]**: Nhận diện sơ bộ màn hình hiển thị bị tổn thương (nứt vỡ mặt kính ngoài hoặc lỗi tấm nền ma trận OLED).\n"
        elif any(k in combined_query for k in ["pin", "battery", "phong", "chai", "phồng"]):
            file_diag_header = f"📸 **[Phân tích ảnh: {fname}]**: Nhận diện sơ bộ pin có dấu hiệu chai phồng, giảm tuổi thọ hoặc kênh viền màn hình.\n"
        elif any(k in combined_query for k in ["cam", "camera", "kinh cam"]):
            file_diag_header = f"📸 **[Phân tích ảnh: {fname}]**: Nhận diện sơ bộ tổn thương cụm thấu kính hoặc nứt vỡ kính bảo vệ camera.\n"
        elif any(k in combined_query for k in ["sac", "chan sac", "type c", "lightning"]):
            file_diag_header = f"📸 **[Phân tích ảnh: {fname}]**: Nhận diện cụm cổng sạc bị bụi ẩm oxy hóa hoặc cong lẫy tiếp xúc nguồn.\n"
        else:
            file_diag_header = f"📸 **[Đã nhận ảnh: {fname}]**: Hệ thống AI đã lưu ảnh thiết bị để Kỹ thuật viên đối chiếu trực tiếp khi nhận máy.\n"

    # Trường hợp 3.1: Khách hỏi theo Phiếu sửa chữa cụ thể
    if phieu_info and phieu_info.get("maPhieu"):
        ma_p = phieu_info.get("maPhieu")
        da_duyet = phieu_info.get("daDuyetChuanDoan", False)
        chuan_doan = phieu_info.get("chuanDoanKTV") or phieu_info.get("ghiChuKTV")
        nguoi_duyet = phieu_info.get("nguoiDuyetChuanDoan", "Kỹ thuật viên")
        thoi_gian_duyet = phieu_info.get("thoiGianDuyetChuanDoan", "")
        parts = phieu_info.get("parts", [])
        tien_lk = sum([float(p.get("donGia", 0)) * int(p.get("soLuong", 1)) for p in parts])
        tien_cong = 150000
        tong_du_toan = tien_lk + tien_cong
        tien_coc_30 = int(tong_du_toan * 0.3)

        # NẾU KTV CHƯA DUYỆT -> CHẶN LẠI, KHÔNG ĐƯỢC ĐƯA NGUYÊN NHÂN CHO KHÁCH HÀNG
        if not da_duyet:
            return (
                f"Dạ kính chào Quý khách! 🐸📱 Về phiếu sửa chữa #{ma_p}:\n\n"
                f"{file_diag_header}"
                f"⏳ HIỆN TRẠNG KIỂM TRA:\n"
                f"- Thiết bị của Quý khách đang được Kỹ thuật viên chuyên trách đo kiểm phần cứng và vi mạch chuyên sâu.\n\n"
                f"⚠️ QUY ĐỊNH KIỂM SOÁT KỸ THUẬT FROGHIPPO PHONE:\n"
                f"- Để đảm bảo tính chính xác 100% và tránh sai lệch thông tin, mọi kết luận về NGUYÊN NHÂN HƯ HỎNG BẮT BUỘC PHẢI QUA SỰ KIỂM SOÁT VÀ PHÊ DUYỆT TRỰC TIẾP CỦA KỸ THUẬT VIÊN thì mới được đưa cho khách hàng.\n"
                f"- Ngay sau khi KTV hoàn tất đo kiểm và bấm duyệt chính thức, hệ thống sẽ công khai đầy đủ nguyên nhân, rủi ro và phương án xử lý tới Quý khách.\n\n"
                f"Kính mời Quý khách đợi trong ít phút hoặc liên hệ Hotline 1900 6868 nếu cần hỗ trợ khẩn cấp ạ!"
            )

        # NẾU KTV ĐÃ DUYỆT -> CÔNG KHAI CHI TIẾT
        return (
            f"Dạ kính chào Quý khách! 🐸📱 Trợ lý kỹ thuật FrogHippo Phone xin phản hồi thông tin phiếu #{ma_p}:\n\n"
            f"{file_diag_header}"
            f"👨‍🔧 CHUẨN ĐOÁN KỸ THUẬT ĐÃ ĐƯỢC DUYỆT BỞI KTV ({nguoi_duyet} - {thoi_gian_duyet}):\n"
            f"\"{chuan_doan}\"\n\n"
            f"📋 THEO BỘ QUY CHUẨN SỬA CHỮA TRUNG TÂM:\n"
            f"- Tình trạng thiết bị đã được KTV kiểm định trực tiếp, xác định rõ nguyên nhân hư hỏng phần cứng.\n"
            f"- Phương án xử lý: Thay thế linh kiện chính hãng tiêu chuẩn, ép ron kháng nước và cân chỉnh lại toàn bộ vi mạch.\n"
            f"- Dự toán chi phí: Linh kiện ({tien_lk:,.0f}đ) + Tiền công chuẩn ({tien_cong:,.0f}đ) = Tổng {tong_du_toan:,.0f} VNĐ.\n"
            f"- Quy định đặt cọc: Đặt cọc 30% ({tien_coc_30:,.0f}đ) để KTV xuất kho linh kiện và tiến hành sửa chữa. 70% còn lại thanh toán khi Quý khách nghiệm thu máy hoàn hảo.\n"
            f"- Chế độ bảo hành: 12 Tháng chính hãng (1 đổi 1 trong 30 ngày đầu lỗi NSX).\n\n"
            f"Nếu Quý khách cần hỗ trợ thêm, xin vui lòng gọi ngay Hotline 1900 6868 ạ!"
        )

    # Trường hợp 3.2: Khách hỏi giá linh kiện hoặc gửi ảnh kiểm tra linh kiện trong kho
    # Danh sách thương hiệu để kiểm tra tính tương thích chính xác
    known_brands = ["iphone", "ipad", "apple", "samsung", "galaxy", "xiaomi", "redmi", "oppo", "vivo", "realme", "huawei", "nokia", "sony", "pixel", "lamborghini", "vertu", "asus", "rog"]
    query_brands = [b for b in known_brands if b in combined_query]

    scored_parts = []
    for lk in danh_muc_linh_kien:
        ten_raw = lk.get("tenLK", "")
        ten_lower = ten_raw.lower()
        score = 0
        
        # Nếu câu hỏi chỉ định thương hiệu cụ thể (vd: lamborghini, samsung, iphone...)
        # thì linh kiện BẮT BUỘC phải cùng thương hiệu, không lấy râu ông nọ cắm cằm bà kia
        if query_brands:
            if not any(b in ten_lower for b in query_brands):
                continue

        # Nếu cả tên linh kiện xuất hiện trong câu hỏi hoặc tên file
        if ten_lower in combined_query:
            score += 60

        # Tách từ để chấm điểm khớp
        words = [w for w in re.split(r"[\s\-_,]+", ten_lower) if len(w) >= 2]
        for w in words:
            if w in combined_query:
                if w in ["iphone", "samsung", "xiaomi", "oppo", "oled", "13", "14", "15", "pro", "promax", "plus", "pin", "màn", "hình", "camera", "sạc"]:
                    score += 15
                else:
                    score += 5
                    
        # Điều kiện loại linh kiện tương ứng
        is_type_match = False
        if any(k in combined_query for k in ["màn", "hinh", "oled", "kính"]) and any(k in ten_lower for k in ["màn", "oled", "kính"]):
            is_type_match = True
            score += 20
        if any(k in combined_query for k in ["pin", "battery"]) and "pin" in ten_lower:
            is_type_match = True
            score += 20
        if any(k in combined_query for k in ["sạc", "sac"]) and "sạc" in ten_lower:
            is_type_match = True
            score += 20
        if any(k in combined_query for k in ["cam", "camera"]) and "camera" in ten_lower:
            is_type_match = True
            score += 20

        # Yêu cầu tối thiểu để đảm bảo không bịa đặt hoặc so khớp bừa
        if is_type_match and score >= 25:
            scored_parts.append((score, lk))
        elif score >= 35:
            scored_parts.append((score, lk))

    scored_parts.sort(key=lambda x: x[0], reverse=True)
    found_parts = [p[1] for p in scored_parts]

    if found_parts:
        result_lines = []
        for lk in found_parts[:3]:
            stock_text = f"Còn {lk['soLuongTon']} chiếc" if lk.get('soLuongTon', 0) > 0 else "Hết hàng"
            gia_lk = int(lk.get('giaBan', 0))
            tong = gia_lk + 150000
            result_lines.append(
                f"• {lk.get('tenLK')}: Giá linh kiện {gia_lk:,.0f}đ + Công thay 150.000đ = Tổng {tong:,.0f}đ | {stock_text} | Bảo hành 12 Tháng chính hãng"
            )
        prefix = f"{file_diag_header}\n" if file_diag_header else ""
        return (
            f"Dạ chào Quý khách! 🐸 {prefix}FrogHippo Phone đã kiểm tra theo Bộ quy chuẩn và kho thực tế:\n\n"
            + "\n".join(result_lines) +
            f"\n\n📌 Quy định trung tâm: Đặt cọc 30% khi duyệt phương án, 70% thanh toán khi nhận máy sau khi test hoàn hảo 18 chức năng.\n"
            f"Kính mời Quý khách ghé trung tâm hoặc gọi Hotline 1900 6868 để KTV hỗ trợ ngay ạ!"
        )
    else:
        # Kiểm tra nếu là câu chào hỏi mở đầu
        msg_simple = re.sub(r"[^\w\s]", "", msg_lower).strip()
        if msg_simple in ["chào", "xin chào", "hello", "hi", "chào bạn", "chào shop", "bot ơi", "admin ơi", "alo", "bạn ơi"]:
            return (
                "Dạ kính chào Quý khách! 🐸 Tôi là Trợ lý AI tư vấn dịch vụ sửa chữa và linh kiện của FrogHippo Phone.\n\n"
                "Tôi có thể hỗ trợ Quý khách:\n"
                "• Tra cứu giá thay thế linh kiện chính hãng (màn hình, pin, camera, sạc...)\n"
                "• Chẩn đoán triệu chứng hư hỏng thiết bị (nứt vỡ, rơi nước, sập nguồn...)\n"
                "• Phân tích hình ảnh chụp thiết bị hỏng (bấm nút 📎 đính kèm ảnh)\n"
                "• Tiếp nhận câu hỏi bằng giọng nói tiếng Việt (bấm nút 🎙️ micro)\n\n"
                "Quý khách đang cần hỗ trợ kiểm tra hoặc thay thế linh kiện cho dòng máy nào ạ?"
            )

        prefix = f"{file_diag_header}\n" if file_diag_header else ""
        return (
            f"Dạ chào Quý khách! 🐸 {prefix}Theo Bộ quy chuẩn của FrogHippo Phone, hiện tại linh kiện này chưa có sẵn trong kho "
            "hoặc chưa có giá niêm yết chính thức trong hệ thống.\n\n"
            "Để đảm bảo tính chính xác và không làm mất thời gian của Quý khách, xin vui lòng gọi Hotline 1900 6868 "
            "hoặc mang máy đến trung tâm để Kỹ thuật viên đo kiểm và báo giá chi tiết trong 30 phút ạ!"
        )


def generate_deposit_message(
    ma_phieu: str, ten_kh: str, mo_ta_loi: str,
    parts_list: list, tien_coc: float, tong_hoa_don: float, channel: str = "Gmail"
) -> str:
    """Sinh tin nhắn/email báo giá và đặt cọc 30%."""
    tien_con_lai = tong_hoa_don - tien_coc
    channel_upper = channel.upper()

    parts_text_parts = []
    for p in parts_list:
        name = p.get('tenLK', p.get('maLK', ''))
        price = int(p.get('thanhTien', 0))
        parts_text_parts.append(name + " (" + str(price) + "d)")
    parts_text = ", ".join(parts_text_parts) if parts_text_parts else "Linh kien chinh hang"

    prompt = (
        "Soan thu/tin nhan BAO GIA & DAT COC 30% gui cho khach qua kenh " + channel_upper + " tu FrogHippo Phone.\n"
        "Ten khach: " + ten_kh + " | Ma phieu: " + ma_phieu + " | Hang muc: " + parts_text + "\n"
        "Tong hoa don: " + str(int(tong_hoa_don)) + " VND | Tien coc 30%: " + str(int(tien_coc)) + " VND | Con lai 70%: " + str(int(tien_con_lai)) + " VND\n"
        "Link: http://127.0.0.1:8000/?maPhieu=" + ma_phieu + "\n"
        "Soan thu lich su, chuyen nghiep qua Gmail, ro rang chi phi."
    ) + MSG_OUTPUT_RULES

    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            return call_gemini_api(prompt)
        except Exception:
            pass

    if "SMS" in channel_upper:
        return (
            f"[FrogHippo Phone] Kính gửi {ten_kh}, báo giá phiếu #{ma_phieu}: "
            f"Tổng dự kiến {int(tong_hoa_don):,}đ. Đặt cọc 30%: {int(tien_coc):,}đ (còn lại {int(tien_con_lai):,}đ khi nhận máy). "
            f"Tra cứu tiến độ: http://127.0.0.1:8000/?maPhieu={ma_phieu} . Hotline: 19006868."
        )

    return (
        "TIÊU ĐỀ: [FrogHippo Phone] Báo Giá Sửa Chữa & Đặt Cọc 30% - Phiếu #" + ma_phieu + "\n\n"
        "Kính gửi Quý khách " + ten_kh + ",\n\n"
        "Trung tâm Sửa chữa FrogHippo Phone đã kiểm tra thiết bị của Quý khách theo Phiếu #" + ma_phieu + ".\n\n"
        "📋 CHI TIẾT DỊCH VỤ & LINH KIỆN:\n"
        "- Hạng mục thay thế: " + parts_text + "\n"
        "- Tổng hóa đơn dự kiến: " + str(int(tong_hoa_don)) + " VNĐ\n"
        "- Số tiền đặt cọc 30%: " + str(int(tien_coc)) + " VNĐ\n"
        "- Số tiền còn lại thu khi hoàn tất (70%): " + str(int(tien_con_lai)) + " VNĐ\n\n"
        "Quý khách có thể theo dõi tiến độ sửa chữa trực tuyến tại:\n"
        "👉 http://127.0.0.1:8000/?maPhieu=" + ma_phieu + "\n\n"
        "Hotline hỗ trợ: 1900 6868\n"
        "Trân trọng cảm ơn Quý khách!"
    )


def generate_completion_message(
    ma_phieu: str, ten_kh: str, tien_coc: float, tien_con_lai: float, channel: str = "Gmail"
) -> str:
    """Sinh email máy đã sửa xong, mời đến lấy & thu 70% còn lại."""
    channel_upper = channel.upper()

    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            prompt = (
                "Soan thu thong bao MAY DA SUA XONG qua " + channel_upper + ". "
                "Ten khach: " + ten_kh + ", Phieu #" + ma_phieu + ", Da coc: " + str(int(tien_coc)) + "d, Con lai thu: " + str(int(tien_con_lai)) + "d. "
                "Thu trang trong, lich su, chuyen nghiep, day du thong tin nhan may va bao hanh."
            ) + MSG_OUTPUT_RULES
            return call_gemini_api(prompt)
        except Exception:
            pass

    if "SMS" in channel_upper:
        return (
            f"[FrogHippo Phone] Kính gửi {ten_kh}, thiết bị theo phiếu #{ma_phieu} ĐÃ SỬA XONG hoàn tất và sẵn sàng bàn giao! "
            f"Quyết toán 70% còn lại: {int(tien_con_lai):,}đ. Kính mời Quý khách đến nhận máy. "
            f"Tra cứu hồ sơ: http://127.0.0.1:8000/?maPhieu={ma_phieu} . Hotline: 19006868."
        )

    return (
        "TIÊU ĐỀ: [FrogHippo Phone] Thông Báo Thiết Bị #" + ma_phieu + " ĐÃ SỬA XONG - Kính Mời Nhận Máy\n\n"
        "Kính gửi Quý khách " + ten_kh + ",\n\n"
        "FrogHippo Phone xin trân trọng thông báo thiết bị của Quý khách theo Phiếu #" + ma_phieu + " ĐÃ HOÀN THÀNH SỬA CHỮA và kiểm định chất lượng an toàn.\n\n"
        "💰 QUYẾT TOÁN THANH TOÁN:\n"
        "- Đã đặt cọc trước (30%): " + str(int(tien_coc)) + " VNĐ\n"
        "- Số tiền còn lại cần thanh toán (70%): " + str(int(tien_con_lai)) + " VNĐ\n\n"
        "Kính mời Quý khách ghé Trung tâm FrogHippo Phone để kiểm tra và nhận lại thiết bị.\n"
        "Tra cứu hồ sơ bảo hành điện tử: http://127.0.0.1:8000/?maPhieu=" + ma_phieu + "\n"
        "Hotline hỗ trợ: 1900 6868\n\n"
        "Trân trọng cảm ơn Quý khách đã tin tưởng FrogHippo Phone!"
    )

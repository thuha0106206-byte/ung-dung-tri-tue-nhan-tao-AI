

# =====================================================================
# CHATBOT TU VAN GIA LINH KIEN - GROUNDED 100% TREN DU LIEU THAT
# =====================================================================
def chat_tu_van_linh_kien(user_message: str, danh_muc_linh_kien: list) -> str:
    """
    Chatbot tra loi gia linh kien chinh xac 100% dua tren CSDL thuc te.
    Khong bao gio bịa gia.
    """
    if danh_muc_linh_kien:
        lines = []
        for lk in danh_muc_linh_kien:
            stock = "CON HANG (" + str(lk['soLuongTon']) + ")" if lk['soLuongTon'] > 0 else "HET HANG"
            lines.append("- " + lk['tenLK'] + " | Ma: " + lk['maLK'] + " | Gia ban: " + str(int(lk['giaBan'])) + " VND | Ton kho: " + stock)
        bang_du_lieu = "\n".join(lines)
    else:
        bang_du_lieu = "(Chua co du lieu linh kien trong he thong)"

    system_prompt = (
        "Ban la nhan vien tu van linh kien cua Trung tam sua chua FrogHippo Phone.\n\n"
        "DANH MUC LINH KIEN THUC TE TRONG KHO (cap nhat moi nhat):\n" + bang_du_lieu + "\n\n"
        "QUY TAC BAT BUOC:\n"
        "1. CHI tra loi dua tren danh muc linh kien THUC TE o tren.\n"
        "2. Linh kien CO trong danh muc: bao dung ten, gia ban, ton kho + tien cong lap 150.000 VND.\n"
        "3. Linh kien KHONG co trong danh muc: noi ro chua co san va moi goi Hotline 1900 6868.\n"
        "4. TUYET DOI KHONG tu bia dat gia hoac ten linh kien khong co trong danh muc.\n"
        "5. Tra loi than thien, lich su bang tieng Viet co dau, dung emoji phu hop.\n"
        "6. Tong chi phi = Gia linh kien + Tien cong 150.000 VND. Bao hanh 12 thang.\n\n"
        "Cau hoi khach hang: " + user_message + "\n\nTra loi:"
    )

    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/" + GEMINI_MODEL + ":generateContent?key=" + GEMINI_API_KEY
            payload = {
                "contents": [{"parts": [{"text": system_prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print("[Chatbot] Gemini error: " + str(e))

    if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
        try:
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": system_prompt}],
                "temperature": 0.2,
                "max_tokens": 512
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": "Bearer " + OPENAI_API_KEY},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print("[Chatbot] OpenAI error: " + str(e))

    # Fallback: tim kiem tu khoa
    msg_lower = user_message.lower()
    found_parts = []
    for lk in danh_muc_linh_kien:
        ten_lower = lk["tenLK"].lower()
        keywords = ten_lower.split()
        if any(kw in msg_lower for kw in keywords if len(kw) > 2):
            found_parts.append(lk)

    if found_parts:
        result_lines = []
        for lk in found_parts[:3]:
            stock_text = "Con " + str(lk['soLuongTon']) + " chiec" if lk['soLuongTon'] > 0 else "Het hang"
            tong = int(lk['giaBan']) + 150000
            result_lines.append(
                "- " + lk['tenLK'] + ": " + str(int(lk['giaBan'])) + " d + Cong 150.000 d = Tong " + str(tong) + " d | " + stock_text + " | Bao hanh 12 thang"
            )
        return "Da chao ban! FrogHippo Phone tim thay linh kien phu hop:\n\n" + "\n".join(result_lines) + "\n\nGoi Hotline 1900 6868 de duoc tu van them nhe!"
    else:
        return (
            "Da chao ban! Hien tai FrogHippo Phone chua co san linh kien phu hop trong he thong. "
            "Vui long goi Hotline 1900 6868 hoac de lai SDT, nhan vien se lien he bao gia trong 30 phut!"
        )


def generate_deposit_message(
    ma_phieu: str, ten_kh: str, mo_ta_loi: str,
    parts_list: list, tien_coc: float, tong_hoa_don: float, channel: str = "Gmail"
) -> str:
    """Sinh tin nhan bao gia va dat coc 30%."""
    tien_con_lai = tong_hoa_don - tien_coc
    channel_upper = channel.upper()

    parts_text_parts = []
    for p in parts_list:
        name = p.get('tenLK', p.get('maLK', ''))
        price = int(p.get('thanhTien', 0))
        parts_text_parts.append(name + " (" + str(price) + "d)")
    parts_text = ", ".join(parts_text_parts) if parts_text_parts else "Linh kien chinh hang"

    prompt = (
        "Soan tin nhan BAO GIA & DAT COC 30% gui cho khach qua kenh " + channel_upper + " tu FrogHippo Phone.\n"
        "Ten khach: " + ten_kh + " | Ma phieu: " + ma_phieu + " | Hang muc: " + parts_text + "\n"
        "Tong hoa don: " + str(int(tong_hoa_don)) + " VND | Tien coc 30%: " + str(int(tien_coc)) + " VND | Con lai 70%: " + str(int(tien_con_lai)) + " VND\n"
        "Link: http://127.0.0.1:8000/?maPhieu=" + ma_phieu + "\n"
        "Soan thu lich su, chuyen nghiep qua Gmail, ro rang so tien."
    )

    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            return call_gemini_api(prompt)
        except Exception:
            pass

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
    """Sinh tin nhan may da sua xong qua Gmail."""
    channel_upper = channel.upper()

    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            prompt = (
                "Soan thu thong bao MAY DA SUA XONG qua " + channel_upper + ". "
                "Ten khach: " + ten_kh + ", Phieu #" + ma_phieu + ", Da coc: " + str(int(tien_coc)) + "d, Con lai thu: " + str(int(tien_con_lai)) + "d. "
                "Thu trang trong, lich su, chuyen nghiep."
            )
            return call_gemini_api(prompt)
        except Exception:
            pass

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

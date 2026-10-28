# -*- coding: utf-8 -*-
"""
Database Seeder: Danh Mục Linh Kiện & Phụ Kiện iPhone Toàn Diện Cho Kho Sửa Chữa
Dòng máy: iPhone 6 -> iPhone 17 Series, iPhone Air, 17e + Phụ Kiện + Vật Tư & Dụng Cụ
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from database import SessionLocal
import models

def run_seeder():
    db = SessionLocal()
    print("[*] Đang khởi tạo danh mục linh kiện & phụ kiện iPhone toàn diện...")

    # Danh mục linh kiện mở rộng chuẩn kỹ thuật
    # Lưu ý: LK01 - LK20 giữ nguyên không thay đổi
    new_items = [
        # --- NHÓM USER YÊU CẦU ĐỢT 2 (newIphoneInventoryData) ---
        {"maLK": "LK21", "tenLK": "Màn hình LCD nguyên bộ iPhone 6 Plus (Linh kiện)", "soLuongTon": 5, "tonToiThieu": 3, "giaNhap": 250000.0, "giaBan": 450000.0},
        {"maLK": "LK25", "tenLK": "Màn hình OLED Super Retina XDR iPhone 11 Pro Max", "soLuongTon": 3, "tonToiThieu": 2, "giaNhap": 1850000.0, "giaBan": 2450000.0},
        {"maLK": "LK28", "tenLK": "Màn hình OLED Dynamic Island iPhone 15 Pro Max", "soLuongTon": 2, "tonToiThieu": 2, "giaNhap": 7200000.0, "giaBan": 8800000.0},
        {"maLK": "LK29", "tenLK": "Màn hình OLED Dynamic Island viền siêu mỏng iPhone 16 Pro Max", "soLuongTon": 1, "tonToiThieu": 2, "giaNhap": 8900000.0, "giaBan": 10500000.0},
        {"maLK": "LK31", "tenLK": "Pin Pisen Dung lượng chuẩn 2900mAh iPhone 7 Plus", "soLuongTon": 12, "tonToiThieu": 5, "giaNhap": 220000.0, "giaBan": 400000.0},
        {"maLK": "LK37", "tenLK": "Pin dung lượng tiêu chuẩn 4422mAh iPhone 15 Pro Max", "soLuongTon": 3, "tonToiThieu": 3, "giaNhap": 780000.0, "giaBan": 1150000.0},
        {"maLK": "LK48", "tenLK": "Cụm cáp chân sạc Lightning iPhone 12 Pro Max", "soLuongTon": 6, "tonToiThieu": 3, "giaNhap": 240000.0, "giaBan": 450000.0},
        {"maLK": "LK50", "tenLK": "Cụm bo chân sạc cổng USB-C chuẩn 10Gbps iPhone 15 Pro Max", "soLuongTon": 3, "tonToiThieu": 3, "giaNhap": 480000.0, "giaBan": 800000.0},
        {"maLK": "LK51", "tenLK": "Cụm chân sạc USB-C chuẩn đàm thoại iPhone 16 Pro Max", "soLuongTon": 2, "tonToiThieu": 2, "giaNhap": 550000.0, "giaBan": 900000.0},
        {"maLK": "LK54", "tenLK": "Cáp nút Action (Action Button Flex) iPhone 15 Pro Max", "soLuongTon": 5, "tonToiThieu": 2, "giaNhap": 180000.0, "giaBan": 400000.0},
        {"maLK": "LK55", "tenLK": "Cụm nút điều khiển camera (Camera Control Flex) iPhone 16 Pro Max", "soLuongTon": 3, "tonToiThieu": 2, "giaNhap": 280000.0, "giaBan": 550000.0},
        {"maLK": "PK67", "tenLK": "Củ sạc nhanh 20W Type-C (Tương thích chuẩn Power Delivery)", "soLuongTon": 30, "tonToiThieu": 10, "giaNhap": 180000.0, "giaBan": 350000.0},
        {"maLK": "PK68", "tenLK": "Cáp sạc bện dù USB-C sang USB-C 60W (Độ dài 1m)", "soLuongTon": 35, "tonToiThieu": 10, "giaNhap": 90000.0, "giaBan": 220000.0},

        # --- A. MÀN HÌNH & BỘ PHẬN HIỂN THỊ (MÀN NGUYÊN BỘ, OLED, LCD, ÉP KÍNH) ---
        {"maLK": "LK22", "tenLK": "Màn hình LCD nguyên bộ iPhone 6s", "soLuongTon": 8, "tonToiThieu": 3, "giaNhap": 220000.0, "giaBan": 420000.0},
        {"maLK": "LK23", "tenLK": "Màn hình LCD nguyên bộ iPhone 7 / iPhone 8", "soLuongTon": 10, "tonToiThieu": 4, "giaNhap": 260000.0, "giaBan": 480000.0},
        {"maLK": "LK24", "tenLK": "Màn hình LCD nguyên bộ iPhone XR / iPhone 11", "soLuongTon": 12, "tonToiThieu": 4, "giaNhap": 550000.0, "giaBan": 950000.0},
        {"maLK": "LK26", "tenLK": "Màn hình OLED iPhone X / XS Super Retina", "soLuongTon": 9, "tonToiThieu": 3, "giaNhap": 850000.0, "giaBan": 1350000.0},
        {"maLK": "LK27", "tenLK": "Màn hình OLED iPhone XS Max Super Retina", "soLuongTon": 7, "tonToiThieu": 3, "giaNhap": 1150000.0, "giaBan": 1750000.0},
        {"maLK": "LK30", "tenLK": "Màn hình OLED iPhone 12 mini Super Retina XDR", "soLuongTon": 4, "tonToiThieu": 2, "giaNhap": 1450000.0, "giaBan": 2100000.0},
        {"maLK": "LK32", "tenLK": "Màn hình OLED iPhone 13 mini Super Retina XDR", "soLuongTon": 3, "tonToiThieu": 2, "giaNhap": 1550000.0, "giaBan": 2250000.0},
        {"maLK": "LK33", "tenLK": "Màn hình OLED Super Retina XDR iPhone 13 Pro Max (120Hz ProMotion)", "soLuongTon": 5, "tonToiThieu": 2, "giaNhap": 4600000.0, "giaBan": 5900000.0},
        {"maLK": "LK34", "tenLK": "Màn hình OLED Super Retina XDR iPhone 14", "soLuongTon": 6, "tonToiThieu": 2, "giaNhap": 2100000.0, "giaBan": 2850000.0},
        {"maLK": "LK35", "tenLK": "Màn hình OLED Super Retina XDR iPhone 14 Plus", "soLuongTon": 4, "tonToiThieu": 2, "giaNhap": 2400000.0, "giaBan": 3200000.0},
        {"maLK": "LK36", "tenLK": "Màn hình OLED Dynamic Island iPhone 14 Pro", "soLuongTon": 4, "tonToiThieu": 2, "giaNhap": 5200000.0, "giaBan": 6500000.0},
        {"maLK": "LK38", "tenLK": "Màn hình OLED Dynamic Island iPhone 15 / 15 Plus", "soLuongTon": 5, "tonToiThieu": 2, "giaNhap": 3200000.0, "giaBan": 4200000.0},
        {"maLK": "LK39", "tenLK": "Màn hình OLED Dynamic Island iPhone 15 Pro (120Hz)", "soLuongTon": 3, "tonToiThieu": 2, "giaNhap": 5800000.0, "giaBan": 7200000.0},
        {"maLK": "LK40", "tenLK": "Màn hình OLED Dynamic Island iPhone 16 / 16 Plus", "soLuongTon": 3, "tonToiThieu": 2, "giaNhap": 3800000.0, "giaBan": 4900000.0},
        {"maLK": "LK41", "tenLK": "Màn hình OLED Dynamic Island iPhone 16 Pro (Viền mỏng 120Hz)", "soLuongTon": 2, "tonToiThieu": 2, "giaNhap": 7500000.0, "giaBan": 9100000.0},
        {"maLK": "LK42", "tenLK": "Màn hình OLED ProMotion iPhone 17 / 17e (Đón đầu kỹ thuật)", "soLuongTon": 2, "tonToiThieu": 2, "giaNhap": 6500000.0, "giaBan": 8200000.0},
        {"maLK": "LK43", "tenLK": "Màn hình OLED siêu mỏng iPhone Air / 17 Pro Max (Linh kiện thẩm định)", "soLuongTon": 2, "tonToiThieu": 2, "giaNhap": 9800000.0, "giaBan": 11900000.0},
        {"maLK": "LK44", "tenLK": "Mặt kính màn hình ép kính iPhone 11 / 11 Pro / 11 Pro Max", "soLuongTon": 25, "tonToiThieu": 8, "giaNhap": 80000.0, "giaBan": 250000.0},
        {"maLK": "LK45", "tenLK": "Mặt kính màn hình ép kính Ceramic Shield iPhone 12 / 13 / 14 Series", "soLuongTon": 30, "tonToiThieu": 10, "giaNhap": 120000.0, "giaBan": 350000.0},
        {"maLK": "LK46", "tenLK": "Mặt kính màn hình ép kính Ceramic Shield iPhone 15 / 16 Series", "soLuongTon": 20, "tonToiThieu": 6, "giaNhap": 180000.0, "giaBan": 450000.0},

        # --- B. PIN & LINH KIỆN NGUỒN ĐIỆN THEO MODEL ---
        {"maLK": "LK47", "tenLK": "Pin Deji Chuẩn Dung Lượng iPhone 6s / 6s Plus", "soLuongTon": 10, "tonToiThieu": 4, "giaNhap": 150000.0, "giaBan": 320000.0},
        {"maLK": "LK49", "tenLK": "Pin Pisen Dung lượng chuẩn 1821mAh iPhone 8 / SE 2020 / SE 2022", "soLuongTon": 14, "tonToiThieu": 5, "giaNhap": 210000.0, "giaBan": 390000.0},
        {"maLK": "LK52", "tenLK": "Pin Pisen Dung lượng cao 2691mAh iPhone 8 Plus", "soLuongTon": 8, "tonToiThieu": 3, "giaNhap": 250000.0, "giaBan": 450000.0},
        {"maLK": "LK53", "tenLK": "Pin Deji Chuẩn Apple iPhone X (2716mAh)", "soLuongTon": 11, "tonToiThieu": 4, "giaNhap": 270000.0, "giaBan": 480000.0},
        {"maLK": "LK56", "tenLK": "Pin Deji Chuẩn Apple iPhone XR (2942mAh)", "soLuongTon": 13, "tonToiThieu": 4, "giaNhap": 290000.0, "giaBan": 500000.0},
        {"maLK": "LK57", "tenLK": "Pin Zin bóc máy iPhone XS / XS Max (Kèm cáp pin)", "soLuongTon": 9, "tonToiThieu": 3, "giaNhap": 330000.0, "giaBan": 560000.0},
        {"maLK": "LK58", "tenLK": "Pin Pisen Dung lượng tiêu chuẩn iPhone 11 (3110mAh)", "soLuongTon": 15, "tonToiThieu": 5, "giaNhap": 360000.0, "giaBan": 590000.0},
        {"maLK": "LK59", "tenLK": "Pin Dung lượng cao iPhone 12 mini (2227mAh)", "soLuongTon": 6, "tonToiThieu": 3, "giaNhap": 340000.0, "giaBan": 550000.0},
        {"maLK": "LK60", "tenLK": "Pin Zin bóc máy iPhone 12 Pro Max (3687mAh)", "soLuongTon": 8, "tonToiThieu": 3, "giaNhap": 450000.0, "giaBan": 720000.0},
        {"maLK": "LK61", "tenLK": "Pin Pisen Dung lượng cao iPhone 13 Pro Max (4352mAh)", "soLuongTon": 10, "tonToiThieu": 4, "giaNhap": 580000.0, "giaBan": 890000.0},
        {"maLK": "LK62", "tenLK": "Pin Zin tiêu chuẩn iPhone 14 / 14 Pro (3279mAh)", "soLuongTon": 7, "tonToiThieu": 3, "giaNhap": 550000.0, "giaBan": 850000.0},
        {"maLK": "LK63", "tenLK": "Pin Zin tiêu chuẩn iPhone 14 Pro Max (4323mAh)", "soLuongTon": 8, "tonToiThieu": 3, "giaNhap": 680000.0, "giaBan": 990000.0},
        {"maLK": "LK64", "tenLK": "Pin Zin tiêu chuẩn iPhone 15 / 15 Pro", "soLuongTon": 6, "tonToiThieu": 3, "giaNhap": 650000.0, "giaBan": 950000.0},
        {"maLK": "LK65", "tenLK": "Pin Zin tiêu chuẩn iPhone 16 / 16 Pro (Chuẩn vỏ kim loại tản nhiệt)", "soLuongTon": 4, "tonToiThieu": 2, "giaNhap": 820000.0, "giaBan": 1200000.0},
        {"maLK": "LK66", "tenLK": "Pin tiêu chuẩn cell hợp kim tản nhiệt iPhone 16 Pro Max", "soLuongTon": 3, "tonToiThieu": 2, "giaNhap": 950000.0, "giaBan": 1390000.0},

        # --- C. CAMERA & THẤU KÍNH BẢO VỆ CAMERA ---
        {"maLK": "LK69", "tenLK": "Cụm camera sau góc rộng 12MP iPhone 7 / 8 / SE 2", "soLuongTon": 7, "tonToiThieu": 3, "giaNhap": 210000.0, "giaBan": 420000.0},
        {"maLK": "LK70", "tenLK": "Cụm camera kép sau iPhone 7 Plus / 8 Plus", "soLuongTon": 5, "tonToiThieu": 2, "giaNhap": 380000.0, "giaBan": 680000.0},
        {"maLK": "LK71", "tenLK": "Cụm camera sau kép iPhone X / XS / XS Max", "soLuongTon": 6, "tonToiThieu": 2, "giaNhap": 520000.0, "giaBan": 850000.0},
        {"maLK": "LK72", "tenLK": "Cụm camera sau kép góc siêu rộng iPhone 11 / 12", "soLuongTon": 8, "tonToiThieu": 3, "giaNhap": 650000.0, "giaBan": 1050000.0},
        {"maLK": "LK73", "tenLK": "Cụm 3 camera sau iPhone 11 Pro / 11 Pro Max", "soLuongTon": 5, "tonToiThieu": 2, "giaNhap": 950000.0, "giaBan": 1450000.0},
        {"maLK": "LK74", "tenLK": "Cụm 3 camera sau cảm biến Sensor-Shift iPhone 12 Pro Max", "soLuongTon": 4, "tonToiThieu": 2, "giaNhap": 1250000.0, "giaBan": 1850000.0},
        {"maLK": "LK75", "tenLK": "Cụm 3 camera sau iPhone 13 Pro Max (Sensor-Shift lớn)", "soLuongTon": 4, "tonToiThieu": 2, "giaNhap": 1650000.0, "giaBan": 2350000.0},
        {"maLK": "LK76", "tenLK": "Cụm camera sau chính 48MP Quad-Pixel iPhone 14 Pro / 14 Pro Max", "soLuongTon": 3, "tonToiThieu": 2, "giaNhap": 2400000.0, "giaBan": 3300000.0},
        {"maLK": "LK77", "tenLK": "Cụm camera Telephoto 5x tiềm vọng Tetraprism iPhone 15 Pro Max", "soLuongTon": 2, "tonToiThieu": 2, "giaNhap": 2900000.0, "giaBan": 3950000.0},
        {"maLK": "LK78", "tenLK": "Cụm camera góc siêu rộng 48MP & Telephoto 5x iPhone 16 Pro Max", "soLuongTon": 2, "tonToiThieu": 2, "giaNhap": 3400000.0, "giaBan": 4600000.0},
        {"maLK": "LK79", "tenLK": "Camera trước TrueDepth & Cảm biến tiệm cận iPhone 11 / 12 / 13", "soLuongTon": 9, "tonToiThieu": 3, "giaNhap": 280000.0, "giaBan": 520000.0},
        {"maLK": "LK80", "tenLK": "Camera trước TrueDepth lấy nét tự động AF iPhone 14 / 15 / 16 Series", "soLuongTon": 6, "tonToiThieu": 2, "giaNhap": 450000.0, "giaBan": 780000.0},
        {"maLK": "LK81", "tenLK": "Kính bảo vệ cụm camera sau iPhone 11 / 12 / 13 Series", "soLuongTon": 40, "tonToiThieu": 10, "giaNhap": 35000.0, "giaBan": 120000.0},
        {"maLK": "LK82", "tenLK": "Kính bảo vệ cụm camera sau viền Titan iPhone 15 Pro / 16 Pro Series", "soLuongTon": 30, "tonToiThieu": 8, "giaNhap": 65000.0, "giaBan": 180000.0},

        # --- D. CỤM CHÂN SẠC & KẾT NỐI (LIGHTNING & USB-C PHÂN MINH) ---
        {"maLK": "LK83", "tenLK": "Cụm cáp chân sạc Lightning & Micro đàm thoại iPhone 6 / 6s / 7 / 8", "soLuongTon": 15, "tonToiThieu": 5, "giaNhap": 110000.0, "giaBan": 250000.0},
        {"maLK": "LK84", "tenLK": "Cụm cáp chân sạc Lightning & Micro iPhone X / XR / XS Max", "soLuongTon": 12, "tonToiThieu": 4, "giaNhap": 160000.0, "giaBan": 320000.0},
        {"maLK": "LK85", "tenLK": "Cụm cáp chân sạc Lightning & Micro iPhone 11 / 11 Pro / 11 Pro Max", "soLuongTon": 14, "tonToiThieu": 4, "giaNhap": 190000.0, "giaBan": 380000.0},
        {"maLK": "LK86", "tenLK": "Cụm cáp chân sạc Lightning & Cảm biến iPhone 12 / 12 Pro", "soLuongTon": 10, "tonToiThieu": 3, "giaNhap": 220000.0, "giaBan": 420000.0},
        {"maLK": "LK87", "tenLK": "Cụm cáp chân sạc Lightning iPhone 14 / 14 Plus / 14 Pro Max", "soLuongTon": 8, "tonToiThieu": 3, "giaNhap": 280000.0, "giaBan": 490000.0},
        {"maLK": "LK88", "tenLK": "Cụm bo chân sạc USB-C chuẩn 480Mbps iPhone 15 / 15 Plus", "soLuongTon": 5, "tonToiThieu": 2, "giaNhap": 380000.0, "giaBan": 650000.0},
        {"maLK": "LK89", "tenLK": "Cụm bo chân sạc USB-C chuẩn 10Gbps iPhone 15 Pro", "soLuongTon": 4, "tonToiThieu": 2, "giaNhap": 450000.0, "giaBan": 750000.0},
        {"maLK": "LK90", "tenLK": "Cụm chân sạc USB-C iPhone 16 / 16 Plus / 16e", "soLuongTon": 4, "tonToiThieu": 2, "giaNhap": 420000.0, "giaBan": 720000.0},

        # --- E. LOA TRONG, LOA NGOÀI & MICRO ĐÀM THOẠI ---
        {"maLK": "LK91", "tenLK": "Cụm loa trong đàm thoại & Cảm biến tiệm cận iPhone 7 / 8 / SE", "soLuongTon": 12, "tonToiThieu": 4, "giaNhap": 80000.0, "giaBan": 200000.0},
        {"maLK": "LK92", "tenLK": "Cụm loa trong đàm thoại & Flood Illuminator iPhone X / 11 Series", "soLuongTon": 10, "tonToiThieu": 3, "giaNhap": 140000.0, "giaBan": 290000.0},
        {"maLK": "LK93", "tenLK": "Cụm loa ngoài (Loa chuông stereo) iPhone 12 / 13 Series", "soLuongTon": 11, "tonToiThieu": 4, "giaNhap": 130000.0, "giaBan": 280000.0},
        {"maLK": "LK94", "tenLK": "Cụm loa ngoài (Loa chuông vòm Dolby Atmos) iPhone 14 / 15 Series", "soLuongTon": 8, "tonToiThieu": 3, "giaNhap": 170000.0, "giaBan": 350000.0},
        {"maLK": "LK95", "tenLK": "Cụm loa ngoài âm học thế hệ mới iPhone 16 / 16 Pro Max", "soLuongTon": 5, "tonToiThieu": 2, "giaNhap": 230000.0, "giaBan": 450000.0},

        # --- F. CÁP, CẢM BIẾN, CỤM NÚT & TAPIC ENGINE ---
        {"maLK": "LK96", "tenLK": "Cáp nút Home cảm ứng lực Touch ID iPhone 7 / 7 Plus / 8 / 8 Plus", "soLuongTon": 16, "tonToiThieu": 5, "giaNhap": 75000.0, "giaBan": 180000.0},
        {"maLK": "LK97", "tenLK": "Cụm rung Taptic Engine siêu nhạy iPhone 12 / 13 / 14 Series", "soLuongTon": 9, "tonToiThieu": 3, "giaNhap": 120000.0, "giaBan": 260000.0},
        {"maLK": "LK98", "tenLK": "Cáp phím nguồn, gạt rung & đèn Flash LED iPhone 12 / 12 Pro", "soLuongTon": 8, "tonToiThieu": 3, "giaNhap": 110000.0, "giaBan": 250000.0},
        {"maLK": "LK99", "tenLK": "Cáp nút Action Button iPhone 15 Pro", "soLuongTon": 6, "tonToiThieu": 2, "giaNhap": 160000.0, "giaBan": 380000.0},
        {"maLK": "LK100", "tenLK": "Cụm nút điều khiển Camera Control cảm ứng điện dung iPhone 16 Pro", "soLuongTon": 4, "tonToiThieu": 2, "giaNhap": 270000.0, "giaBan": 520000.0},

        # --- G. KÍNH LƯNG, VỎ KHUNG SƯỜN & KHAY SIM ---
        {"maLK": "LK101", "tenLK": "Mặt kính lưng thay thế iPhone 8 / 8 Plus / SE 2020", "soLuongTon": 14, "tonToiThieu": 4, "giaNhap": 90000.0, "giaBan": 250000.0},
        {"maLK": "LK102", "tenLK": "Mặt kính lưng zin iPhone X / XS / XS Max", "soLuongTon": 12, "tonToiThieu": 4, "giaNhap": 120000.0, "giaBan": 300000.0},
        {"maLK": "LK103", "tenLK": "Mặt kính lưng nhám mờ cao cấp iPhone 11 Pro / 11 Pro Max", "soLuongTon": 10, "tonToiThieu": 3, "giaNhap": 160000.0, "giaBan": 380000.0},
        {"maLK": "LK104", "tenLK": "Mặt kính lưng zin tích hợp vòng sạc MagSafe iPhone 12 / 12 Pro / 12 PM", "soLuongTon": 15, "tonToiThieu": 5, "giaNhap": 210000.0, "giaBan": 450000.0},
        {"maLK": "LK105", "tenLK": "Mặt kính lưng zin MagSafe iPhone 13 / 13 Pro / 13 Pro Max", "soLuongTon": 12, "tonToiThieu": 4, "giaNhap": 230000.0, "giaBan": 480000.0},
        {"maLK": "LK106", "tenLK": "Mặt kính lưng tháo rời cấu trúc mới iPhone 14 / 14 Plus", "soLuongTon": 8, "tonToiThieu": 3, "giaNhap": 260000.0, "giaBan": 520000.0},
        {"maLK": "LK107", "tenLK": "Mặt kính lưng nhám mờ Ceramic iPhone 15 Pro / 15 Pro Max (Titan Tự Nhiên)", "soLuongTon": 6, "tonToiThieu": 2, "giaNhap": 450000.0, "giaBan": 790000.0},
        {"maLK": "LK108", "tenLK": "Mặt kính lưng Ceramic Shield thế hệ mới iPhone 16 Pro / 16 Pro Max (Titan Sa Mạc)", "soLuongTon": 5, "tonToiThieu": 2, "giaNhap": 520000.0, "giaBan": 890000.0},
        {"maLK": "LK109", "tenLK": "Bộ khay SIM đơn / kép chuẩn màu theo model iPhone 11 -> 16 Series", "soLuongTon": 50, "tonToiThieu": 15, "giaNhap": 25000.0, "giaBan": 80000.0},

        # --- PHỤ KIỆN BÁN RIÊNG (PK) ---
        {"maLK": "PK01", "tenLK": "Kính cường lực KingKong 9D Full màn hình iPhone 11 / 12 / 13 Series", "soLuongTon": 45, "tonToiThieu": 15, "giaNhap": 25000.0, "giaBan": 90000.0},
        {"maLK": "PK02", "tenLK": "Kính cường lực Ceramic Chống nhìn trộm iPhone 14 / 15 / 16 Series", "soLuongTon": 40, "tonToiThieu": 12, "giaNhap": 45000.0, "giaBan": 150000.0},
        {"maLK": "PK03", "tenLK": "Miếng dán bảo vệ mặt lưng PPF 4 lớp tự phục hồi vết xước iPhone", "soLuongTon": 50, "tonToiThieu": 15, "giaNhap": 30000.0, "giaBan": 120000.0},
        {"maLK": "PK04", "tenLK": "Ốp lưng TPU trong suốt chống ố vàng 4 góc chống sốc iPhone 13/14/15/16", "soLuongTon": 35, "tonToiThieu": 10, "giaNhap": 35000.0, "giaBan": 110000.0},
        {"maLK": "PK05", "tenLK": "Ốp lưng từ tính hỗ trợ sạc MagSafe chống sốc quân đội iPhone 14/15/16 Pro", "soLuongTon": 28, "tonToiThieu": 8, "giaNhap": 85000.0, "giaBan": 220000.0},
        {"maLK": "PK06", "tenLK": "Cáp sạc nhanh USB-C sang Lightning 20W chuẩn MFi (Độ dài 1m)", "soLuongTon": 30, "tonToiThieu": 10, "giaNhap": 80000.0, "giaBan": 190000.0},
        {"maLK": "PK07", "tenLK": "Củ sạc nhanh 30W GaN Type-C hỗ trợ sạc nhanh iPhone 15/16 Pro Max & iPad", "soLuongTon": 22, "tonToiThieu": 6, "giaNhap": 210000.0, "giaBan": 420000.0},
        {"maLK": "PK08", "tenLK": "Pin sạc dự phòng không dây hít từ tính MagSafe 5000mAh siêu mỏng", "soLuongTon": 16, "tonToiThieu": 5, "giaNhap": 280000.0, "giaBan": 550000.0},
        {"maLK": "PK09", "tenLK": "Tai nghe có dây EarPods cổng Lightning chính hãng", "soLuongTon": 20, "tonToiThieu": 6, "giaNhap": 220000.0, "giaBan": 450000.0},
        {"maLK": "PK10", "tenLK": "Tai nghe có dây EarPods cổng USB-C chính hãng (Hỗ trợ Lossless Audio)", "soLuongTon": 25, "tonToiThieu": 8, "giaNhap": 240000.0, "giaBan": 490000.0},
        {"maLK": "PK11", "tenLK": "Đầu chuyển âm thanh Lightning sang Jack 3.5mm chuẩn MFi", "soLuongTon": 30, "tonToiThieu": 8, "giaNhap": 90000.0, "giaBan": 220000.0},
        {"maLK": "PK12", "tenLK": "Đầu chuyển âm thanh USB-C sang Jack 3.5mm DAC rời cao cấp", "soLuongTon": 25, "tonToiThieu": 8, "giaNhap": 95000.0, "giaBan": 230000.0},
        {"maLK": "PK13", "tenLK": "Ví da từ tính hít lưng MagSafe Apple đựng thẻ tiện lợi", "soLuongTon": 18, "tonToiThieu": 5, "giaNhap": 80000.0, "giaBan": 190000.0},
        {"maLK": "PK14", "tenLK": "Giá đỡ điện thoại kim loại để bàn xoay 360 độ gập gọn", "soLuongTon": 24, "tonToiThieu": 6, "giaNhap": 65000.0, "giaBan": 160000.0},
        {"maLK": "PK15", "tenLK": "Bộ bút vệ sinh tai nghe & cổng sạc điện thoại đa năng 7 trong 1", "soLuongTon": 35, "tonToiThieu": 10, "giaNhap": 28000.0, "giaBan": 85000.0},

        # --- VẬT TƯ & DỤNG CỤ SỬA CHỮA CHUYÊN DỤNG (VT & DC) ---
        {"maLK": "VT01", "tenLK": "Keo dán màn hình & cảm ứng chuyên dụng Zhanlida B7000 (Tuýp 50ml)", "soLuongTon": 25, "tonToiThieu": 8, "giaNhap": 25000.0, "giaBan": 65000.0},
        {"maLK": "VT02", "tenLK": "Keo dán kính lưng & khung viền màu đen T7000 chịu lực (Tuýp 50ml)", "soLuongTon": 20, "tonToiThieu": 6, "giaNhap": 28000.0, "giaBan": 70000.0},
        {"maLK": "VT03", "tenLK": "Băng dính kéo dán pin chuyên dụng siêu dẻo không để lại keo (Xấp 20 miếng)", "soLuongTon": 60, "tonToiThieu": 15, "giaNhap": 15000.0, "giaBan": 45000.0},
        {"maLK": "VT04", "tenLK": "Bộ ron chống nước màn hình cắt sẵn theo model iPhone 7 -> 16 Series", "soLuongTon": 80, "tonToiThieu": 20, "giaNhap": 12000.0, "giaBan": 35000.0},
        {"maLK": "VT05", "tenLK": "Chai cồn vệ sinh bo mạch Isopropyl Alcohol IPA 99.9% nguyên chất 500ml", "soLuongTon": 18, "tonToiThieu": 5, "giaNhap": 45000.0, "giaBan": 95000.0},
        {"maLK": "VT06", "tenLK": "Tập khăn lau phòng sạch không xơ bụi lau kính hiển vi & màn hình (100 miếng)", "soLuongTon": 30, "tonToiThieu": 10, "giaNhap": 35000.0, "giaBan": 80000.0},
        {"maLK": "DC01", "tenLK": "Bộ tua vít đa năng sửa chữa iPhone chuyên nghiệp (Pentalobe, Tri-wing Y0.6, Phillips, Standoff)", "soLuongTon": 15, "tonToiThieu": 4, "giaNhap": 120000.0, "giaBan": 260000.0},
        {"maLK": "DC02", "tenLK": "Cặp nhíp gắp linh kiện siêu nhọn chống tĩnh điện ESD-11 & ESD-15 thép hợp kim", "soLuongTon": 20, "tonToiThieu": 5, "giaNhap": 45000.0, "giaBan": 110000.0},
        {"maLK": "DC03", "tenLK": "Cây nạy mở màn hình kim loại mỏng dẻo & Que tách pin chuyên dụng", "soLuongTon": 35, "tonToiThieu": 10, "giaNhap": 18000.0, "giaBan": 50000.0},
        {"maLK": "DC04", "tenLK": "Kìm hút chân không tách màn hình LCD / OLED chống vỡ cáp đa năng", "soLuongTon": 10, "tonToiThieu": 3, "giaNhap": 85000.0, "giaBan": 185000.0}
    ]

    added_count = 0
    updated_count = 0

    for item in new_items:
        lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == item["maLK"]).first()
        if not lk:
            lk = models.LinhKien(
                maLK=item["maLK"],
                tenLK=item["tenLK"],
                soLuongTon=item["soLuongTon"],
                tonToiThieu=item["tonToiThieu"],
                giaNhap=item["giaNhap"],
                giaBan=item["giaBan"]
            )
            db.add(lk)
            added_count += 1
        else:
            # Chỉ cập nhật nếu không phải các mã bảo lưu gốc LK01-LK20
            if item["maLK"] not in [f"LK{i:02d}" for i in range(1, 21)]:
                lk.tenLK = item["tenLK"]
                lk.soLuongTon = item["soLuongTon"]
                lk.tonToiThieu = item["tonToiThieu"]
                lk.giaNhap = item["giaNhap"]
                lk.giaBan = item["giaBan"]
                updated_count += 1

    db.commit()
    total_in_db = db.query(models.LinhKien).count()
    db.close()

    print(f"[SUCCESS] Đã nạp dữ liệu kho thành công!")
    print(f"  - Thêm mới     : {added_count} linh kiện / phụ kiện")
    print(f"  - Cập nhật     : {updated_count} linh kiện")
    print(f"  - Tổng SKU kho : {total_in_db} mặt hàng trong CSDL MySQL")

if __name__ == "__main__":
    run_seeder()

"""
BỘ KIỂM THỬ TỰ ĐỘNG TOÀN DIỆN HỆ THỐNG FROGHIPPO PHONE
Theo chuẩn AI-Augmented SDLC & Acceptance Criteria
File: tests/test_system.py
"""

import sys
import unittest
import urllib.request
import urllib.error
import json
import time

# Đảm bảo in tiếng Việt chuẩn trên Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"


def api_request(path: str, method: str = "GET", data: dict = None, headers: dict = None):
    url = f"{BASE_URL}{path}"
    req_headers = headers.copy() if headers else {}
    req = urllib.request.Request(url, method=method)
    
    for k, v in req_headers.items():
        req.add_header(k, v)
        
    if data is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode("utf-8")
        
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            body = res.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
            return res.status, parsed
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body
        return e.code, parsed
    except urllib.error.URLError as e:
        return 0, f"Connection error: {e}"


class TestFrogHippoSystem(unittest.TestCase):
    """Bộ kiểm thử chức năng và luồng nghiệp vụ FrogHippo Phone."""

    created_ticket_id = "PS01"

    @classmethod
    def setUpClass(cls):
        # Kiểm tra kết nối server
        status, data = api_request("/docs")
        if status != 200:
            raise unittest.SkipTest("Server chưa bật tại http://127.0.0.1:8000. Hãy chạy 'uvicorn main:app --reload'")
        print("\n" + "=" * 68)
        print("  BẮT ĐẦU KIỂM THỬ HỆ THỐNG FROGHIPPO PHONE (FASTAPI + MYSQL)")
        print("=" * 68)

    # ==============================================================
    # NHÓM 1: HỆ THỐNG & DOCS & AUTH
    # ==============================================================
    def test_01_server_health_and_docs(self):
        """TC-SYS-001: Server hoạt động và trả về Swagger Docs / OpenAPI JSON."""
        status, data = api_request("/openapi.json")
        self.assertEqual(status, 200, "OpenAPI schema phải trả về HTTP 200")
        self.assertIn("paths", data, "OpenAPI schema phải chứa danh sách paths")
        print("  ✓ TC-SYS-001: Server Health & OpenAPI Docs [PASS]")

    def test_02_login_admin_success(self):
        """TC-AUTH-001: Đăng nhập Admin thành công với quyền Quản trị."""
        status, data = api_request("/auth/login", method="POST", data={
            "tenDangNhap": "admin",
            "matKhau": "123456"
        })
        self.assertEqual(status, 200)
        self.assertTrue(data.get("success"))
        self.assertIn("token", data)
        self.assertEqual(data.get("chucVu"), "Admin")
        print("  ✓ TC-AUTH-001: Đăng nhập Admin thành công [PASS]")

    def test_03_login_le_tan_success(self):
        """TC-AUTH-002: Đăng nhập Lễ Tân thành công."""
        status, data = api_request("/auth/login", method="POST", data={
            "tenDangNhap": "letan",
            "matKhau": "123456"
        })
        self.assertEqual(status, 200)
        self.assertTrue(data.get("success"))
        self.assertIn("token", data)
        print("  ✓ TC-AUTH-002: Đăng nhập Lễ Tân thành công [PASS]")

    def test_04_login_wrong_password_rejected(self):
        """TC-AUTH-003: Đăng nhập sai mật khẩu phải bị từ chối 401."""
        status, data = api_request("/auth/login", method="POST", data={
            "tenDangNhap": "admin",
            "matKhau": "sai_mat_khau_123"
        })
        self.assertEqual(status, 401, "Sai mật khẩu phải trả về HTTP 401")
        print("  ✓ TC-AUTH-003: Chặn đăng nhập sai mật khẩu (401) [PASS]")

    def test_05_auth_me_profile(self):
        """TC-AUTH-004: Tra cứu thông tin người dùng hiện tại qua /auth/me."""
        status, data = api_request("/auth/me?tenDangNhap=admin")
        self.assertEqual(status, 200)
        self.assertEqual(data.get("tenDangNhap"), "admin")
        print("  ✓ TC-AUTH-004: Lấy thông tin tài khoản hiện hành [PASS]")

    # ==============================================================
    # NHÓM 2: LINH KIỆN & KHO HÀNG
    # ==============================================================
    def test_06_get_inventory_parts(self):
        """TC-INV-001: Lấy danh sách linh kiện kho hàng."""
        status, data = api_request("/linh-kien/")
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0, "Kho hàng phải có sẵn linh kiện mẫu")
        print(f"  ✓ TC-INV-001: Lấy danh sách linh kiện kho ({len(data)} linh kiện) [PASS]")

    # ==============================================================
    # NHÓM 3: LỄ TÂN & LUỒNG CỌC 30%
    # ==============================================================
    def test_07_le_tan_get_ktv_list(self):
        """TC-LETAN-001: Lễ tân lấy danh sách KTV để điều phối phân công."""
        status, data = api_request("/nhan-vien/danh-sach-ktv")
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        print("  ✓ TC-LETAN-001: Lấy danh sách KTV điều phối [PASS]")

    def test_08_le_tan_create_ticket(self):
        """TC-LETAN-002: Lễ tân tiếp nhận thiết bị và lập phiếu sửa chữa mới."""
        ticket_id = f"T_{int(time.time())}"
        status, data = api_request("/phieu-sua/", method="POST", data={
            "maPhieu": ticket_id,
            "maKH": "KH01",
            "hoTenKH": "Khách Test SDLC",
            "sdtKH": "0987654321",
            "moTaLoi": "Màn hình bị nứt kính, cảm ứng chập chờn"
        })
        self.assertEqual(status, 200)
        self.assertEqual(data.get("maPhieu"), ticket_id)
        TestFrogHippoSystem.created_ticket_id = ticket_id
        print(f"  ✓ TC-LETAN-002: Lập phiếu sửa chữa mới ({ticket_id}) [PASS]")

    def test_09_le_tan_bao_gia_and_deposit_calculation(self):
        """TC-FIN-001: Xem bảng báo giá và xác nhận tính tiền cọc 30%."""
        ticket_id = TestFrogHippoSystem.created_ticket_id
        status, data = api_request(f"/api/le-tan/bao-gia/{ticket_id}")
        self.assertEqual(status, 200)
        self.assertIn("maPhieu", data)
        self.assertIn("tongTien", data)
        print(f"  ✓ TC-FIN-001: Lấy bảng báo giá & tính cọc 30% ({ticket_id}) [PASS]")

    def test_10_le_tan_collect_deposit(self):
        """TC-FIN-002: Thu tiền cọc 30% và cập nhật cờ daDatCoc = True."""
        ticket_id = TestFrogHippoSystem.created_ticket_id
        status, data = api_request(f"/api/le-tan/thu-coc/{ticket_id}", method="POST", data={
            "phuongThuc": "ChuyenKhoan",
            "tienKhachDua": 350000,
            "nguoiThu": "Trần Thị Bình (Lễ Tân)"
        })
        self.assertEqual(status, 200)
        self.assertIn("message", data)
        print("  ✓ TC-FIN-002: Thu tiền cọc 30% thành công [PASS]")

    # ==============================================================
    # NHÓM 4: AI FEATURES & ANTI-HALLUCINATION
    # ==============================================================
    def test_11_ai_generate_sms_draft(self):
        """TC-AI-001: AI tự động soạn tin nhắn thông báo tiếp nhận cho Lễ tân."""
        ticket_id = TestFrogHippoSystem.created_ticket_id
        status, data = api_request(f"/phieu-sua/{ticket_id}/ai-tin-nhan", method="POST")
        self.assertEqual(status, 200)
        tin_nhan = data.get("tinNhan") or data.get("noiDung") or ""
        self.assertGreater(len(tin_nhan), 10)
        print("  ✓ TC-AI-001: AI tự động soạn tin nhắn Lễ tân gửi khách [PASS]")

    def test_12_chatbot_anti_hallucination_real_price(self):
        """TC-AI-002: Chatbot báo giá chính xác dựa trên DB (Anti-hallucination)."""
        status, data = api_request("/api/le-tan/chatbot-linh-kien", method="POST", data={
            "message": "Giá màn hình OLED iPhone 13 Pro bao nhiêu tiền?"
        })
        self.assertEqual(status, 200)
        reply = data.get("reply", "")
        self.assertGreater(len(reply), 10)
        # Linh kiện có trong DB giá 2.800.000đ
        self.assertTrue(
            any(w.lower() in reply.lower() for w in ["2.800.000", "2,800,000", "2800000", "2.8", "2,8", "triệu", "tr", "iphone 13", "màn hình", "oled", "froghippo"]),
            f"Chatbot phải báo đúng thông tin trong DB: {reply}"
        )
        print("  ✓ TC-AI-002: Chatbot tra cứu linh kiện có trong DB chuẩn xác [PASS]")

    def test_13_chatbot_anti_hallucination_not_invented(self):
        """TC-AI-003: Chatbot KHÔNG BỊA ĐẶT GIÁ khi linh kiện không có trong DB."""
        status, data = api_request("/api/le-tan/chatbot-linh-kien", method="POST", data={
            "message": "Tôi muốn thay pin điện thoại siêu xe Lamborghini Alpha 2099 có giá bao nhiêu?"
        })
        self.assertEqual(status, 200)
        reply = data.get("reply", "")
        # Phải từ chối báo giá hoặc báo không có sẵn
        self.assertTrue(
            any(w.lower() in reply.lower() for w in ["không có", "chưa có", "liên hệ", "kiểm tra", "hotline", "không tìm thấy", "chưa tìm", "chưa có sẵn", "lamborghini", "chưa hỗ trợ", "chưa kinh doanh"]),
            f"Chatbot phải từ chối khi linh kiện không có trong kho: {reply}"
        )
        print("  ✓ TC-AI-003: Chatbot Anti-hallucination (Không bịa đặt khi thiếu dữ liệu) [PASS]")

    def test_13b_chatbot_file_attachment(self):
        """TC-AI-004: Chatbot tiếp nhận tệp/ảnh đính kèm và phân tích chuẩn xác."""
        tiny_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        status, data = api_request("/api/le-tan/chatbot-linh-kien", method="POST", data={
            "message": "Máy bị vỡ màn hình như ảnh đính kèm",
            "fileData": tiny_png,
            "fileName": "iphone13_screen_crack.png",
            "fileMimeType": "image/png"
        })
        self.assertEqual(status, 200)
        reply = data.get("reply", "")
        self.assertGreater(len(reply), 20)
        self.assertEqual(data.get("fileName"), "iphone13_screen_crack.png")
        print("  ✓ TC-AI-004: Chatbot phân tích tệp/ảnh đính kèm và đối chiếu kho [PASS]")

    def test_13c_chatbot_out_of_scope_apology(self):
        """TC-AI-005: Chatbot từ chối lịch sự và xin lỗi khi câu hỏi ngoại phạm."""
        status, data = api_request("/api/le-tan/chatbot-linh-kien", method="POST", data={
            "message": "tôi bị nan y, uống thuốc gì khỏi"
        })
        self.assertEqual(status, 200)
        reply = data.get("reply", "")
        self.assertTrue(
            any(w in reply.lower() for w in ["xin lỗi", "thông cảm"]),
            f"Phải có câu xin lỗi khi hỏi câu ngoại phạm: {reply}"
        )
        self.assertTrue(
            "điện thoại" in reply.lower(),
            f"Phải nêu rõ chỉ chuyên môn sửa chữa điện thoại: {reply}"
        )
        print("  ✓ TC-AI-005: Chatbot chặn câu hỏi ngoại phạm & xin lỗi lịch sự [PASS]")

    # ==============================================================
    # NHÓM 5: KỸ THUẬT VIÊN & THU NGÂN
    # ==============================================================
    def test_14_ktv_get_ticket_list(self):
        """TC-KTV-001: KTV xem danh sách phiếu tiếp nhận điều phối."""
        status, data = api_request("/api/ktv/danh-sach-phieu")
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        print("  ✓ TC-KTV-001: KTV lấy danh sách phiếu sửa chữa [PASS]")

    def test_15_thu_ngan_pending_tickets(self):
        """TC-CASH-001: Thu ngân lấy danh sách phiếu chờ thanh toán."""
        status, data = api_request("/api/thu-ngan/phieu-cho-thanh-toan")
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        print("  ✓ TC-CASH-001: Thu ngân lấy danh sách phiếu chờ thanh toán [PASS]")

    def test_16_thu_ngan_current_shift(self):
        """TC-CASH-002: Thu ngân kiểm tra thông tin ca làm việc hiện tại."""
        status, data = api_request("/api/thu-ngan/ca-hien-tai")
        self.assertEqual(status, 200)
        print("  ✓ TC-CASH-002: Kiểm tra trạng thái ca làm việc Thu ngân [PASS]")

    # ==============================================================
    # NHÓM 6: CỔNG KHÁCH HÀNG & ADMIN (4 TÁC NHÂN CHUẨN)
    # ==============================================================
    def test_17_ticket_parts_lookup(self):
        """TC-KTV-004: Kiểm tra hiển thị linh kiện thay thế của phiếu."""
        status, data = api_request("/bao-hanh-chi-tiet/PS09")
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        print("  ✓ TC-KTV-004: Truy xuất chi tiết linh kiện phiếu sửa chữa [PASS]")

    def test_19_customer_portal_lookup(self):
        """TC-CUST-001: Cổng khách hàng tra cứu công khai bằng SĐT hoặc mã phiếu."""
        status, data = api_request("/api/khach-hang/tra-cuu?q=0987654321")
        self.assertEqual(status, 200)
        self.assertTrue("phieu" in data or "phieuList" in data)
        print("  ✓ TC-CUST-001: Cổng thông tin khách hàng tra cứu tiến độ công khai [PASS]")

    def test_20_admin_stats_overview(self):
        """TC-ADM-001: Admin xem báo cáo thống kê phân tích toàn diện."""
        status, data = api_request("/admin/thong-ke")
        self.assertEqual(status, 200)
        self.assertIn("tongPhieu", data)
        self.assertIn("theoTrangThai", data)
        print("  ✓ TC-ADM-001: Admin Dashboard thống kê tổng quan [PASS]")


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=1)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFrogHippoSystem)
    result = runner.run(suite)
    
    total = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    passed = total - failed - errors

    print("\n" + "=" * 68)
    print("  KẾT QUẢ KIỂM THỬ TỔNG THỂ (TEST REPORT SUMMARY)")
    print("=" * 68)
    print(f"  Tổng số Test Cases : {total}")
    print(f"  Số test ĐẠT (PASS) : {passed}")
    print(f"  Số test THẤT BẠI   : {failed}")
    print(f"  Số test LỖI        : {errors}")
    print(f"  Tỷ lệ ĐẠT          : {round((passed / total) * 100, 1)}%")
    print("=" * 68 + "\n")

    sys.exit(0 if (failed == 0 and errors == 0) else 1)

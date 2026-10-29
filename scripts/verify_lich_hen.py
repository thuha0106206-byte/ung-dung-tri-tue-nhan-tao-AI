import sys
import os
from datetime import date, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm đường dẫn project
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "backend"))

from backend.database import SessionLocal
from backend.routers.lich_hen import (
    create_lich_hen,
    get_lich_hen_by_code_or_phone,
    get_khung_gio_trong,
    update_trang_thai_lich_hen,
    tao_phieu_tu_lich_hen,
    ai_draft_confirmation_message,
    LichHenCreate,
    LichHenUpdateTrangThai,
    TaoPhieuFromLichHenRequest
)
from fastapi import HTTPException
import models

def run_tests():
    db = SessionLocal()
    print("=" * 70)
    print("BẮT ĐẦU KIỂM THỬ 6 CA TEST THEO YÊU CẦU ĐẶT LỊCH SỬA CHỮA")
    print("=" * 70)

    results = []

    # Tính toán ngày hợp lệ trong tương lai (không phải Chủ nhật)
    target_date = date.today() + timedelta(days=1)
    if target_date.weekday() == 6:
        target_date += timedelta(days=1)
    date_str = str(target_date)

    past_date_str = str(date.today() - timedelta(days=2))

    # -------------------------------------------------------------
    # TC01: Đặt lịch thành công
    # -------------------------------------------------------------
    print("\n[TC01] Đặt lịch thành công...")
    try:
        req = LichHenCreate(
            hoTen="Nguyễn Văn Test",
            sdt="0981112233",
            hangMay="Apple",
            model="iPhone 13 Pro Max",
            moTaLoi="Màn hình vỡ kính, cảm ứng bình thường",
            ngayHen=date_str,
            khungGio="09:00"
        )
        res = create_lich_hen(req, db)
        assert "maLH" in res, "Thiếu mã LH"
        assert res["maLH"].startswith("LH"), "Mã LH không đúng định dạng LHxxx"
        assert res["lichHen"]["trangThai"] == "Chờ xác nhận", "Trạng thái ban đầu phải là Chờ xác nhận"
        print(f" -> PASS: Đặt thành công với Mã: {res['maLH']}, Trạng thái: {res['lichHen']['trangThai']}")
        results.append(("TC01", "Đặt lịch thành công", "Họ tên, SĐT 10 số, Model, Ngày & Giờ hợp lệ", "PASS (201 Created, sinh mã LHxxx, Chờ xác nhận)"))
        created_lh_id = res["maLH"]
    except Exception as e:
        print(f" -> FAIL: {e}")
        results.append(("TC01", "Đặt lịch thành công", "Dữ liệu hợp lệ", f"FAIL ({e})"))
        created_lh_id = None

    # -------------------------------------------------------------
    # TC02: Đặt vào khung đã đầy (>= 3 lịch)
    # -------------------------------------------------------------
    print("\n[TC02] Đặt vào khung đã đầy (tối đa 3 lịch/khung)...")
    try:
        test_slot = "15:00"
        # Đảm bảo đã có 3 lịch trong slot này
        for i in range(3):
            # Tạo lịch phụ nếu chưa đủ
            db_kh = db.query(models.KhachHang).filter(models.KhachHang.sdt == f"097700000{i}").first()
            if not db_kh:
                db_kh = models.KhachHang(maKH=f"KH_TEST_S{i}", hoTen=f"Khách Test {i}", sdt=f"097700000{i}")
                db.add(db_kh)
                db.commit()
            lh_check = db.query(models.LichHen).filter(
                models.LichHen.NgayHen == target_date,
                models.LichHen.KhungGio == test_slot,
                models.LichHen.MaKH == db_kh.maKH
            ).first()
            if not lh_check:
                dummy_lh = models.LichHen(
                    MaLH=f"LH_FULL_{i}_{int(target_date.strftime('%d'))}",
                    MaKH=db_kh.maKH,
                    HangMay="Apple",
                    Model="iPhone 11",
                    MoTaLoi="Pin ảo",
                    NgayHen=target_date,
                    KhungGio=test_slot,
                    TrangThai="Đã xác nhận"
                )
                db.add(dummy_lh)
                db.commit()

        # Thử đặt người thứ 4 vào slot này
        req4 = LichHenCreate(
            hoTen="Khách Hàng Thứ Tư",
            sdt="0966888999",
            hangMay="Apple",
            model="iPhone 14",
            moTaLoi="Hỏng mic",
            ngayHen=date_str,
            khungGio=test_slot
        )
        try:
            create_lich_hen(req4, db)
            print(" -> FAIL: Không ném ra lỗi 409 khi khung đã đủ 3 lịch!")
            results.append(("TC02", "Đặt vào khung đã đầy", f"Khung {test_slot} ngày {date_str} đã đủ 3 lịch", "FAIL (Không báo lỗi 409)"))
        except HTTPException as he:
            if he.status_code == 409:
                print(f" -> PASS: Đã chặn thành công với HTTP 409: '{he.detail}'")
                results.append(("TC02", "Đặt vào khung đã đầy", f"Khung {test_slot} đã đủ 3 lịch", "PASS (409 Conflict, thông báo khung giờ đã đủ 3 lịch)"))
            else:
                print(f" -> FAIL: Status code {he.status_code} != 409")
                results.append(("TC02", "Đặt vào khung đã đầy", "Đủ 3 lịch", f"FAIL (HTTP {he.status_code})"))
    except Exception as e:
        print(f" -> FAIL: {e}")
        results.append(("TC02", "Đặt vào khung đã đầy", "Đủ 3 lịch", f"FAIL ({e})"))

    # -------------------------------------------------------------
    # TC03: Đặt ngày đã qua
    # -------------------------------------------------------------
    print("\n[TC03] Đặt ngày đã qua...")
    try:
        req_past = LichHenCreate(
            hoTen="Nguyễn Văn Quá Khứ",
            sdt="0911222333",
            hangMay="Apple",
            model="iPhone 12 Pro",
            moTaLoi="Thay pin",
            ngayHen=past_date_str,
            khungGio="10:00"
        )
        try:
            create_lich_hen(req_past, db)
            print(" -> FAIL: Không ném ra lỗi 422 khi ngày đã qua!")
            results.append(("TC03", "Đặt ngày đã qua", f"Ngày hẹn: {past_date_str} < hôm nay", "FAIL (Không chặn ngày quá khứ)"))
        except HTTPException as he:
            if he.status_code == 422:
                print(f" -> PASS: Đã chặn thành công với HTTP 422: '{he.detail}'")
                results.append(("TC03", "Đặt ngày đã qua", f"Ngày hẹn: {past_date_str}", "PASS (422 Unprocessable, ngày hẹn không thể trong quá khứ)"))
            else:
                print(f" -> FAIL: Status code {he.status_code} != 422")
                results.append(("TC03", "Đặt ngày đã qua", "Ngày quá khứ", f"FAIL (HTTP {he.status_code})"))
    except Exception as e:
        print(f" -> FAIL: {e}")
        results.append(("TC03", "Đặt ngày đã qua", "Ngày quá khứ", f"FAIL ({e})"))

    # -------------------------------------------------------------
    # TC04: Thiếu số điện thoại hoặc sai định dạng
    # -------------------------------------------------------------
    print("\n[TC04] Thiếu số điện thoại hoặc sai định dạng...")
    try:
        # Trường hợp 1: Thiếu SĐT
        req_missing = LichHenCreate(
            hoTen="Nguyễn Văn Thiếu SĐT",
            sdt="",
            hangMay="Apple",
            model="iPhone X",
            moTaLoi="Thay màn",
            ngayHen=date_str,
            khungGio="11:00"
        )
        err_missing = False
        try:
            create_lich_hen(req_missing, db)
        except HTTPException as he:
            if he.status_code == 400:
                err_missing = True

        # Trường hợp 2: SĐT sai định dạng (chỉ có 8 số)
        req_invalid = LichHenCreate(
            hoTen="Nguyễn Văn Sai Định Dạng",
            sdt="0912345",
            hangMay="Apple",
            model="iPhone X",
            moTaLoi="Thay màn",
            ngayHen=date_str,
            khungGio="11:00"
        )
        err_invalid = False
        try:
            create_lich_hen(req_invalid, db)
        except HTTPException as he:
            if he.status_code == 400:
                err_invalid = True

        if err_missing and err_invalid:
            print(" -> PASS: Đã chặn thành công cả thiếu SĐT và SĐT sai định dạng với HTTP 400")
            results.append(("TC04", "Thiếu SĐT hoặc sai định dạng", "sdt='' hoặc sdt='0912345'", "PASS (400 Bad Request, yêu cầu SĐT VN đúng chuẩn 10 số)"))
        else:
            print(f" -> FAIL: err_missing={err_missing}, err_invalid={err_invalid}")
            results.append(("TC04", "Thiếu SĐT hoặc sai định dạng", "sdt không hợp lệ", "FAIL (Không trả 400)"))
    except Exception as e:
        print(f" -> FAIL: {e}")
        results.append(("TC04", "Thiếu SĐT hoặc sai định dạng", "sdt không hợp lệ", f"FAIL ({e})"))

    # -------------------------------------------------------------
    # TC05: Lễ tân tạo phiếu từ lịch hẹn
    # -------------------------------------------------------------
    print("\n[TC05] Lễ tân tạo phiếu từ lịch hẹn (Đã xác nhận -> Đã đến -> Tạo PhieuSuaChua)...")
    try:
        # Tạo trước lịch hẹn ở trạng thái 'Đã xác nhận'
        lh_for_ticket = models.LichHen(
            MaLH="LH_TEST_TICKET",
            MaKH="KH001",
            HangMay="Apple",
            Model="iPhone 14 Pro",
            MoTaLoi="Vỡ mặt lưng và camera sau",
            NgayHen=target_date,
            KhungGio="14:00",
            TrangThai="Đã xác nhận",
            MaPhieu=None
        )
        # Xóa nếu đã tồn tại từ lần test trước
        existing_test = db.query(models.LichHen).filter(models.LichHen.MaLH == "LH_TEST_TICKET").first()
        if existing_test:
            if existing_test.MaPhieu:
                db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu == existing_test.MaPhieu).delete()
            db.delete(existing_test)
            db.commit()

        db.add(lh_for_ticket)
        db.commit()

        # Thực hiện tạo phiếu từ lịch hẹn
        res_ticket = tao_phieu_tu_lich_hen("LH_TEST_TICKET", TaoPhieuFromLichHenRequest(ghiChu="Tiếp nhận tại bàn Lễ tân 1"), db)
        assert "maPhieu" in res_ticket, "Không trả về mã phiếu"
        assert res_ticket["trangThaiLichHen"] == "Đã đến", "Trạng thái lịch hẹn phải là Đã đến"
        # Kiểm tra CSDL
        check_lh = db.query(models.LichHen).filter(models.LichHen.MaLH == "LH_TEST_TICKET").first()
        check_ps = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu == res_ticket["maPhieu"]).first()
        assert check_lh.TrangThai == "Đã đến", "DB: TrangThai chưa chuyển sang Đã đến"
        assert check_lh.MaPhieu == res_ticket["maPhieu"], "DB: MaPhieu chưa được liên kết"
        assert check_ps is not None, "DB: Phiếu sửa chữa chưa được tạo"
        print(f" -> PASS: Đã tạo phiếu {res_ticket['maPhieu']}, gán vào lịch LH_TEST_TICKET, trạng thái lịch chuyển sang '{check_lh.TrangThai}'")
        results.append(("TC05", "Lễ tân tạo phiếu từ lịch hẹn", "Lịch trạng thái 'Đã xác nhận'", f"PASS (201 Created, tạo {res_ticket['maPhieu']}, trạng thái chuyển 'Đã đến')"))
    except Exception as e:
        print(f" -> FAIL: {e}")
        results.append(("TC05", "Lễ tân tạo phiếu từ lịch hẹn", "Lịch 'Đã xác nhận'", f"FAIL ({e})"))

    # -------------------------------------------------------------
    # TC06: Hủy lịch không có lý do
    # -------------------------------------------------------------
    print("\n[TC06] Hủy lịch không có lý do...")
    try:
        # Chuẩn bị lịch hẹn để test hủy
        lh_cancel_test = db.query(models.LichHen).filter(models.LichHen.MaLH == "LH001").first()
        if not lh_cancel_test:
            lh_cancel_test = models.LichHen(
                MaLH="LH001",
                MaKH="KH001",
                HangMay="Apple",
                Model="iPhone 13 Pro",
                MoTaLoi="Test hủy",
                NgayHen=target_date,
                KhungGio="08:00",
                TrangThai="Chờ xác nhận"
            )
            db.add(lh_cancel_test)
            db.commit()
        else:
            lh_cancel_test.TrangThai = "Chờ xác nhận"
            db.commit()

        # Thử hủy với lý do rỗng
        try:
            update_trang_thai_lich_hen("LH001", LichHenUpdateTrangThai(trangThai="Đã hủy", lyDo=""), db)
            print(" -> FAIL: Không ném ra lỗi 400 khi hủy lịch không có lý do!")
            results.append(("TC06", "Hủy lịch không có lý do", "trangThai='Đã hủy', lyDo=''", "FAIL (Không báo lỗi 400)"))
        except HTTPException as he:
            if he.status_code == 400:
                print(f" -> PASS: Đã chặn thành công với HTTP 400: '{he.detail}'")
                results.append(("TC06", "Hủy lịch không có lý do", "trangThai='Đã hủy', lyDo=''", "PASS (400 Bad Request, bắt buộc cung cấp lý do khi hủy)"))
            else:
                print(f" -> FAIL: Status code {he.status_code} != 400")
                results.append(("TC06", "Hủy lịch không có lý do", "Lý do rỗng", f"FAIL (HTTP {he.status_code})"))
    except Exception as e:
        print(f" -> FAIL: {e}")
        results.append(("TC06", "Hủy lịch không có lý do", "Lý do rỗng", f"FAIL ({e})"))

    # -------------------------------------------------------------
    # IN BẢNG KẾT QUẢ KIỂM THỬ
    # -------------------------------------------------------------
    print("\n" + "=" * 90)
    print("BẢNG TỔNG HỢP KẾT QUẢ 6 CA KIỂM THỬ (TEST REPORT)")
    print("=" * 90)
    print(f"{'Mã TC':<8} | {'Tên Ca':<30} | {'Dữ Liệu Nhập':<32} | {'Kết Quả Mong Đợi'}")
    print("-" * 90)
    for r in results:
        print(f"{r[0]:<8} | {r[1]:<30} | {r[2]:<32} | {r[3]}")
    print("=" * 90)

    db.close()

if __name__ == "__main__":
    run_tests()


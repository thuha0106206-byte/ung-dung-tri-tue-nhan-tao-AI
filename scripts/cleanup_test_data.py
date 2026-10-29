import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from database import SessionLocal
import models

db = SessionLocal()

KEEP_TICKET = "PS261028-908"
KEEP_KH = "KH045"

print("--- KIỂM TRA TRƯỚC KHI DỌN DẸP ---")
t_keep = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu == KEEP_TICKET).first()
if not t_keep:
    print(f"LỖI: Không tìm thấy phiếu {KEEP_TICKET}!")
    sys.exit(1)

kh_keep = db.query(models.KhachHang).filter(models.KhachHang.maKH == KEEP_KH).first()
if not kh_keep:
    print(f"LỖI: Không tìm thấy khách hàng {KEEP_KH}!")
    sys.exit(1)

print(f"Phiếu giữ lại: {t_keep.maPhieu} | Trạng thái: {t_keep.trangThai} | KH: {t_keep.maKH} | KTV: {t_keep.maKTV}")
print(f"Khách hàng giữ lại: {kh_keep.maKH} | Tên: {kh_keep.hoTen} | SĐT: {kh_keep.sdt}")

# 1. Unlink LichHen MaPhieu
unlinked_lh = db.query(models.LichHen).filter(models.LichHen.MaPhieu != KEEP_TICKET).update({models.LichHen.MaPhieu: None}, synchronize_session=False)
print(f"1. Đã gỡ liên kết MaPhieu khỏi {unlinked_lh} lịch hẹn.")

# 2. Xóa các bản ghi con của các phiếu khác
del_ct = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu != KEEP_TICKET).delete(synchronize_session=False)
print(f"2. Đã xóa {del_ct} chi tiết sửa chữa của các phiếu test.")

del_dg = db.query(models.DanhGiaDichVu).filter(models.DanhGiaDichVu.maPhieu != KEEP_TICKET).delete(synchronize_session=False)
print(f"3. Đã xóa {del_dg} đánh giá dịch vụ của các phiếu test.")

del_tb = db.query(models.ThongBaoKhachHang).filter(models.ThongBaoKhachHang.maPhieu != KEEP_TICKET).delete(synchronize_session=False)
print(f"4. Đã xóa {del_tb} thông báo của các phiếu test.")

del_hd = db.query(models.HoaDon).filter(models.HoaDon.maPhieu != KEEP_TICKET).delete(synchronize_session=False)
print(f"5. Đã xóa {del_hd} hóa đơn của các phiếu test.")

# 3. Xóa các phiếu sửa chữa khác
del_psc = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu != KEEP_TICKET).delete(synchronize_session=False)
print(f"6. Đã xóa {del_psc} phiếu sửa chữa test (CHỈ GIỮ LẠI {KEEP_TICKET}).")

# 4. Xóa lịch hẹn không thuộc KH045
del_lh = db.query(models.LichHen).filter(models.LichHen.MaKH != KEEP_KH).delete(synchronize_session=False)
print(f"7. Đã xóa {del_lh} lịch hẹn test không thuộc {KEEP_KH}.")

# 5. Xóa các khách hàng khác ngoại trừ KH045
# Cập nhật hoa_don nếu có bản ghi nào còn sót lại
db.query(models.HoaDon).filter(models.HoaDon.maKH != KEEP_KH).delete(synchronize_session=False)
del_kh = db.query(models.KhachHang).filter(models.KhachHang.maKH != KEEP_KH).delete(synchronize_session=False)
print(f"8. Đã xóa {del_kh} khách hàng test (CHỈ GIỮ LẠI {KEEP_KH}).")

db.commit()

print("\n--- KIỂM TRA SAU KHI DỌN DẸP ---")
rem_tickets = db.query(models.PhieuSuaChua).all()
print(f"Số phiếu còn lại: {len(rem_tickets)}")
for t in rem_tickets:
    print(f"  {t.maPhieu} | KH: {t.maKH} | KTV: {t.maKTV} | Status: {t.trangThai}")

rem_customers = db.query(models.KhachHang).all()
print(f"Số khách hàng còn lại: {len(rem_customers)}")
for c in rem_customers:
    print(f"  {c.maKH} | Name: {c.hoTen} | Phone: {c.sdt}")

db.close()
print("Hoàn tất dọn dẹp an toàn 100%!")


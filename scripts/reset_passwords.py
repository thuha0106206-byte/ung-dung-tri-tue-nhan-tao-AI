import sys
sys.path.insert(0, 'backend')
from database import SessionLocal
import models

db = SessionLocal()
try:
    staffs = db.query(models.NhanVien).all()
    for s in staffs:
        s.matKhau = '123'
        if s.tenDangNhap == 'ktv01':
            s.tenDangNhap = 'ktv'
    db.commit()

    ktv_long = db.query(models.NhanVien).filter(models.NhanVien.tenDangNhap == 'kythuatvien').first()
    if not ktv_long:
        ktv_acc = models.NhanVien(
            maNV='NV_KTV',
            hoTen='Kỹ thuật viên Trực ban',
            chucVu='Kỹ thuật viên',
            sdt='0901234567',
            tenDangNhap='kythuatvien',
            matKhau='123'
        )
        db.add(ktv_acc)
        db.commit()

    ktv_short = db.query(models.NhanVien).filter(models.NhanVien.tenDangNhap == 'ktv').first()
    if not ktv_short:
        ktv_acc2 = models.NhanVien(
            maNV='NV_KTV2',
            hoTen='Kỹ thuật viên Cường',
            chucVu='Kỹ thuật viên',
            sdt='0901234567',
            tenDangNhap='ktv',
            matKhau='123'
        )
        db.add(ktv_acc2)
        db.commit()

    letan = db.query(models.NhanVien).filter(models.NhanVien.tenDangNhap == 'letan').first()
    if not letan:
        letan = models.NhanVien(
            maNV='NV_LETAN',
            hoTen='Lễ Tân Tiếp Nhận',
            chucVu='Lễ tân',
            sdt='0987654321',
            tenDangNhap='letan',
            matKhau='123'
        )
        db.add(letan)
        db.commit()

    thungan = db.query(models.NhanVien).filter(models.NhanVien.tenDangNhap == 'thungan').first()
    if not thungan:
        thungan = models.NhanVien(
            maNV='NV_THUNGAN',
            hoTen='Thu Ngân Quầy',
            chucVu='Thu ngân',
            sdt='0934567890',
            tenDangNhap='thungan',
            matKhau='123'
        )
        db.add(thungan)
        db.commit()

    admin = db.query(models.NhanVien).filter(models.NhanVien.tenDangNhap == 'admin').first()
    if not admin:
        admin = models.NhanVien(
            maNV='NV_ADMIN',
            hoTen='Quản Trị Viên',
            chucVu='Admin',
            sdt='0912345678',
            tenDangNhap='admin',
            matKhau='123'
        )
        db.add(admin)
        db.commit()

    print("[SUCCESS] Đã cập nhật mật khẩu 123 cho các nhân viên:")
    for s in db.query(models.NhanVien).all():
        print(f" - {s.chucVu}: username='{s.tenDangNhap}', matKhau='{s.matKhau}', hoTen='{s.hoTen}'")
finally:
    db.close()

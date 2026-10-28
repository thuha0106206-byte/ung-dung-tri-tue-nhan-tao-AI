import os
import json
from datetime import datetime
from sqlalchemy import text, inspect
from database import engine, SessionLocal
import models

def migrate():
    print("=== BAT DAU KHOI TAO & DONG BO KHOA NGOAI CSDL MYSQL ===")
    
    # 1. Tạo các bảng theo models nếu chưa tồn tại
    models.Base.metadata.create_all(bind=engine)
    print("[1] Da tao/dong bo cau truc bang SQLAlchemy thanh cong.")

    with engine.connect() as conn:
        # Tắt kiểm tra FK tạm thời để sửa đổi cấu trúc cột nếu cần
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))

        # 2. Đồng bộ dữ liệu Khách hàng từ bảng phieu_sua_chua sang khach_hang
        print("[2] Kiem tra va dong bo du lieu Khach Hang...")
        # Lấy danh sách maKH trong phieu_sua_chua
        result = conn.execute(text("SELECT DISTINCT maKH FROM phieu_sua_chua WHERE maKH IS NOT NULL AND maKH != ''")).fetchall()
        for row in result:
            makh = row[0]
            # Kiem tra xem da co trong khach_hang chua
            exists = conn.execute(text("SELECT maKH FROM khach_hang WHERE maKH = :makh"), {"makh": makh}).fetchone()
            if not exists:
                conn.execute(
                    text("INSERT INTO khach_hang (maKH, hoTen, sdt, ngayTao) VALUES (:makh, :hoten, :sdt, NOW())"),
                    {"makh": makh, "hoten": f"Khách hàng {makh}", "sdt": "0900000000"}
                )
                print(f"   -> Da them khach hang mau cho ma: {makh}")

        # Đồng thời thêm một vài khách hàng mẫu đẹp nếu danh sách ít
        sample_customers = [
            ("KH001", "Nguyễn Văn Long", "0918123456", "123 Lê Duẩn, Hà Nội"),
            ("KH002", "Trần Mai Anh", "0982998877", "45 Cầu Giấy, Hà Nội"),
            ("KH003", "Chị Lan Hoàng", "0934556677", "88 Hai Bà Trưng, Hà Nội"),
            ("KH004", "Anh Tuấn Hùng", "0905112233", "67 Kim Mã, Ba Đình"),
            ("KH005", "Chú Tuấn Minh", "0977889900", "12 Xã Đàn, Đống Đa"),
        ]
        for cid, cname, cphone, caddr in sample_customers:
            exists = conn.execute(text("SELECT maKH FROM khach_hang WHERE maKH = :makh"), {"makh": cid}).fetchone()
            if not exists:
                conn.execute(
                    text("INSERT INTO khach_hang (maKH, hoTen, sdt, diaChi, ngayTao) VALUES (:cid, :cname, :cphone, :caddr, NOW())"),
                    {"cid": cid, "cname": cname, "cphone": cphone, "caddr": caddr}
                )

        conn.commit()

        # 3. Chuẩn hóa độ dài cột maKH trong phieu_sua_chua thành VARCHAR(50)
        try:
            conn.execute(text("ALTER TABLE phieu_sua_chua MODIFY COLUMN maKH VARCHAR(50) NOT NULL;"))
            conn.commit()
        except Exception as e:
            print("   Luu y alter column maKH:", e)

        # 4. Kiểm tra và bổ sung Khóa ngoại (Foreign Keys) nếu chưa có
        insp = inspect(engine)
        
        # Hàm kiểm tra FK đã tồn tại chưa
        def has_fk(table_name, col_name, ref_table):
            fks = insp.get_foreign_keys(table_name)
            for fk in fks:
                if col_name in fk.get('constrained_columns', []) and fk.get('referred_table') == ref_table:
                    return True
            return False

        # FK: phieu_sua_chua.maKH -> khach_hang.maKH
        if not has_fk('phieu_sua_chua', 'maKH', 'khach_hang'):
            try:
                conn.execute(text("""
                    ALTER TABLE phieu_sua_chua 
                    ADD CONSTRAINT fk_phieu_khach_hang 
                    FOREIGN KEY (maKH) REFERENCES khach_hang(maKH) 
                    ON UPDATE CASCADE;
                """))
                conn.commit()
                print("   [OK] Da them FK: phieu_sua_chua.maKH -> khach_hang.maKH")
            except Exception as e:
                print("   [Luu y] FK phieu_khach_hang:", e)

        # FK: phieu_sua_chua.maKTV -> nhan_vien.maNV
        if not has_fk('phieu_sua_chua', 'maKTV', 'nhan_vien'):
            try:
                conn.execute(text("""
                    ALTER TABLE phieu_sua_chua 
                    ADD CONSTRAINT fk_phieu_nhan_vien 
                    FOREIGN KEY (maKTV) REFERENCES nhan_vien(maNV) 
                    ON UPDATE CASCADE ON DELETE SET NULL;
                """))
                conn.commit()
                print("   [OK] Da them FK: phieu_sua_chua.maKTV -> nhan_vien.maNV")
            except Exception as e:
                print("   [Luu y] FK phieu_nhan_vien:", e)

        # 5. Migrate dữ liệu thanh toán từ shifts_data.json sang bảng hoa_don
        print("[3] Kiem tra va migrate lich su thanh toan tu shifts_data.json sang MySQL hoa_don...")
        if os.path.exists("shifts_data.json"):
            try:
                with open("shifts_data.json", "r", encoding="utf-8") as f:
                    sdata = json.load(f)
                    
                payments = sdata.get("thanh_toan", [])
                for p in payments:
                    ma_hd = p.get("maGiaoDich") or f"HD-{p.get('maPhieu')}"
                    ma_phieu = p.get("maPhieu")
                    
                    # Kiểm tra xem phiếu có tồn tại trong phieu_sua_chua không
                    phieu_exists = conn.execute(text("SELECT maPhieu, maKH FROM phieu_sua_chua WHERE maPhieu = :mp"), {"mp": ma_phieu}).fetchone()
                    if not phieu_exists:
                        continue
                    
                    hd_exists = conn.execute(text("SELECT maHD FROM hoa_don WHERE maHD = :mhd OR maPhieu = :mp"), {"mhd": ma_hd, "mp": ma_phieu}).fetchone()
                    if not hd_exists:
                        # Kiểm tra maKH
                        makh = p.get("maKH") or phieu_exists[1]
                        # Đảm bảo makh có trong khach_hang
                        c_ex = conn.execute(text("SELECT maKH FROM khach_hang WHERE maKH = :mk"), {"mk": makh}).fetchone()
                        if not c_ex:
                            conn.execute(text("INSERT INTO khach_hang (maKH, hoTen, sdt) VALUES (:mk, :ht, '0900000000')"), {"mk": makh, "ht": f"Khách hàng {makh}"})

                        # Kiểm tra maThuNgan
                        ma_tn = p.get("maThuNgan")
                        tn_ex = conn.execute(text("SELECT maNV FROM nhan_vien WHERE maNV = :mnv"), {"mnv": ma_tn}).fetchone()
                        if not tn_ex:
                            ma_tn = None

                        ngay_tt = p.get("ngayThanhToan")
                        try:
                            dt_tt = datetime.strptime(ngay_tt, "%Y-%m-%d %H:%M:%S")
                        except Exception:
                            dt_tt = datetime.now()

                        conn.execute(text("""
                            INSERT INTO hoa_don (maHD, maPhieu, maKH, maThuNgan, phuongThuc, tienLinhKien, tienCong, tongTien, tienKhachDua, tienTraLai, ghiChu, ngayThanhToan)
                            VALUES (:maHD, :maPhieu, :maKH, :maThuNgan, :phuongThuc, :tienLinhKien, :tienCong, :tongTien, :tienKhachDua, :tienTraLai, :ghiChu, :ngayThanhToan)
                        """), {
                            "maHD": ma_hd,
                            "maPhieu": ma_phieu,
                            "maKH": makh,
                            "maThuNgan": ma_tn,
                            "phuongThuc": p.get("phuongThuc", "TienMat"),
                            "tienLinhKien": float(p.get("tienLinhKien", 0.0)),
                            "tienCong": float(p.get("tienCong", 150000.0)),
                            "tongTien": float(p.get("tongTien", 150000.0)),
                            "tienKhachDua": float(p.get("tongTien", 150000.0)),
                            "tienTraLai": 0.0,
                            "ghiChu": p.get("ghiChu", "Migrate tu shifts_data.json"),
                            "ngayThanhToan": dt_tt
                        })
                        print(f"   -> Da migrate hoa don: {ma_hd} cho phieu {ma_phieu}")
                conn.commit()
            except Exception as ex:
                print("   Loi migrate shifts_data:", ex)

        # 6. Bật lại kiểm tra FK
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
        conn.commit()

    print("=== HOAN TAT MIGRATION & LIEN KET CSDL MYSQL ===")

if __name__ == "__main__":
    migrate()

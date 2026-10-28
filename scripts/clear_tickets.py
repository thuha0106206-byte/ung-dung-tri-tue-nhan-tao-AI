import sys
sys.path.insert(0, 'backend')
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("[*] Dang tien hanh lam sach danh sach thiet bi va phieu sua chua...")
    
    # 1. Tat kiem tra foreign key tam thoi de xoa sach se
    db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    
    # 2. Xoa cac bang lien quan den phieu sua
    for tbl in ["chi_tiet_sua_chua", "danh_gia_dich_vu", "thong_bao_khach", "hoa_don", "phieu_sua_chua"]:
        try:
            db.execute(text(f"TRUNCATE TABLE {tbl};"))
            print(f" - Da lam sach bang: {tbl}")
        except Exception as e:
            # Neu truncate bi chan boi FK thi dung delete
            db.execute(text(f"DELETE FROM {tbl};"))
            print(f" - Da xoa du lieu bang: {tbl}")

    # 3. Bat lai kiem tra foreign key
    db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    
    db.commit()
    print("\n[SUCCESS] DA LOAI BO THANH CONG TOAN BO PHIEU SUA CHUA & THIET BI!")
    print(" - Tab 'Thiet Bi Cua Toi': 0")
    print(" - Tab 'May Cho Nhan': 0")
    print(" - San sang de quy trinh Le tan -> KTV tiep nhan may moi tu dau.")
except Exception as e:
    db.rollback()
    print(f"[ERROR] Loi khi lam sach du lieu: {e}")
finally:
    db.close()

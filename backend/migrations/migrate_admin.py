import database
import models
from sqlalchemy import text, inspect

def run_migration():
    print("[MIGRATION] Bắt đầu kiểm tra và cập nhật Schema cho Admin...")
    engine = database.engine
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # 1. Bổ sung cột cho bảng nhan_vien nếu thiếu
        if "nhan_vien" in existing_tables:
            nv_cols = [c["name"] for c in inspector.get_columns("nhan_vien")]
            if "trangThai" not in nv_cols:
                try:
                    conn.execute(text("ALTER TABLE nhan_vien ADD COLUMN trangThai VARCHAR(20) DEFAULT 'HOAT_DONG'"))
                    conn.commit()
                    print("-> Đã thêm cột trangThai vào nhan_vien")
                except Exception as e:
                    print(f"Lỗi thêm trangThai: {e}")
            if "vaiTro" not in nv_cols:
                try:
                    conn.execute(text("ALTER TABLE nhan_vien ADD COLUMN vaiTro VARCHAR(50) DEFAULT 'Kỹ thuật viên'"))
                    conn.commit()
                    print("-> Đã thêm cột vaiTro vào nhan_vien")
                except Exception as e:
                    print(f"Lỗi thêm vaiTro: {e}")
            if "quyenTruyCap" not in nv_cols:
                try:
                    conn.execute(text("ALTER TABLE nhan_vien ADD COLUMN quyenTruyCap TEXT NULL"))
                    conn.commit()
                    print("-> Đã thêm cột quyenTruyCap vào nhan_vien")
                except Exception as e:
                    print(f"Lỗi thêm quyenTruyCap: {e}")

        # 2. Bổ sung cột cho bảng linh_kien nếu thiếu
        if "linh_kien" in existing_tables:
            lk_cols = [c["name"] for c in inspector.get_columns("linh_kien")]
            if "giaNhap" not in lk_cols:
                try:
                    conn.execute(text("ALTER TABLE linh_kien ADD COLUMN giaNhap FLOAT DEFAULT 0.0"))
                    conn.commit()
                    print("-> Đã thêm cột giaNhap vào linh_kien")
                except Exception as e:
                    print(f"Lỗi thêm giaNhap: {e}")
            if "tonToiThieu" not in lk_cols:
                try:
                    conn.execute(text("ALTER TABLE linh_kien ADD COLUMN tonToiThieu INT DEFAULT 5"))
                    conn.commit()
                    print("-> Đã thêm cột tonToiThieu vào linh_kien")
                except Exception as e:
                    print(f"Lỗi thêm tonToiThieu: {e}")

    # 3. Tạo các bảng mới tự động bằng SQLAlchemy
    models.Base.metadata.create_all(bind=engine)
    print("-> Đã khởi tạo các bảng mới trong Base.metadata thành công!")

if __name__ == "__main__":
    run_migration()

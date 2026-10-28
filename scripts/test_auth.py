import sys
sys.path.insert(0, 'backend')
from main import login, LoginRequest
from database import SessionLocal

db = SessionLocal()
test_accounts = [
    ('letan', '123'),
    ('ktv', '123'),
    ('kythuatvien', '123'),
    ('thungan', '123'),
    ('admin', '123'),
    ('Lễ tân', '123'),
    ('Kỹ thuật viên', '123'),
    ('Thu ngân', '123'),
    ('Admin', '123'),
    ('hieuktv', '123')
]

all_pass = True
for u, p in test_accounts:
    try:
        creds = LoginRequest(tenDangNhap=u, matKhau=p)
        res = login(creds, db)
        print(f"[PASS] Dang nhap thanh cong: '{u}' -> {res.get('hoTen')} ({res.get('chucVu')})")
    except Exception as e:
        print(f"[FAIL] Dang nhap that bai: '{u}' -> {e}")
        all_pass = False

db.close()
if all_pass:
    print("\n[PERFECT] Tat ca cac tai khoan tac nhan deu dang nhap thanh cong voi mat khau 123!")

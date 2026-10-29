import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from database import SessionLocal
import models

db = SessionLocal()
print("=== PHIEU SUA CHUA ===")
tickets = db.query(models.PhieuSuaChua).all()
print(f"Total tickets: {len(tickets)}")
for t in tickets:
    print(f"Ticket: {t.maPhieu} | KH: {t.maKH} | KTV: {t.maKTV} | Status: {t.trangThai} | Device: {getattr(t, 'tenMay', '')}")

print("\n=== KHACH HANG ===")
customers = db.query(models.KhachHang).all()
print(f"Total customers: {len(customers)}")
for c in customers:
    print(f"KH: {c.maKH} | Name: {c.hoTen} | Phone: {c.sdt} | Email: {c.email}")

print("\n=== LICH HEN ===")
bookings = db.query(models.LichHen).all()
print(f"Total bookings: {len(bookings)}")
for b in bookings:
    print(f"LH: {b.MaLH} | KH: {b.MaKH} | Phone: {b.Model} | Status: {b.TrangThai} | MaPhieu: {b.MaPhieu}")

db.close()

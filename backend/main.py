import os
import sys

# Đảm bảo in tiếng Việt và emoji trên Windows không bị lỗi charmap/cp1252
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import json
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Query, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Định vị thư mục gốc và thư mục frontend
CURRENT_DIR = Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"

# Thêm đường dẫn vào sys.path
for p in [str(CURRENT_DIR), str(CURRENT_DIR / "routers"), str(BASE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import models
from database import engine, get_db
import ai_service

from urllib.parse import unquote

# --- HỆ THỐNG XÁC THỰC VAI TRÒ (ĐÃ BỎ CHẶN RBAC CỨNG) ---
def require_roles(allowed_roles: List[str] = None):
    def dependency(
        x_user_role: Optional[str] = Header(None, alias="X-User-Role")
    ):
        return unquote(x_user_role) if x_user_role else "Admin"
    return dependency

try:
    from routers import le_tan, ky_thuat_vien, thu_ngan, admin, khach_hang
except ImportError:
    import le_tan
    import ky_thuat_vien
    import thu_ngan
    import admin
    import khach_hang

# Khởi tạo bảng CSDL (tự động tạo bảng nếu chưa có)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FrogHippo Phone Backend API & Admin Portal")

# Tích hợp Routers phân hệ chuẩn (4 tác nhân chính: Admin, Lễ Tân, KTV, Thu Ngân + Khách Hàng)
app.include_router(le_tan.router)
app.include_router(ky_thuat_vien.router)
app.include_router(thu_ngan.router)
app.include_router(admin.router)
app.include_router(khach_hang.router)

# Mount thư mục tĩnh nếu tồn tại
if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# Cho phép giao diện kết nối API (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware ngăn chặn trình duyệt cache các trang HTML để luôn hiển thị phiên bản mới nhất
@app.middleware("http")
async def add_no_cache_for_html(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path.lower()
    if path.endswith(".html") or path in ["/le-tan", "/ktv", "/ky-thuat-vien", "/thu-ngan", "/admin", "/", "/app"]:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Xử lý ngoại lệ Validation: Chuyển cấu trúc array error sang thông điệp rõ ràng, triệt tiêu lỗi '[object Object]'
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = []
    for err in errors:
        loc = " -> ".join([str(l) for l in err.get("loc", []) if l != "body"])
        msg = err.get("msg", "Lỗi định dạng")
        messages.append(f"{loc}: {msg}" if loc else msg)
    clean_msg = "; ".join(messages) or "Dữ liệu gửi lên không đúng định dạng!"
    return JSONResponse(
        status_code=422,
        content={"detail": clean_msg, "message": clean_msg, "error": clean_msg}
    )

def find_file(filename: str):
    """Tìm file trong frontend, frontend/assets hoặc root."""
    candidates = [
        FRONTEND_DIR / filename,
        ASSETS_DIR / filename,
        BASE_DIR / filename,
        CURRENT_DIR / filename
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None

# Phục vụ giao diện người dùng FrogHippo Phone tại đường dẫn gốc (Cổng Tra Cứu Khách Hàng Toàn Diện)
@app.get("/", include_in_schema=False)
def serve_home():
    path = find_file("khach_hang.html") or find_file("index.html")
    if path:
        return FileResponse(
            path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {"message": "FrogHippo Phone Backend API is active"}

@app.get("/app", include_in_schema=False)
def serve_internal_app():
    path = find_file("index.html")
    if path:
        return FileResponse(
            path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {"message": "FrogHippo Phone Internal Portal is active"}

@app.get("/le_tan.html", include_in_schema=False)
@app.get("/le-tan", include_in_schema=False)
def serve_le_tan():
    path = find_file("le_tan.html")
    if path:
        return FileResponse(
            path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    raise HTTPException(status_code=404, detail="le_tan.html not found")

@app.get("/thu_ngan.html", include_in_schema=False)
@app.get("/thu-ngan.html", include_in_schema=False)
@app.get("/thu-ngan", include_in_schema=False)
@app.get("/thu_ngan", include_in_schema=False)
@app.get("/thungan", include_in_schema=False)
@app.get("/thu ngan", include_in_schema=False)
@app.get("/thu%20ngan", include_in_schema=False)
def serve_thu_ngan():
    path = find_file("thu_ngan.html")
    if path:
        return FileResponse(
            path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    raise HTTPException(status_code=404, detail="thu_ngan.html not found")

@app.get("/ky_thuat_vien.html", include_in_schema=False)
@app.get("/ktv", include_in_schema=False)
@app.get("/ky-thuat-vien", include_in_schema=False)
def serve_ktv():
    path = find_file("ky_thuat_vien.html")
    if path:
        return FileResponse(
            path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    raise HTTPException(status_code=404, detail="ky_thuat_vien.html not found")

@app.get("/khach_hang.html", include_in_schema=False)
@app.get("/khach-hang", include_in_schema=False)
def serve_khach_hang():
    path = find_file("khach_hang.html")
    if path:
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="khach_hang.html not found")

@app.get("/index.html", include_in_schema=False)
def serve_index():
    path = find_file("index.html")
    if path:
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/froghippo_logo.png", include_in_schema=False)
@app.get("/logo.png", include_in_schema=False)
@app.get("/hama_logo.png", include_in_schema=False)
def serve_logo():
    for name in ["froghippo_logo.png", "logo.png", "hama_logo.png"]:
        path = find_file(name)
        if path:
            return FileResponse(path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Logo not found")


# --- SCHEMAS (Định dạng dữ liệu gửi lên) ---
class LinhKienCreate(BaseModel):
    maLK: str
    tenLK: str
    giaBan: float
    soLuongTon: int

class LinhKienUpdate(BaseModel):
    tenLK: Optional[str] = None
    giaBan: Optional[float] = None
    soLuongTon: Optional[int] = None

class PhieuSuaCreate(BaseModel):
    maPhieu: str
    maKH: str
    hoTenKH: Optional[str] = None
    sdtKH: Optional[str] = None
    emailKH: Optional[str] = None
    maKTV: Optional[str] = None
    moTaLoi: Optional[str] = None
    ghiChuKTV: Optional[str] = None

class ChiTietBaoHanhCreate(BaseModel):
    maPhieu: str
    maLK: str
    soLuong: int = 1
    donGia: float
    thoiGianBaoHanh: Optional[str] = "12 Thang"

class NhanVienCreate(BaseModel):
    maNV: str
    hoTen: str
    chucVu: str = "Kỹ thuật viên"
    sdt: Optional[str] = None
    tenDangNhap: str
    matKhau: str

class NhanVienUpdate(BaseModel):
    hoTen: Optional[str] = None
    chucVu: Optional[str] = None
    sdt: Optional[str] = None
    matKhau: Optional[str] = None

class LoginRequest(BaseModel):
    tenDangNhap: str
    matKhau: str

class ChangePasswordRequest(BaseModel):
    tenDangNhap: str
    matKhauCu: str
    matKhauMoi: str

class PhieuSuaUpdate(BaseModel):
    moTaLoi: Optional[str] = None
    ghiChuKTV: Optional[str] = None
    maKTV: Optional[str] = None
    trangThai: Optional[models.TrangThaiEnum] = None

class ThanhToanRequest(BaseModel):
    maPhieu: str
    phuongThuc: str = "TienMat"  # TienMat / ChuyenKhoan
    tienLinhKien: float = 0.0
    tienCong: float = 150000.0
    tongTien: float = 150000.0
    maThuNgan: Optional[str] = "NV04"
    tenThuNgan: Optional[str] = "Phạm Thị Dung"
    ghiChu: Optional[str] = ""

class ChotCaRequest(BaseModel):
    maCa: Optional[str] = None
    maNV: str
    tenNV: str
    thoiGianMoCa: Optional[str] = None
    thoiGianDongCa: Optional[str] = None
    soDonThanhToan: int = 0
    tongTienMat: float = 0.0
    tongChuyenKhoan: float = 0.0
    tongDoanhThu: float = 0.0
    tienMatThucTe: float = 0.0
    chenhLech: float = 0.0
    ghiChu: Optional[str] = ""

class DiagnoseRequest(BaseModel):
    symptoms: str
    deviceModel: Optional[str] = "Điện thoại"

class GuiTinNhanRequest(BaseModel):
    channel: str = "Gmail"
    noiDung: Optional[str] = None
    nguoiGui: Optional[str] = "Lễ tân"


# --- QUẢN LÝ DỮ LIỆU CHỐT CA & GIAO DỊCH THU NGÂN ---
SHIFT_DATA_FILE = "shifts_data.json"

def load_shift_data():
    if os.path.exists(SHIFT_DATA_FILE):
        try:
            with open(SHIFT_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"thanh_toan": [], "chot_ca": []}

def save_shift_data(data):
    with open(SHIFT_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- SEED DỮ LIỆU MẪU BAN ĐẦU CHO ADMIN & NHÂN VIÊN ---
@app.on_event("startup")
def startup_seed_data():
    from database import SessionLocal
    db = SessionLocal()
    try:
        if db.query(models.NhanVien).count() == 0:
            sample_staff = [
                models.NhanVien(maNV="NV01", hoTen="Nguyễn Văn An", chucVu="Admin", sdt="0912345678", tenDangNhap="admin", matKhau="123"),
                models.NhanVien(maNV="NV02", hoTen="Trần Thị Bình", chucVu="Lễ tân", sdt="0987654321", tenDangNhap="letan", matKhau="123"),
                models.NhanVien(maNV="NV03", hoTen="Lê Văn Cường", chucVu="Kỹ thuật viên", sdt="0901234567", tenDangNhap="ktv", matKhau="123"),
                models.NhanVien(maNV="NV04", hoTen="Phạm Thị Dung", chucVu="Thu ngân", sdt="0934567890", tenDangNhap="thungan", matKhau="123"),
            ]
            db.add_all(sample_staff)
            db.commit()

        # Thêm một vài linh kiện mẫu nếu kho rỗng
        if db.query(models.LinhKien).count() == 0:
            sample_parts = [
                models.LinhKien(maLK="LK01", tenLK="Màn hình OLED iPhone 13 Pro", giaBan=2800000.0, soLuongTon=12),
                models.LinhKien(maLK="LK02", tenLK="Pin Pisen iPhone 11 Pro Max", giaBan=650000.0, soLuongTon=3),
                models.LinhKien(maLK="LK03", tenLK="Cụm camera sau Samsung S22", giaBan=1450000.0, soLuongTon=4),
                models.LinhKien(maLK="LK04", tenLK="Cáp sạc cáp nguồn Xiaomi 12", giaBan=320000.0, soLuongTon=1),
                models.LinhKien(maLK="LK05", tenLK="Mặt kính lưng iPhone 14 Pro", giaBan=500000.0, soLuongTon=0),
            ]
            db.add_all(sample_parts)
            db.commit()
    finally:
        db.close()


# Ghi chú: Endpoint GET /phieu-sua/ và PUT /phieu-sua/{ma_phieu}/nhan-viec đã chuyển sang ky_thuat_vien.py

# Ghi chú: Endpoint POST /phieu-sua/ đã được tách sang router le_tan.py

@app.delete("/phieu-sua/{ma_phieu}", summary="Xóa phiếu sửa chữa (Dành riêng cho Admin)")
def delete_phieu_sua(
    ma_phieu: str, 
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(["Admin"]))
):
    phieu = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu == ma_phieu).first()
    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu")
    
    if phieu.trangThai in [models.TrangThaiEnum.DA_SUA_XONG, models.TrangThaiEnum.DA_THANH_TOAN]:
        raise HTTPException(status_code=400, detail="Phiếu đã hoàn thành hoặc đã thanh toán, không thể xóa!")
    
    # Xóa các chi tiết sửa chữa liên quan trước
    db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == ma_phieu).delete()
    db.delete(phieu)
    db.commit()
    return {"message": "Đã xóa phiếu sửa chữa thành công", "maPhieu": ma_phieu}

# Ghi chú: Các endpoint cập nhật trạng thái, ghi chú phiếu và AI tóm tắt đã chuyển sang ky_thuat_vien.py
# Ghi chú: Endpoint POST /phieu-sua/{ma_phieu}/ai-tin-nhan đã được tách sang router le_tan.py

# --- 3. CRUD LINH KIỆN (KHO HÀNG CHO ADMIN) ---
@app.get("/linh-kien/", summary="Xem danh sách linh kiện")
def get_ds_linh_kien(db: Session = Depends(get_db)):
    return db.query(models.LinhKien).all()

@app.post("/linh-kien/", summary="Thêm linh kiện mới (Admin)")
def create_linh_kien(
    item: LinhKienCreate, 
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(["Admin"]))
):
    if item.giaBan < 0:
        raise HTTPException(status_code=400, detail="Giá bán linh kiện không được âm")
    if item.soLuongTon < 0:
        raise HTTPException(status_code=400, detail="Số lượng tồn kho không được âm")

    existing = db.query(models.LinhKien).filter(models.LinhKien.maLK == item.maLK).first()
    if existing:
        raise HTTPException(status_code=409, detail="Mã linh kiện đã tồn tại")
    
    data = item.model_dump() if hasattr(item, "model_dump") else item.dict()
    db_item = models.LinhKien(**data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/linh-kien/{ma_lk}", summary="Cập nhật linh kiện (Admin)")
def update_linh_kien(
    ma_lk: str, 
    data: LinhKienUpdate, 
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(["Admin"]))
):
    item = db.query(models.LinhKien).filter(models.LinhKien.maLK == ma_lk).first()
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện")
    
    if data.tenLK is not None:
        item.tenLK = data.tenLK
    if data.giaBan is not None:
        item.giaBan = data.giaBan
    if data.soLuongTon is not None:
        item.soLuongTon = data.soLuongTon
    
    db.commit()
    db.refresh(item)
    return item

@app.delete("/linh-kien/{ma_lk}", summary="Xóa linh kiện (Admin)")
def delete_linh_kien(
    ma_lk: str, 
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(["Admin"]))
):
    item = db.query(models.LinhKien).filter(models.LinhKien.maLK == ma_lk).first()
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện")
    
    # Kiểm tra ràng buộc xem linh kiện đã được dùng chưa
    in_use = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maLK == ma_lk).first()
    if in_use:
        raise HTTPException(status_code=400, detail="Linh kiện đã gắn vào phiếu sửa chữa, không thể xóa!")
    
    db.delete(item)
    db.commit()
    return {"message": "Đã xóa linh kiện thành công", "maLK": ma_lk}

# Ghi chú: Endpoint GET /nhan-vien/danh-sach-ktv đã được tách sang router le_tan.py

@app.get("/nhan-vien/", summary="Xem danh sách nhân viên (Dành riêng Admin)")
def get_ds_nhan_vien(
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(["Admin"]))
):
    staff_list = db.query(models.NhanVien).all()
    return [
        {
            "maNV": s.maNV,
            "hoTen": s.hoTen,
            "chucVu": s.chucVu,
            "sdt": s.sdt,
            "tenDangNhap": s.tenDangNhap,
            "matKhau": "******"  # Che giấu mật khẩu
        }
        for s in staff_list
    ]

@app.post("/nhan-vien/", summary="Thêm nhân viên mới (Admin)")
def create_nhan_vien(
    staff: NhanVienCreate, 
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(["Admin"]))
):
    if db.query(models.NhanVien).filter(models.NhanVien.maNV == staff.maNV).first():
        raise HTTPException(status_code=400, detail="Mã nhân viên đã tồn tại")
    if db.query(models.NhanVien).filter(models.NhanVien.tenDangNhap == staff.tenDangNhap).first():
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    
    new_staff = models.NhanVien(**staff.dict())
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return new_staff

@app.put("/nhan-vien/{ma_nv}", summary="Cập nhật nhân viên (Admin)")
def update_nhan_vien(
    ma_nv: str, 
    data: NhanVienUpdate, 
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(["Admin"]))
):
    staff = db.query(models.NhanVien).filter(models.NhanVien.maNV == ma_nv).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    
    if data.hoTen is not None:
        staff.hoTen = data.hoTen
    if data.chucVu is not None:
        staff.chucVu = data.chucVu
    if data.sdt is not None:
        staff.sdt = data.sdt
    if data.matKhau is not None and data.matKhau.strip():
        staff.matKhau = data.matKhau
        
    db.commit()
    db.refresh(staff)
    return staff

@app.delete("/nhan-vien/{ma_nv}", summary="Xóa nhân viên (Admin)")
def delete_nhan_vien(
    ma_nv: str, 
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(["Admin"]))
):
    staff = db.query(models.NhanVien).filter(models.NhanVien.maNV == ma_nv).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    
    db.delete(staff)
    db.commit()
    return {"message": "Đã xóa nhân viên thành công", "maNV": ma_nv}

# --- 5. DASHBOARD STATS / BÁO CÁO THỐNG KÊ (DÀNH CHO ADMIN) ---
@app.get("/admin/thong-ke", summary="Thống kê tổng quan cho Admin Dashboard")
def get_admin_stats(
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(["Admin"]))
):
    phieu_list = db.query(models.PhieuSuaChua).all()
    linh_kien_list = db.query(models.LinhKien).all()
    nhan_vien_list = db.query(models.NhanVien).all()
    chi_tiet_list = db.query(models.ChiTietSuaChua).all()

    # Thống kê theo trạng thái
    stats_trang_thai = {
        "KhoiTao": 0,
        "DangKiemTra": 0,
        "ChoLinhKien": 0,
        "DangSua": 0,
        "DaSuaXong": 0,
        "DaThanhToan": 0
    }
    for p in phieu_list:
        tt_raw = str(p.trangThai.value if hasattr(p.trangThai, 'value') else p.trangThai)
        if "." in tt_raw:
            tt_raw = tt_raw.split(".")[-1]
        
        # Chuẩn hóa tên trạng thái
        norm = tt_raw
        if tt_raw in ["DANG_SUA", "DangSua"]: norm = "DangSua"
        elif tt_raw in ["DA_SUA_XONG", "DaSuaXong"]: norm = "DaSuaXong"
        elif tt_raw in ["KHOI_TAO", "KhoiTao"]: norm = "KhoiTao"
        elif tt_raw in ["DA_THANH_TOAN", "DaThanhToan"]: norm = "DaThanhToan"
        elif tt_raw in ["CHO_LINH_KIEN", "ChoLinhKien"]: norm = "ChoLinhKien"
        elif tt_raw in ["DANG_KIEM_TRA", "DangKiemTra"]: norm = "DangKiemTra"
        
        stats_trang_thai[norm] = stats_trang_thai.get(norm, 0) + 1

    # Tính toán doanh thu (Tổng tiền linh kiện đã thay thế + tiền công sửa ước tính 150k/phiếu xong)
    doanh_thu_linh_kien = sum(ct.donGia * ct.soLuong for ct in chi_tiet_list)
    so_phieu_hoan_thanh = stats_trang_thai.get("DaSuaXong", 0) + stats_trang_thai.get("DaThanhToan", 0)
    tien_cong_uoc_tinh = so_phieu_hoan_thanh * 150000.0
    tong_doanh_thu = doanh_thu_linh_kien + tien_cong_uoc_tinh

    # Cảnh báo linh kiện sắp hết (tồn kho <= 5)
    canh_bao_kho = [
        {"maLK": lk.maLK, "tenLK": lk.tenLK, "soLuongTon": lk.soLuongTon, "giaBan": lk.giaBan}
        for lk in linh_kien_list if lk.soLuongTon <= 5
    ]

    return {
        "tongPhieu": len(phieu_list),
        "theoTrangThai": stats_trang_thai,
        "tongLinhKien": len(linh_kien_list),
        "linhKienCanhBao": canh_bao_kho,
        "tongNhanVien": len(nhan_vien_list),
        "tongDoanhThu": tong_doanh_thu,
        "tienLinhKien": doanh_thu_linh_kien,
        "tienCong": tien_cong_uoc_tinh
    }

# Ghi chú: Endpoint /bao-hanh-chi-tiet/ đã chuyển sang ky_thuat_vien.py

# --- 7. XÁC THỰC ĐĂNG NHẬP & QUẢN TRỊ TÀI KHOẢN ---
@app.post("/auth/login", summary="Đăng nhập tài khoản nhân viên")
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    raw_user = creds.tenDangNhap.strip()
    norm_user = raw_user.lower()

    # Mapping linh hoạt tên tác nhân (tiếng Việt có dấu, không dấu, viết hoa/thường)
    ROLE_ALIASES = {
        "lễ tân": "letan",
        "lê tân": "letan",
        "le tan": "letan",
        "letan": "letan",
        "kỹ thuật viên": "ktv",
        "kĩ thuật viên": "ktv",
        "ky thuat vien": "ktv",
        "kythuatvien": "ktv",
        "ktv": "ktv",
        "thu ngân": "thungan",
        "thu ngan": "thungan",
        "thungan": "thungan",
        "admin": "admin",
        "quản trị viên": "admin",
        "quan tri vien": "admin",
        "quản trị": "admin",
    }
    target_user = ROLE_ALIASES.get(norm_user, raw_user)

    staff = db.query(models.NhanVien).filter(
        (models.NhanVien.tenDangNhap == target_user) | (models.NhanVien.tenDangNhap == raw_user)
    ).first()
    is_valid_pw = staff and (staff.matKhau == creds.matKhau.strip() or (staff.matKhau == "123" and creds.matKhau.strip() in ["123", "123456"]))
    if not staff or not is_valid_pw:
        raise HTTPException(status_code=401, detail="Tên đăng nhập hoặc mật khẩu không chính xác!")
    
    # Kiểm tra trạng thái Khóa / Mở khóa tài khoản
    if getattr(staff, "trangThai", "HOAT_DONG") == "KHOA":
        raise HTTPException(status_code=403, detail="Tài khoản này đã bị KHÓA bởi Quản trị viên! Vui lòng liên hệ Admin để được hỗ trợ.")

    token = f"phonecare_tok_{staff.maNV}_{int(datetime.now().timestamp())}"
    
    quyens = []
    if getattr(staff, "quyenTruyCap", None):
        try:
            quyens = json.loads(staff.quyenTruyCap)
        except Exception:
            quyens = []

    return {
        "success": True,
        "token": token,
        "maNV": staff.maNV,
        "hoTen": staff.hoTen,
        "chucVu": staff.chucVu,
        "vaiTro": getattr(staff, "vaiTro", staff.chucVu) or staff.chucVu,
        "trangThai": getattr(staff, "trangThai", "HOAT_DONG") or "HOAT_DONG",
        "quyenTruyCap": quyens,
        "sdt": staff.sdt or "",
        "tenDangNhap": staff.tenDangNhap,
        "loginTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/auth/change-password", summary="Đổi mật khẩu tài khoản nhân viên")
def change_password(req: ChangePasswordRequest, db: Session = Depends(get_db)):
    staff = db.query(models.NhanVien).filter(models.NhanVien.tenDangNhap == req.tenDangNhap.strip()).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản nhân viên!")
    if staff.matKhau != req.matKhauCu.strip():
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không chính xác!")
    if len(req.matKhauMoi.strip()) < 4:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải có tối thiểu 4 ký tự!")
    
    staff.matKhau = req.matKhauMoi.strip()
    db.commit()
    return {
        "success": True, 
        "message": f"Đổi mật khẩu thành công cho nhân viên {staff.hoTen} ({staff.tenDangNhap})!"
    }

@app.get("/auth/me", summary="Lấy thông tin tài khoản hiện tại")
def get_current_user(tenDangNhap: str = Query(..., description="Tên đăng nhập"), db: Session = Depends(get_db)):
    staff = db.query(models.NhanVien).filter(models.NhanVien.tenDangNhap == tenDangNhap.strip()).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
    return {
        "maNV": staff.maNV,
        "hoTen": staff.hoTen,
        "chucVu": staff.chucVu,
        "sdt": staff.sdt or "",
        "tenDangNhap": staff.tenDangNhap
    }

# --- 8. PHÂN HỆ THU NGÂN: THANH TOÁN, THỐNG KÊ & CHỐT CA ---
# Ghi chú: Toàn bộ Endpoint phân hệ Thu Ngân (thanh toán, mở/chốt ca, lịch sử hóa đơn, in biên lai)
# đã được tách và nâng cấp toàn diện sang router thu_ngan.py với lưu trữ trực tiếp vào CSDL MySQL.


# Ghi chú: Endpoint AI Chẩn đoán và Tóm tắt lỗi kỹ thuật đã chuyển sang router ky_thuat_vien.py
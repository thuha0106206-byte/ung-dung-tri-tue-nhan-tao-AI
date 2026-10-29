import os
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from database import get_db
import models
import ai_service

router = APIRouter(tags=["Phân hệ Quản Lý & Admin"])

# --- DANH MỤC QUYỀN VÀ NHÓM VAI TRÒ CHUẨN ---
DANH_SACH_QUYEN_HE_THONG = [
    {"ma": "QL_NHAN_SU", "ten": "Quản lý nhân sự & phân quyền", "nhom": "Nhân sự"},
    {"ma": "KHOA_TAI_KHOAN", "ten": "Khóa / Mở khóa tài khoản nhân viên", "nhom": "Nhân sự"},
    {"ma": "XEM_KHO", "ten": "Xem danh mục và tồn kho linh kiện", "nhom": "Kho & Dịch vụ"},
    {"ma": "NHAP_KHO", "ten": "Lập phiếu nhập kho linh kiện", "nhom": "Kho & Dịch vụ"},
    {"ma": "KIEM_KE_KHO", "ten": "Kiểm kê & điều chỉnh tồn kho", "nhom": "Kho & Dịch vụ"},
    {"ma": "SUA_GIA_LINH_KIEN", "ten": "Cập nhật bảng giá linh kiện", "nhom": "Kho & Dịch vụ"},
    {"ma": "QUAN_LY_DICH_VU", "ten": "Quản lý danh mục dịch vụ & tiền công", "nhom": "Kho & Dịch vụ"},
    {"ma": "XEM_BAO_CAO_DOANH_THU", "ten": "Xem báo cáo doanh thu & tài chính", "nhom": "Báo cáo"},
    {"ma": "DANH_GIA_KTV", "ten": "Xem báo cáo đánh giá hiệu suất KTV", "nhom": "Báo cáo"},
    {"ma": "QUAN_LY_VOUCHER", "ten": "Quản lý voucher & khuyến mãi", "nhom": "Khuyến mãi"},
    {"ma": "CAU_HINH_AI", "ten": "Cấu hình tham số AI & Hệ thống", "nhom": "Hệ thống"}
]

NHOM_VAI_TRO_MAC_DINH = [
    {
        "maVaiTro": "Admin",
        "tenVaiTro": "Quản Trị Viên Toàn Quyền",
        "moTa": "Toàn quyền quản trị hệ thống, nhân sự, tài chính, kho hàng và cấu hình AI",
        "quyen": [q["ma"] for q in DANH_SACH_QUYEN_HE_THONG]
    },
    {
        "maVaiTro": "QuanLy",
        "tenVaiTro": "Quản Lý Cửa Hàng",
        "moTa": "Giám sát hoạt động, xem báo cáo doanh thu, đánh giá KTV, quản lý kho & voucher",
        "quyen": ["QL_NHAN_SU", "XEM_KHO", "NHAP_KHO", "KIEM_KE_KHO", "SUA_GIA_LINH_KIEN", "QUAN_LY_DICH_VU", "XEM_BAO_CAO_DOANH_THU", "DANH_GIA_KTV", "QUAN_LY_VOUCHER"]
    },
    {
        "maVaiTro": "KyThuatVien",
        "tenVaiTro": "Kỹ Thuật Viên Sửa Chữa",
        "moTa": "Tiếp nhận máy, chẩn đoán AI, cập nhật tiến độ và xuất linh kiện",
        "quyen": ["XEM_KHO"]
    },
    {
        "maVaiTro": "LeTan",
        "tenVaiTro": "Lễ Tân & Tiếp Nhận",
        "moTa": "Tiếp nhận thiết bị, báo giá khách hàng, phân công KTV và gửi tin nhắn",
        "quyen": ["XEM_KHO", "QUAN_LY_DICH_VU"]
    },
    {
        "maVaiTro": "ThuNgan",
        "tenVaiTro": "Thu Ngân & Quầy Thu",
        "moTa": "Tra cứu phiếu, thanh toán, in hóa đơn, mở ca và chốt ca làm việc",
        "quyen": ["QUAN_LY_VOUCHER"]
    },
    {
        "maVaiTro": "ThuKho",
        "tenVaiTro": "Thủ Kho Linh Kiện",
        "moTa": "Chuyên trách quản lý nhập kho, kiểm kê và cảnh báo mức tồn linh kiện",
        "quyen": ["XEM_KHO", "NHAP_KHO", "KIEM_KE_KHO", "SUA_GIA_LINH_KIEN"]
    }
]

# --- SCHEMAS ---
class NhanVienAdminCreate(BaseModel):
    maNV: str
    hoTen: str
    chucVu: str = "Kỹ thuật viên"
    vaiTro: str = "KyThuatVien"
    sdt: Optional[str] = None
    tenDangNhap: str
    matKhau: str
    quyenTruyCap: Optional[List[str]] = None

class NhanVienAdminUpdate(BaseModel):
    hoTen: Optional[str] = None
    chucVu: Optional[str] = None
    vaiTro: Optional[str] = None
    sdt: Optional[str] = None
    matKhau: Optional[str] = None
    quyenTruyCap: Optional[List[str]] = None

class PhanQuyenRequest(BaseModel):
    vaiTro: Optional[str] = None
    quyenTruyCap: List[str]

class NhapKhoRequest(BaseModel):
    maLK: str
    soLuongNhap: int
    giaNhap: float
    nhaCungCap: Optional[str] = "Nhà cung cấp linh kiện chính hãng"
    nguoiNhap: Optional[str] = "Admin"
    ghiChu: Optional[str] = ""

class KiemKeCanDoiRequest(BaseModel):
    maLK: str
    soLuongThucTe: int
    lyDo: Optional[str] = "Kiểm kê định kỳ"

class CapNhatGiaLinhKienRequest(BaseModel):
    giaBan: float
    giaNhap: Optional[float] = None
    tonToiThieu: Optional[int] = 5

class LinhKienAdminCreate(BaseModel):
    maLK: str
    tenLK: str
    giaNhap: float = 0.0
    giaBan: float
    soLuongTon: int = 0
    tonToiThieu: int = 5

class LinhKienAdminUpdate(BaseModel):
    tenLK: Optional[str] = None
    giaNhap: Optional[float] = None
    giaBan: Optional[float] = None
    soLuongTon: Optional[int] = None
    tonToiThieu: Optional[int] = None

class DichVuCreate(BaseModel):
    maDV: str
    tenDV: str
    loaiMay: str = "Tất cả"
    tienCong: float = 150000.0
    thoiGianBaoHanh: str = "12 Tháng"
    moTa: Optional[str] = ""

class DichVuUpdate(BaseModel):
    tenDV: Optional[str] = None
    loaiMay: Optional[str] = None
    tienCong: Optional[float] = None
    thoiGianBaoHanh: Optional[str] = None
    moTa: Optional[str] = None
    trangThai: Optional[str] = None

class VoucherCreate(BaseModel):
    maVoucher: str
    tenVoucher: str
    loaiGiam: str = "PHAN_TRAM" # PHAN_TRAM / SO_TIEN
    giaTriGiam: float
    donToiThieu: float = 0.0
    ngayHetHan: Optional[str] = None
    soLuong: int = 100

class VoucherUpdate(BaseModel):
    tenVoucher: Optional[str] = None
    loaiGiam: Optional[str] = None
    giaTriGiam: Optional[float] = None
    donToiThieu: Optional[float] = None
    ngayHetHan: Optional[str] = None
    soLuong: Optional[int] = None
    trangThai: Optional[str] = None

class CauHinhAIRequest(BaseModel):
    provider: str = "Gemini" # Gemini / OpenAI
    apiKey: Optional[str] = None
    modelName: str = "gemini-1.5-flash"
    temperature: float = 0.3
    systemPrompt: Optional[str] = None
    laborFeeDefault: Optional[float] = 150000.0


# --- ROUTE GIAO DIỆN CHUYÊN BIỆT CHO ADMIN ---
@router.get("/admin", include_in_schema=False)
def get_admin_portal():
    """Phục vụ trang giao diện riêng cho Quản Lý & Admin."""
    for p in ["frontend/admin.html", "admin.html", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "admin.html")]:
        if os.path.exists(p):
            return FileResponse(p)
    raise HTTPException(status_code=404, detail="Không tìm thấy file giao diện admin.html")


# ==============================================================
# NHÓM 1: QUẢN LÝ NHÂN SỰ & PHÂN QUYỀN
# ==============================================================

@router.get("/api/admin/nhan-vien", summary="Danh sách nhân sự & trạng thái tài khoản")
def admin_get_nhan_vien(db: Session = Depends(get_db)):
    staffs = db.query(models.NhanVien).all()
    result = []
    for s in staffs:
        quyens = []
        if s.quyenTruyCap:
            try:
                quyens = json.loads(s.quyenTruyCap)
            except Exception:
                quyens = [s.quyenTruyCap]
        
        result.append({
            "maNV": s.maNV,
            "hoTen": s.hoTen,
            "chucVu": s.chucVu,
            "vaiTro": s.vaiTro or s.chucVu,
            "sdt": s.sdt or "",
            "tenDangNhap": s.tenDangNhap,
            "trangThai": getattr(s, "trangThai", "HOAT_DONG") or "HOAT_DONG",
            "quyenTruyCap": quyens
        })
    return result

@router.post("/api/admin/nhan-vien", summary="Tạo mới nhân viên (Admin)")
def admin_create_nhan_vien(data: NhanVienAdminCreate, db: Session = Depends(get_db)):
    import re
    ma_nv = data.maNV.strip()
    ten_dang_nhap = data.tenDangNhap.strip()

    # Tự sinh tên đăng nhập theo vai trò nếu để trống
    if not ten_dang_nhap:
        prefix_map = {
            "Admin": "admin",
            "QuanLy": "quanly",
            "KyThuatVien": "ktv",
            "LeTan": "letan",
            "ThuNgan": "thungan"
        }
        prefix = prefix_map.get(data.vaiTro, "nv")
        counter = 2
        cand = prefix
        while db.query(models.NhanVien).filter(func.lower(models.NhanVien.tenDangNhap) == cand.lower()).first():
            cand = f"{prefix}{counter:02d}"
            counter += 1
        ten_dang_nhap = cand

    # Nếu mã NV đã tồn tại, tự động lấy mã tiếp theo chưa bị trùng
    if db.query(models.NhanVien).filter(models.NhanVien.maNV == ma_nv).first():
        all_staffs = db.query(models.NhanVien.maNV).all()
        max_num = 0
        for s in all_staffs:
            nums = re.findall(r'\d+', s[0])
            if nums:
                n = int(nums[0])
                if n > max_num: max_num = n
        ma_nv = f"NV{max_num + 1:02d}"

    # Nếu tên đăng nhập đã tồn tại, tự động tăng hậu tố số để không bị chặn
    existing_user = db.query(models.NhanVien).filter(func.lower(models.NhanVien.tenDangNhap) == ten_dang_nhap.lower()).first()
    if existing_user:
        base = ten_dang_nhap
        counter = 2
        while db.query(models.NhanVien).filter(func.lower(models.NhanVien.tenDangNhap) == f"{base}{counter:02d}".lower()).first():
            counter += 1
        ten_dang_nhap = f"{base}{counter:02d}"

    quyens_json = json.dumps(data.quyenTruyCap or [], ensure_ascii=False)
    mat_khau = (data.matKhau or "").strip() or "123"

    nv = models.NhanVien(
        maNV=ma_nv,
        hoTen=data.hoTen.strip(),
        chucVu=data.chucVu.strip(),
        vaiTro=data.vaiTro.strip() if data.vaiTro else data.chucVu.strip(),
        sdt=data.sdt.strip() if data.sdt else "",
        tenDangNhap=ten_dang_nhap,
        matKhau=mat_khau,
        trangThai="HOAT_DONG",
        quyenTruyCap=quyens_json
    )
    db.add(nv)
    db.commit()
    db.refresh(nv)
    return {"success": True, "message": f"Tạo nhân viên {nv.hoTen} ({nv.maNV} - @{nv.tenDangNhap}) thành công! Mật khẩu mặc định: {nv.matKhau}", "nhanVien": nv}

@router.put("/api/admin/nhan-vien/{ma_nv}", summary="Cập nhật thông tin nhân sự")
def admin_update_nhan_vien(ma_nv: str, data: NhanVienAdminUpdate, db: Session = Depends(get_db)):
    nv = db.query(models.NhanVien).filter(models.NhanVien.maNV == ma_nv).first()
    if not nv:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên!")
    
    if data.hoTen is not None:
        nv.hoTen = data.hoTen.strip()
    if data.chucVu is not None:
        nv.chucVu = data.chucVu.strip()
    if data.vaiTro is not None:
        nv.vaiTro = data.vaiTro.strip()
    if data.sdt is not None:
        nv.sdt = data.sdt.strip()
    if data.matKhau is not None and data.matKhau.strip():
        nv.matKhau = data.matKhau.strip()
    if data.quyenTruyCap is not None:
        nv.quyenTruyCap = json.dumps(data.quyenTruyCap, ensure_ascii=False)

    db.commit()
    db.refresh(nv)
    return {"success": True, "message": f"Cập nhật thông tin nhân viên {nv.hoTen} thành công!"}

@router.put("/api/admin/nhan-vien/{ma_nv}/toggle-status", summary="Khóa / Mở khóa tài khoản nhân sự")
def admin_toggle_staff_status(ma_nv: str, db: Session = Depends(get_db)):
    nv = db.query(models.NhanVien).filter(models.NhanVien.maNV == ma_nv).first()
    if not nv:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên!")
    if nv.tenDangNhap.lower() == "admin" or nv.maNV == "NV01":
        raise HTTPException(status_code=400, detail="Không thể khóa tài khoản Quản trị viên tối cao (Admin)!")

    current_status = getattr(nv, "trangThai", "HOAT_DONG") or "HOAT_DONG"
    new_status = "KHOA" if current_status == "HOAT_DONG" else "HOAT_DONG"
    nv.trangThai = new_status
    db.commit()

    action_text = "Đã KHÓA" if new_status == "KHOA" else "Đã MỞ KHÓA"
    return {
        "success": True,
        "message": f"{action_text} tài khoản nhân viên {nv.hoTen} ({nv.tenDangNhap}) thành công!",
        "maNV": nv.maNV,
        "trangThai": new_status
    }

@router.delete("/api/admin/nhan-vien/{ma_nv}", summary="Xóa nhân viên khỏi hệ thống")
def admin_delete_nhan_vien(ma_nv: str, db: Session = Depends(get_db)):
    nv = db.query(models.NhanVien).filter(models.NhanVien.maNV == ma_nv).first()
    if not nv:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên!")
    if nv.tenDangNhap.lower() == "admin" or nv.maNV == "NV01":
        raise HTTPException(status_code=400, detail="Không thể xóa tài khoản Quản trị viên tối cao!")

    db.delete(nv)
    db.commit()
    return {"success": True, "message": f"Đã xóa tài khoản nhân viên {ma_nv} thành công!"}

@router.get("/api/admin/vai-tro", summary="Thiết lập nhóm vai trò & Danh mục quyền hệ thống")
def admin_get_roles():
    return {
        "nhomVaiTro": NHOM_VAI_TRO_MAC_DINH,
        "danhSachQuyen": DANH_SACH_QUYEN_HE_THONG
    }

@router.put("/api/admin/nhan-vien/{ma_nv}/phan-quyen", summary="Gán quyền truy cập cho nhân viên")
def admin_assign_permissions(ma_nv: str, req: PhanQuyenRequest, db: Session = Depends(get_db)):
    nv = db.query(models.NhanVien).filter(models.NhanVien.maNV == ma_nv).first()
    if not nv:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên!")

    if req.vaiTro:
        nv.vaiTro = req.vaiTro
    nv.quyenTruyCap = json.dumps(req.quyenTruyCap, ensure_ascii=False)
    db.commit()

    return {
        "success": True,
        "message": f"Đã cập nhật phân quyền cho {nv.hoTen} thành công!",
        "quyenTruyCap": req.quyenTruyCap
    }


# ==============================================================
# NHÓM 2: QUẢN LÝ KHO & BẢNG GIÁ DỊCH VỤ
# ==============================================================

@router.get("/api/admin/kho/kiem-ke", summary="Kiểm kê & Cảnh báo tồn kho linh kiện")
def admin_kiem_ke_kho(db: Session = Depends(get_db)):
    lks = db.query(models.LinhKien).all()
    result = []
    tong_ton = 0
    gia_tri_kho = 0.0
    canh_bao_count = 0

    for lk in lks:
        ton = lk.soLuongTon or 0
        min_ton = getattr(lk, "tonToiThieu", 5) or 5
        gia_nhap = getattr(lk, "giaNhap", 0.0) or 0.0
        gia_ban = lk.giaBan or 0.0

        trang_thai = "AN_TOAN"
        if ton <= 0:
            trang_thai = "CANH_BAO_HET"
            canh_bao_count += 1
        elif ton <= min_ton:
            trang_thai = "SAP_HET"
            canh_bao_count += 1

        tong_ton += ton
        gia_tri_kho += (ton * (gia_nhap if gia_nhap > 0 else gia_ban * 0.7))

        result.append({
            "maLK": lk.maLK,
            "tenLK": lk.tenLK,
            "soLuongTon": ton,
            "tonToiThieu": min_ton,
            "giaNhap": gia_nhap,
            "giaBan": gia_ban,
            "trangThai": trang_thai
        })

    return {
        "tongSoMatHang": len(lks),
        "tongSoLuongTon": tong_ton,
        "giaTriKhoUocTinh": gia_tri_kho,
        "soLuongCanhBao": canh_bao_count,
        "danhSachLinhKien": result
    }

@router.post("/api/admin/kho/nhap-kho", summary="Quản lý nhập kho & Cập nhật tồn kho")
def admin_nhap_kho(req: NhapKhoRequest, db: Session = Depends(get_db)):
    lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == req.maLK).first()
    if not lk:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện trong kho!")
    if req.soLuongNhap <= 0:
        raise HTTPException(status_code=400, detail="Số lượng nhập phải lớn hơn 0!")

    now = datetime.now()
    ma_nhap = f"NK-{now.strftime('%Y%m%d%H%M%S')}"
    tong_tien = req.soLuongNhap * req.giaNhap

    # Tạo phiếu nhập kho
    phieu_nhap = models.PhieuNhapKho(
        maNhap=ma_nhap,
        maLK=req.maLK,
        tenLK=lk.tenLK,
        soLuong=req.soLuongNhap,
        giaNhap=req.giaNhap,
        tongTien=tong_tien,
        nhaCungCap=req.nhaCungCap or "Tổng kho linh kiện",
        nguoiNhap=req.nguoiNhap or "Admin",
        ngayNhap=now,
        ghiChu=req.ghiChu or ""
    )
    db.add(phieu_nhap)

    # Cập nhật tồn kho và giá nhập mới nhất cho linh kiện
    lk.soLuongTon += req.soLuongNhap
    lk.giaNhap = req.giaNhap

    db.commit()
    db.refresh(phieu_nhap)

    return {
        "success": True,
        "message": f"Nhập kho thành công {req.soLuongNhap} {lk.tenLK}. Tồn kho mới: {lk.soLuongTon}!",
        "phieuNhap": {
            "maNhap": phieu_nhap.maNhap,
            "maLK": phieu_nhap.maLK,
            "tenLK": phieu_nhap.tenLK,
            "soLuong": phieu_nhap.soLuong,
            "giaNhap": phieu_nhap.giaNhap,
            "tongTien": phieu_nhap.tongTien,
            "ngayNhap": phieu_nhap.ngayNhap.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

@router.get("/api/admin/kho/lich-su-nhap", summary="Lịch sử các phiếu nhập kho")
def admin_lich_su_nhap_kho(db: Session = Depends(get_db)):
    phieus = db.query(models.PhieuNhapKho).order_by(desc(models.PhieuNhapKho.ngayNhap)).limit(100).all()
    return [
        {
            "maNhap": p.maNhap,
            "maLK": p.maLK,
            "tenLK": p.tenLK,
            "soLuong": p.soLuong,
            "giaNhap": p.giaNhap,
            "tongTien": p.tongTien,
            "nhaCungCap": p.nhaCungCap,
            "nguoiNhap": p.nguoiNhap,
            "ngayNhap": p.ngayNhap.strftime("%Y-%m-%d %H:%M:%S") if p.ngayNhap else "",
            "ghiChu": p.ghiChu or ""
        }
        for p in phieus
    ]

@router.post("/api/admin/kho/kiem-ke-can-doi", summary="Điều chỉnh tồn kho thực tế sau kiểm kê")
def admin_can_doi_kho(req: KiemKeCanDoiRequest, db: Session = Depends(get_db)):
    lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == req.maLK).first()
    if not lk:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện!")
    
    ton_cu = lk.soLuongTon
    lk.soLuongTon = max(0, req.soLuongThucTe)
    db.commit()

    return {
        "success": True,
        "message": f"Đã cân đối tồn kho {lk.tenLK}: từ {ton_cu} -> {lk.soLuongTon} theo biên bản kiểm kê ({req.lyDo})!",
        "maLK": lk.maLK,
        "soLuongTonMoi": lk.soLuongTon
    }

@router.put("/api/admin/kho/linh-kien/{ma_lk}/gia", summary="Cập nhật bảng giá & định mức linh kiện")
def admin_update_gia_linh_kien(ma_lk: str, req: CapNhatGiaLinhKienRequest, db: Session = Depends(get_db)):
    lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == ma_lk).first()
    if not lk:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện!")
    
    lk.giaBan = req.giaBan
    if req.giaNhap is not None:
        lk.giaNhap = req.giaNhap
    if req.tonToiThieu is not None:
        lk.tonToiThieu = req.tonToiThieu

    db.commit()
    return {"success": True, "message": f"Cập nhật giá linh kiện {lk.tenLK} thành công!"}

@router.post("/api/admin/kho/linh-kien", summary="Thêm mới linh kiện / phụ kiện vào kho")
def admin_create_linh_kien(item: LinhKienAdminCreate, db: Session = Depends(get_db)):
    ma_lk = item.maLK.strip()
    ten_lk = item.tenLK.strip()
    if not ma_lk:
        raise HTTPException(status_code=400, detail="Mã linh kiện không được để trống!")
    if not ten_lk:
        raise HTTPException(status_code=400, detail="Tên linh kiện không được để trống!")
    if item.giaBan < 0:
        raise HTTPException(status_code=400, detail="Giá bán không được âm!")
    if item.giaNhap < 0:
        raise HTTPException(status_code=400, detail="Giá nhập không được âm!")
    if item.soLuongTon < 0:
        raise HTTPException(status_code=400, detail="Số lượng tồn kho không được âm!")
    if item.tonToiThieu < 0:
        raise HTTPException(status_code=400, detail="Định mức tối thiểu không được âm!")

    existing = db.query(models.LinhKien).filter(models.LinhKien.maLK == ma_lk).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Mã linh kiện '{ma_lk}' đã tồn tại trong hệ thống!")

    new_item = models.LinhKien(
        maLK=ma_lk,
        tenLK=ten_lk,
        giaNhap=item.giaNhap,
        giaBan=item.giaBan,
        soLuongTon=item.soLuongTon,
        tonToiThieu=item.tonToiThieu
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return {
        "success": True,
        "message": f"Thêm mới linh kiện '{new_item.tenLK}' ({new_item.maLK}) vào kho thành công!",
        "data": {
            "maLK": new_item.maLK,
            "tenLK": new_item.tenLK,
            "giaNhap": new_item.giaNhap,
            "giaBan": new_item.giaBan,
            "soLuongTon": new_item.soLuongTon,
            "tonToiThieu": new_item.tonToiThieu
        }
    }

@router.put("/api/admin/kho/linh-kien/{ma_lk}", summary="Cập nhật toàn diện thông tin linh kiện")
def admin_update_linh_kien_full(ma_lk: str, req: LinhKienAdminUpdate, db: Session = Depends(get_db)):
    lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == ma_lk).first()
    if not lk:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện!")
    
    if req.tenLK is not None and req.tenLK.strip():
        lk.tenLK = req.tenLK.strip()
    if req.giaBan is not None:
        if req.giaBan < 0:
            raise HTTPException(status_code=400, detail="Giá bán không được âm!")
        lk.giaBan = req.giaBan
    if req.giaNhap is not None:
        if req.giaNhap < 0:
            raise HTTPException(status_code=400, detail="Giá nhập không được âm!")
        lk.giaNhap = req.giaNhap
    if req.soLuongTon is not None:
        if req.soLuongTon < 0:
            raise HTTPException(status_code=400, detail="Số lượng tồn kho không được âm!")
        lk.soLuongTon = req.soLuongTon
    if req.tonToiThieu is not None:
        if req.tonToiThieu < 0:
            raise HTTPException(status_code=400, detail="Định mức tối thiểu không được âm!")
        lk.tonToiThieu = req.tonToiThieu

    db.commit()
    return {
        "success": True,
        "message": f"Cập nhật thông tin linh kiện '{lk.tenLK}' ({lk.maLK}) thành công!"
    }

@router.delete("/api/admin/kho/linh-kien/{ma_lk}", summary="Xóa an toàn linh kiện khỏi kho")
def admin_delete_linh_kien(ma_lk: str, db: Session = Depends(get_db)):
    lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == ma_lk).first()
    if not lk:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện!")
    
    # Ràng buộc an toàn: kiểm tra phiếu sửa chữa và phiếu nhập kho
    in_sua_chua = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maLK == ma_lk).first()
    if in_sua_chua:
        raise HTTPException(status_code=400, detail=f"Không thể xóa! Linh kiện {ma_lk} đã phát sinh giao dịch trong phiếu sửa chữa ({in_sua_chua.maPhieu}).")
    
    in_nhap_kho = db.query(models.PhieuNhapKho).filter(models.PhieuNhapKho.maLK == ma_lk).first()
    if in_nhap_kho:
        raise HTTPException(status_code=400, detail=f"Không thể xóa! Linh kiện {ma_lk} đã được ghi nhận trong phiếu nhập kho ({in_nhap_kho.maNhap}).")

    ten_lk = lk.tenLK
    db.delete(lk)
    db.commit()
    return {
        "success": True,
        "message": f"Đã xóa linh kiện '{ten_lk}' ({ma_lk}) khỏi kho thành công!"
    }

# --- QUẢN LÝ DANH MỤC DỊCH VỤ SỬA CHỮA & TIỀN CÔNG ---

@router.get("/api/admin/dich-vu", summary="Danh mục loại dịch vụ & bảng giá tiền công")
def admin_get_dich_vu(db: Session = Depends(get_db)):
    dvs = db.query(models.DichVuSuaChua).all()
    # Nếu chưa có dịch vụ nào, tạo sẵn danh mục chuẩn
    if len(dvs) == 0:
        sample_services = [
            models.DichVuSuaChua(maDV="DV01", tenDV="Thay Màn Hình Cảm Ứng OLED", loaiMay="iPhone / Samsung", tienCong=250000.0, thoiGianBaoHanh="12 Tháng", moTa="Tháo lắp cẩn thận, dán ron chống nước áp suất"),
            models.DichVuSuaChua(maDV="DV02", tenDV="Thay Pin Dung Lượng Chuẩn / Siêu Cao", loaiMay="Tất cả", tienCong=100000.0, thoiGianBaoHanh="12 Tháng", moTa="Kèm keo dán pin zin, kích pin chuẩn"),
            models.DichVuSuaChua(maDV="DV03", tenDV="Ép Kính Mặt Trước / Kính Lưng", loaiMay="Màn cong / phẳng", tienCong=200000.0, thoiGianBaoHanh="6 Tháng", moTa="Công nghệ hút chân không không bọt khí"),
            models.DichVuSuaChua(maDV="DV04", tenDV="Sửa Nguồn, IC Sạc & Chân Cáp Sạc", loaiMay="Tất cả", tienCong=300000.0, thoiGianBaoHanh="6 Tháng", moTa="Đo đạc vi mạch chuyên sâu"),
            models.DichVuSuaChua(maDV="DV05", tenDV="Vệ Sinh Toàn Diện & Tra Keo Tản Nhiệt", loaiMay="Tất cả", tienCong=50000.0, thoiGianBaoHanh="1 Tháng", moTa="Làm sạch loa, mic, cổng sạc và bên trong main")
        ]
        db.add_all(sample_services)
        db.commit()
        dvs = db.query(models.DichVuSuaChua).all()

    return dvs

@router.post("/api/admin/dich-vu", summary="Thêm mới loại dịch vụ sửa chữa")
def admin_create_dich_vu(data: DichVuCreate, db: Session = Depends(get_db)):
    if db.query(models.DichVuSuaChua).filter(models.DichVuSuaChua.maDV == data.maDV.strip()).first():
        raise HTTPException(status_code=400, detail="Mã dịch vụ này đã tồn tại!")
    
    dv = models.DichVuSuaChua(
        maDV=data.maDV.strip(),
        tenDV=data.tenDV.strip(),
        loaiMay=data.loaiMay.strip(),
        tienCong=data.tienCong,
        thoiGianBaoHanh=data.thoiGianBaoHanh,
        moTa=data.moTa or "",
        trangThai="HOAT_DONG"
    )
    db.add(dv)
    db.commit()
    db.refresh(dv)
    return {"success": True, "message": f"Thêm dịch vụ {dv.tenDV} thành công!", "dichVu": dv}

@router.put("/api/admin/dich-vu/{ma_dv}", summary="Cập nhật loại dịch vụ & tiền công")
def admin_update_dich_vu(ma_dv: str, data: DichVuUpdate, db: Session = Depends(get_db)):
    dv = db.query(models.DichVuSuaChua).filter(models.DichVuSuaChua.maDV == ma_dv).first()
    if not dv:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ!")

    if data.tenDV is not None: dv.tenDV = data.tenDV.strip()
    if data.loaiMay is not None: dv.loaiMay = data.loaiMay.strip()
    if data.tienCong is not None: dv.tienCong = data.tienCong
    if data.thoiGianBaoHanh is not None: dv.thoiGianBaoHanh = data.thoiGianBaoHanh
    if data.moTa is not None: dv.moTa = data.moTa
    if data.trangThai is not None: dv.trangThai = data.trangThai

    db.commit()
    return {"success": True, "message": f"Cập nhật dịch vụ {dv.tenDV} thành công!"}

@router.delete("/api/admin/dich-vu/{ma_dv}", summary="Xóa loại dịch vụ")
def admin_delete_dich_vu(ma_dv: str, db: Session = Depends(get_db)):
    dv = db.query(models.DichVuSuaChua).filter(models.DichVuSuaChua.maDV == ma_dv).first()
    if not dv:
        raise HTTPException(status_code=404, detail="Không tìm thấy dịch vụ!")
    db.delete(dv)
    db.commit()
    return {"success": True, "message": f"Đã xóa dịch vụ {ma_dv} thành công!"}


# ==============================================================
# NHÓM 3: XEM BÁO CÁO & CẤU HÌNH HỆ THỐNG
# ==============================================================

@router.get("/api/admin/bao-cao/doanh-thu", summary="Thống kê doanh thu tài chính chuyên sâu")
def admin_bao_cao_doanh_thu(
    khoangThoiGian: str = Query("thang_nay", description="hom_nay, 7_ngay, thang_nay, tat_ca"),
    db: Session = Depends(get_db)
):
    query = db.query(models.HoaDon)
    now = datetime.now()

    if khoangThoiGian == "hom_nay":
        start_date = now.replace(hour=0, minute=0, second=0)
        query = query.filter(models.HoaDon.ngayThanhToan >= start_date)
    elif khoangThoiGian == "7_ngay":
        start_date = now - datetime.timedelta(days=7) if hasattr(datetime, 'timedelta') else now.replace(day=max(1, now.day-7))
        query = query.filter(models.HoaDon.ngayThanhToan >= start_date)
    elif khoangThoiGian == "thang_nay":
        start_date = now.replace(day=1, hour=0, minute=0, second=0)
        query = query.filter(models.HoaDon.ngayThanhToan >= start_date)

    hds = query.order_by(desc(models.HoaDon.ngayThanhToan)).all()

    tong_tien_mat = sum(h.tongTien for h in hds if h.phuongThuc == "TienMat")
    tong_chuyen_khoan = sum(h.tongTien for h in hds if h.phuongThuc == "ChuyenKhoan")
    tong_linh_kien = sum(h.tienLinhKien for h in hds)
    tong_tien_cong = sum(h.tienCong for h in hds)
    tong_doanh_thu = tong_tien_mat + tong_chuyen_khoan

    # Ước tính lợi nhuận gộp (Tiền công + 30% margin linh kiện)
    loi_nhuan_uoc_tinh = tong_tien_cong + (tong_linh_kien * 0.3)

    return {
        "khoangThoiGian": khoangThoiGian,
        "tongSoHoaDon": len(hds),
        "tongDoanhThu": tong_doanh_thu,
        "tienLinhKien": tong_linh_kien,
        "tienCong": tong_tien_cong,
        "tongTienMat": tong_tien_mat,
        "tongChuyenKhoan": tong_chuyen_khoan,
        "loiNhuanUocTinh": loi_nhuan_uoc_tinh,
        "danhSachHoaDon": [
            {
                "maHD": h.maHD,
                "maPhieu": h.maPhieu,
                "phuongThuc": h.phuongThuc,
                "tienLinhKien": h.tienLinhKien,
                "tienCong": h.tienCong,
                "tongTien": h.tongTien,
                "ngayThanhToan": h.ngayThanhToan.strftime("%d/%m/%Y %H:%M") if h.ngayThanhToan else ""
            }
            for h in hds[:50]
        ]
    }

@router.get("/api/admin/bao-cao/hieu-suat-ktv", summary="Đánh giá hiệu suất làm việc của Kỹ Thuật Viên")
def admin_bao_cao_ktv(db: Session = Depends(get_db)):
    ktvs = db.query(models.NhanVien).filter(models.NhanVien.chucVu.in_(["Kỹ thuật viên", "Admin"])).all()
    all_phieus = db.query(models.PhieuSuaChua).all()
    all_hds = db.query(models.HoaDon).all()

    result = []
    for ktv in ktvs:
        my_phieus = [p for p in all_phieus if p.maKTV == ktv.maNV]
        total_assigned = len(my_phieus)
        
        done = len([p for p in my_phieus if p.trangThai in [models.TrangThaiEnum.DA_SUA_XONG, models.TrangThaiEnum.DA_THANH_TOAN]])
        in_progress = len([p for p in my_phieus if p.trangThai in [models.TrangThaiEnum.DANG_KIEM_TRA, models.TrangThaiEnum.DANG_SUA, models.TrangThaiEnum.CHO_LINH_KIEN]])
        waiting = len([p for p in my_phieus if p.trangThai == models.TrangThaiEnum.KHOI_TAO])

        # Doanh số tiền công đóng góp
        my_phieu_ids = {p.maPhieu for p in my_phieus}
        doanh_so = sum(h.tienCong for h in all_hds if h.maPhieu in my_phieu_ids)

        ty_le_hoan_thanh = round((done / total_assigned * 100), 1) if total_assigned > 0 else 100.0

        # Đánh giá xếp hạng
        danh_gia = "Khá"
        if done >= 10 or ty_le_hoan_thanh >= 90:
            danh_gia = "Xuất sắc"
        elif done >= 5:
            danh_gia = "Tốt"

        result.append({
            "maKTV": ktv.maNV,
            "hoTen": ktv.hoTen,
            "chucVu": ktv.chucVu,
            "sdt": ktv.sdt or "",
            "tongNhan": total_assigned,
            "daSuaXong": done,
            "dangXuLy": in_progress,
            "choXuLy": waiting,
            "tyLeHoanThanh": ty_le_hoan_thanh,
            "doanhSoTienCong": doanh_so,
            "xepLoai": danh_gia
        })

    # Sắp xếp theo số đơn hoàn thành giảm dần
    result.sort(key=lambda x: x["daSuaXong"], reverse=True)
    return result

# --- QUẢN LÝ VOUCHER & KHUYẾN MÃI ---

@router.get("/api/admin/voucher", summary="Danh sách Voucher & Khuyến mãi")
def admin_get_vouchers(db: Session = Depends(get_db)):
    vouchers = db.query(models.Voucher).all()
    if len(vouchers) == 0:
        sample_vouchers = [
            models.Voucher(maVoucher="FROGGIFT10", tenVoucher="Giảm 10% Cho Khách Hàng Thân Thiết", loaiGiam="PHAN_TRAM", giaTriGiam=10.0, donToiThieu=200000.0, soLuong=200, daDung=12, trangThai="HOAT_DONG"),
            models.Voucher(maVoucher="TRIAN50K", tenVoucher="Voucher 50K Thay Pin & Màn Hình", loaiGiam="SO_TIEN", giaTriGiam=50000.0, donToiThieu=300000.0, soLuong=100, daDung=28, trangThai="HOAT_DONG"),
            models.Voucher(maVoucher="VIPCARE20", tenVoucher="Ưu đãi 20% Học sinh - Sinh viên", loaiGiam="PHAN_TRAM", giaTriGiam=20.0, donToiThieu=150000.0, soLuong=50, daDung=5, trangThai="HOAT_DONG")
        ]
        db.add_all(sample_vouchers)
        db.commit()
        vouchers = db.query(models.Voucher).all()

    return vouchers

@router.post("/api/admin/voucher", summary="Tạo mới Voucher khuyến mãi")
def admin_create_voucher(data: VoucherCreate, db: Session = Depends(get_db)):
    code = data.maVoucher.strip().upper()
    if db.query(models.Voucher).filter(models.Voucher.maVoucher == code).first():
        raise HTTPException(status_code=400, detail="Mã Voucher này đã tồn tại!")

    v = models.Voucher(
        maVoucher=code,
        tenVoucher=data.tenVoucher.strip(),
        loaiGiam=data.loaiGiam,
        giaTriGiam=data.giaTriGiam,
        donToiThieu=data.donToiThieu,
        soLuong=data.soLuong,
        daDung=0,
        trangThai="HOAT_DONG"
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return {"success": True, "message": f"Tạo Voucher {code} thành công!", "voucher": v}

@router.put("/api/admin/voucher/{ma_voucher}", summary="Cập nhật trạng thái / thông tin Voucher")
def admin_update_voucher(ma_voucher: str, data: VoucherUpdate, db: Session = Depends(get_db)):
    v = db.query(models.Voucher).filter(models.Voucher.maVoucher == ma_voucher).first()
    if not v:
        raise HTTPException(status_code=404, detail="Không tìm thấy voucher!")

    if data.tenVoucher is not None: v.tenVoucher = data.tenVoucher.strip()
    if data.loaiGiam is not None: v.loaiGiam = data.loaiGiam
    if data.giaTriGiam is not None: v.giaTriGiam = data.giaTriGiam
    if data.donToiThieu is not None: v.donToiThieu = data.donToiThieu
    if data.soLuong is not None: v.soLuong = data.soLuong
    if data.trangThai is not None: v.trangThai = data.trangThai

    db.commit()
    return {"success": True, "message": f"Cập nhật Voucher {ma_voucher} thành công!"}

@router.delete("/api/admin/voucher/{ma_voucher}", summary="Xóa Voucher")
def admin_delete_voucher(ma_voucher: str, db: Session = Depends(get_db)):
    v = db.query(models.Voucher).filter(models.Voucher.maVoucher == ma_voucher).first()
    if not v:
        raise HTTPException(status_code=404, detail="Không tìm thấy voucher!")
    db.delete(v)
    db.commit()
    return {"success": True, "message": f"Đã xóa voucher {ma_voucher} thành công!"}

@router.get("/api/admin/voucher/kiem-tra/{ma_voucher}", summary="Kiểm tra & áp dụng mã voucher cho khách hàng")
def admin_check_voucher(ma_voucher: str, tongTien: float = Query(0.0), db: Session = Depends(get_db)):
    code = ma_voucher.strip().upper()
    v = db.query(models.Voucher).filter(models.Voucher.maVoucher == code).first()
    if not v:
        raise HTTPException(status_code=404, detail=f"Mã giảm giá '{code}' không tồn tại!")
    if v.trangThai != "HOAT_DONG":
        raise HTTPException(status_code=400, detail="Mã giảm giá này hiện đang tạm ngưng áp dụng!")
    if v.daDung >= v.soLuong:
        raise HTTPException(status_code=400, detail="Mã giảm giá đã hết lượt sử dụng!")
    if tongTien < v.donToiThieu:
        raise HTTPException(status_code=400, detail=f"Đơn hàng cần đạt tối thiểu {v.donToiThieu:,.0f}đ để áp dụng voucher này!")

    # Tính số tiền được giảm
    so_tien_giam = 0.0
    if v.loaiGiam == "PHAN_TRAM":
        so_tien_giam = (tongTien * v.giaTriGiam) / 100.0
    else:
        so_tien_giam = v.giaTriGiam
    
    so_tien_giam = min(so_tien_giam, tongTien)

    return {
        "valid": True,
        "maVoucher": v.maVoucher,
        "tenVoucher": v.tenVoucher,
        "loaiGiam": v.loaiGiam,
        "giaTriGiam": v.giaTriGiam,
        "soTienGiam": so_tien_giam,
        "tongTienSauGiam": max(0.0, tongTien - so_tien_giam)
    }

# --- CẤU HÌNH THAM SỐ AI & HỆ THỐNG ---

@router.get("/api/admin/cai-dat/ai", summary="Lấy cấu hình AI hiện tại")
def admin_get_ai_config(db: Session = Depends(get_db)):
    configs = {c.key: c.value for c in db.query(models.CauHinhHeThong).all()}
    
    provider = configs.get("ai_provider", "Gemini")
    model_name = configs.get("ai_model_name", "gemini-1.5-flash")
    temperature = float(configs.get("ai_temperature", "0.3"))
    system_prompt = configs.get("ai_system_prompt", "Bạn là Trợ lý AI FrogHippo Phone chuyên gia chẩn đoán sửa chữa điện thoại...")
    has_api_key = bool(os.getenv("GEMINI_API_KEY") or configs.get("ai_api_key"))

    return {
        "provider": provider,
        "modelName": model_name,
        "temperature": temperature,
        "systemPrompt": system_prompt,
        "laborFeeDefault": float(configs.get("labor_fee_default", "150000")),
        "hasApiKey": has_api_key,
        "status": "ONLINE" if has_api_key else "OFFLINE_FALLBACK"
    }

@router.post("/api/admin/cai-dat/ai", summary="Cập nhật cấu hình tham số AI & Hệ thống")
def admin_save_ai_config(req: CauHinhAIRequest, db: Session = Depends(get_db)):
    def set_config(k, v, mo_ta=""):
        c = db.query(models.CauHinhHeThong).filter(models.CauHinhHeThong.key == k).first()
        if not c:
            c = models.CauHinhHeThong(key=k, value=str(v), moTa=mo_ta)
            db.add(c)
        else:
            c.value = str(v)
            c.moTa = mo_ta

    set_config("ai_provider", req.provider, "Nhà cung cấp AI")
    set_config("ai_model_name", req.modelName, "Tên Model AI")
    set_config("ai_temperature", str(req.temperature), "Độ sáng tạo nhiệt độ AI")
    if req.systemPrompt:
        set_config("ai_system_prompt", req.systemPrompt, "System Prompt AI")
    if req.apiKey and req.apiKey.strip():
        set_config("ai_api_key", req.apiKey.strip(), "Khóa bí mật API Key")
        os.environ["GEMINI_API_KEY"] = req.apiKey.strip()
    if req.laborFeeDefault:
        set_config("labor_fee_default", str(req.laborFeeDefault), "Tiền công tiêu chuẩn")

    db.commit()
    return {"success": True, "message": "Đã lưu và kích hoạt cấu hình Tham Số AI & Hệ thống thành công!"}

@router.post("/api/admin/cai-dat/ai/test", summary="Kiểm tra kết nối và chạy thử chẩn đoán AI")
def admin_test_ai():
    try:
        res = ai_service.diagnose_and_estimate_repair("Màn hình sọc xanh, liệt cảm ứng góc dưới", "iPhone 13 Pro")
        return {
            "success": True,
            "message": "Kết nối dịch vụ AI hoạt động hoàn hảo!",
            "testResult": res
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Kiểm tra AI thất bại: {str(e)}"
        }

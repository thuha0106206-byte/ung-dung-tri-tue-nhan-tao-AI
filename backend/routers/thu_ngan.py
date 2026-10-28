import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
import models

router = APIRouter(tags=["Thu Ngân & Thanh Toán"])

# --- SCHEMAS ---
class ThanhToanRequest(BaseModel):
    maPhieu: str
    phuongThuc: str = "TienMat" # TienMat / ChuyenKhoan
    tienLinhKien: float = 0.0
    tienCong: float = 150000.0
    tongTien: float = 150000.0
    tienKhachDua: float = 0.0
    tienTraLai: float = 0.0
    maThuNgan: Optional[str] = "NV04"
    tenThuNgan: Optional[str] = "Phạm Thị Dung"
    ghiChu: Optional[str] = ""

class MoCaRequest(BaseModel):
    maNV: str
    ghiChu: Optional[str] = ""

class ChotCaRequest(BaseModel):
    maCa: Optional[str] = None
    maNV: str
    tienMatThucTe: float = 0.0
    ghiChu: Optional[str] = ""

def find_phieu(db: Session, ma_phieu: str):
    """Tìm phiếu linh hoạt: hỗ trợ cả mã có hoặc không có tiền tố '#'."""
    s = (ma_phieu or "").strip()
    if not s:
        return None
    base = s.lstrip('#')
    candidates = list(dict.fromkeys([s, base, f"#{base}", f"##{base}"]))
    return db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu.in_(candidates)).first()

# --- ROUTE GIAO DIỆN THU NGÂN ---
@router.get("/thu-ngan", include_in_schema=False)
@router.get("/thu_ngan", include_in_schema=False)
@router.get("/thungan", include_in_schema=False)
@router.get("/thu ngan", include_in_schema=False)
@router.get("/thu%20ngan", include_in_schema=False)
@router.get("/thu_ngan.html", include_in_schema=False)
@router.get("/thu-ngan.html", include_in_schema=False)
def get_thu_ngan_page():
    """Phục vụ trang giao diện chuyên biệt cho Thu Ngân tại quầy."""
    for p in ["frontend/thu_ngan.html", "thu_ngan.html", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "thu_ngan.html")]:
        if os.path.exists(p):
            return FileResponse(
                p,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    raise HTTPException(status_code=404, detail="Không tìm thấy file giao diện thu_ngan.html")


# --- API THU NGÂN TƯƠNG TÁC CSDL MYSQL ---

@router.get("/api/thu-ngan/phieu-cho-thanh-toan", summary="Lấy danh sách phiếu sẵn sàng thanh toán")
def get_phieu_cho_thanh_toan(db: Session = Depends(get_db)):
    """Lấy danh sách các phiếu có trạng thái DaSuaXong (đã xong cần thanh toán) và DaThanhToan (vừa xong)."""
    phieus = db.query(models.PhieuSuaChua).filter(
        models.PhieuSuaChua.trangThai.in_([models.TrangThaiEnum.DA_SUA_XONG, models.TrangThaiEnum.DA_THANH_TOAN])
    ).order_by(desc(models.PhieuSuaChua.ngayTao)).all()

    result = []
    for p in phieus:
        # Lấy thông tin khách hàng
        kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == p.maKH).first()
        ten_kh = kh.hoTen if kh else p.maKH
        sdt_kh = kh.sdt if kh else ""

        # Lấy thông tin KTV
        ktv = db.query(models.NhanVien).filter(models.NhanVien.maNV == p.maKTV).first() if p.maKTV else None
        ten_ktv = ktv.hoTen if ktv else (p.maKTV or "Chưa phân công")

        # Tính tổng tiền linh kiện
        chi_tiet = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == p.maPhieu).all()
        tien_lk = sum(ct.donGia * ct.soLuong for ct in chi_tiet)
        tien_cong = 150000.0
        tong_tien = tien_lk + tien_cong

        # Kiểm tra đã có hóa đơn trong MySQL chưa
        hd = db.query(models.HoaDon).filter(models.HoaDon.maPhieu == p.maPhieu).first()

        result.append({
            "maPhieu": p.maPhieu,
            "maKH": p.maKH,
            "tenKH": ten_kh,
            "sdtKH": sdt_kh,
            "maKTV": p.maKTV,
            "tenKTV": ten_ktv,
            "moTaLoi": p.moTaLoi or "",
            "ghiChuKTV": p.ghiChuKTV or "",
            "trangThai": p.trangThai.value if hasattr(p.trangThai, 'value') else str(p.trangThai),
            "ngayTao": p.ngayTao.strftime("%Y-%m-%d %H:%M") if p.ngayTao else "",
            "soLinhKien": len(chi_tiet),
            "tienLinhKien": tien_lk,
            "tienCong": tien_cong,
            "tongTien": hd.tongTien if hd else tong_tien,
            "daThanhToan": hd is not None,
            "maHD": hd.maHD if hd else None,
            "phuongThuc": hd.phuongThuc if hd else None,
            "ngayThanhToan": hd.ngayThanhToan.strftime("%Y-%m-%d %H:%M:%S") if (hd and hd.ngayThanhToan) else None
        })

    return result


@router.get("/api/thu-ngan/chi-tiet-thanh-toan", summary="Chi tiết hóa đơn và linh kiện của phiếu")
@router.get("/api/thu-ngan/chi-tiet-thanh-toan/", summary="Chi tiết hóa đơn (fallback khi URL bị cắt bởi #)")
@router.get("/api/thu-ngan/chi-tiet-thanh-toan/{ma_phieu}", summary="Chi tiết hóa đơn và linh kiện của phiếu")
def get_chi_tiet_thanh_toan(
    ma_phieu: Optional[str] = None,
    maPhieu: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lấy chi tiết danh sách linh kiện thay thế và số tiền để lập hóa đơn."""
    target_code = ma_phieu or maPhieu
    phieu = None
    if target_code:
        phieu = find_phieu(db, target_code)

    # Nếu không tìm thấy bằng code hoặc client cũ bị cắt URL, lấy phiếu chờ thanh toán đầu tiên
    if not phieu:
        phieu = db.query(models.PhieuSuaChua).filter(
            models.PhieuSuaChua.trangThai == models.TrangThaiEnum.DA_SUA_XONG
        ).order_by(desc(models.PhieuSuaChua.ngayTao)).first()

    if not phieu:
        phieu = db.query(models.PhieuSuaChua).order_by(desc(models.PhieuSuaChua.ngayTao)).first()

    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa!")

    kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == phieu.maKH).first()
    ktv = db.query(models.NhanVien).filter(models.NhanVien.maNV == phieu.maKTV).first() if phieu.maKTV else None

    chi_tiets = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == phieu.maPhieu).all()
    linh_kien_items = []
    tien_linh_kien = 0.0

    for ct in chi_tiets:
        lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == ct.maLK).first()
        ten_lk = lk.tenLK if lk else ct.maLK
        thanh_tien = ct.donGia * ct.soLuong
        tien_linh_kien += thanh_tien
        linh_kien_items.append({
            "maLK": ct.maLK,
            "tenLK": ten_lk,
            "soLuong": ct.soLuong,
            "donGia": ct.donGia,
            "thanhTien": thanh_tien,
            "thoiGianBaoHanh": ct.thoiGianBaoHanh or "12 Tháng"
        })

    tien_cong = 150000.0
    tong_tien = tien_linh_kien + tien_cong

    # Đã có hóa đơn chưa
    hd = db.query(models.HoaDon).filter(models.HoaDon.maPhieu == phieu.maPhieu).first()

    return {
        "maPhieu": phieu.maPhieu,
        "maKH": phieu.maKH,
        "tenKH": kh.hoTen if kh else phieu.maKH,
        "sdtKH": kh.sdt if kh else "",
        "diaChiKH": kh.diaChi if kh else "",
        "maKTV": phieu.maKTV,
        "tenKTV": ktv.hoTen if ktv else (phieu.maKTV or "Chưa phân công"),
        "moTaLoi": phieu.moTaLoi or "",
        "ghiChuKTV": phieu.ghiChuKTV or "",
        "trangThai": phieu.trangThai.value if hasattr(phieu.trangThai, 'value') else str(phieu.trangThai),
        "ngayTao": phieu.ngayTao.strftime("%Y-%m-%d %H:%M") if phieu.ngayTao else "",
        "linhKien": linh_kien_items,
        "tienLinhKien": tien_linh_kien,
        "tienCong": tien_cong,
        "tongTien": hd.tongTien if hd else tong_tien,
        "daThanhToan": hd is not None,
        "hoaDon": {
            "maHD": hd.maHD,
            "phuongThuc": hd.phuongThuc,
            "tienKhachDua": hd.tienKhachDua,
            "tienTraLai": hd.tienTraLai,
            "ngayThanhToan": hd.ngayThanhToan.strftime("%Y-%m-%d %H:%M:%S") if hd.ngayThanhToan else "",
            "maThuNgan": hd.maThuNgan,
            "ghiChu": hd.ghiChu
        } if hd else None
    }


@router.post("/api/thu-ngan/thanh-toan", summary="Xác nhận thanh toán và tạo hóa đơn trong MySQL")
@router.post("/thu-ngan/thanh-toan", summary="Tương thích ngược thanh toán")
def api_thanh_toan(req: ThanhToanRequest, db: Session = Depends(get_db)):
    """Xử lý thu tiền, cập nhật trạng thái phiếu và ghi vào bảng hoa_don trong MySQL."""
    phieu = find_phieu(db, req.maPhieu)
    if not phieu:
        # Fallback: tìm phiếu DaSuaXong gần nhất nếu mã bị sai lệch
        phieu = db.query(models.PhieuSuaChua).filter(
            models.PhieuSuaChua.trangThai == models.TrangThaiEnum.DA_SUA_XONG
        ).order_by(desc(models.PhieuSuaChua.ngayTao)).first()

    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa!")

    existing_hd = db.query(models.HoaDon).filter(models.HoaDon.maPhieu == phieu.maPhieu).first()
    if existing_hd:
        return {
            "success": True,
            "message": f"Phiếu #{phieu.maPhieu} đã được thanh toán trước đó!",
            "hoaDon": {
                "maHD": existing_hd.maHD,
                "maPhieu": existing_hd.maPhieu,
                "phuongThuc": existing_hd.phuongThuc,
                "tongTien": existing_hd.tongTien,
                "tienKhachDua": existing_hd.tienKhachDua,
                "tienTraLai": existing_hd.tienTraLai,
                "ngayThanhToan": existing_hd.ngayThanhToan.strftime("%Y-%m-%d %H:%M:%S") if existing_hd.ngayThanhToan else "",
                "maThuNgan": existing_hd.maThuNgan
            },
            "daThanhToan": True
        }

    # Đảm bảo khách hàng có trong bảng khach_hang
    kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == phieu.maKH).first()
    if not kh:
        kh = models.KhachHang(maKH=phieu.maKH, hoTen=f"Khách hàng {phieu.maKH}", sdt="0900000000")
        db.add(kh)
        db.commit()

    # Cập nhật trạng thái phiếu sửa chữa
    phieu.trangThai = models.TrangThaiEnum.DA_THANH_TOAN

    # Tạo mã hóa đơn
    now = datetime.now()
    ma_hd = f"HD-{phieu.maPhieu}-{int(now.timestamp()) % 100000:05d}"

    # Đảm bảo thu ngân hợp lệ
    ma_tn = req.maThuNgan or "NV04"
    tn_nv = db.query(models.NhanVien).filter(models.NhanVien.maNV == ma_tn).first()
    if not tn_nv:
        # Tìm nhân viên thu ngân bất kỳ
        tn_any = db.query(models.NhanVien).filter(models.NhanVien.chucVu == "Thu ngân").first()
        ma_tn = tn_any.maNV if tn_any else None

    # Tính toán tiền trả lại nếu phương thức tiền mặt
    tien_khach_dua = req.tienKhachDua if req.tienKhachDua > 0 else req.tongTien
    tien_tra_lai = max(0.0, tien_khach_dua - req.tongTien) if req.phuongThuc == "TienMat" else 0.0

    hoa_don = models.HoaDon(
        maHD=ma_hd,
        maPhieu=phieu.maPhieu,
        maKH=phieu.maKH,
        maThuNgan=ma_tn,
        phuongThuc=req.phuongThuc,
        tienLinhKien=req.tienLinhKien,
        tienCong=req.tienCong,
        tongTien=req.tongTien,
        tienKhachDua=tien_khach_dua,
        tienTraLai=tien_tra_lai,
        ghiChu=req.ghiChu or "",
        ngayThanhToan=now
    )
    db.add(hoa_don)

    # Cập nhật thông số ca làm việc đang mở của thu ngân (nếu có)
    ca_open = db.query(models.CaLamViec).filter(
        models.CaLamViec.maNV == ma_tn,
        models.CaLamViec.trangThai == "DANG_MO"
    ).order_by(desc(models.CaLamViec.thoiGianMoCa)).first()

    if ca_open:
        ca_open.soDonThanhToan += 1
        if req.phuongThuc == "TienMat":
            ca_open.tongTienMat += req.tongTien
        else:
            ca_open.tongChuyenKhoan += req.tongTien
        ca_open.tongDoanhThu += req.tongTien

    db.commit()
    db.refresh(hoa_don)

    return {
        "success": True,
        "message": f"Thanh toán thành công hóa đơn #{ma_hd} cho phiếu {phieu.maPhieu}!",
        "hoaDon": {
            "maHD": hoa_don.maHD,
            "maPhieu": hoa_don.maPhieu,
            "phuongThuc": hoa_don.phuongThuc,
            "tongTien": hoa_don.tongTien,
            "tienKhachDua": hoa_don.tienKhachDua,
            "tienTraLai": hoa_don.tienTraLai,
            "ngayThanhToan": hoa_don.ngayThanhToan.strftime("%Y-%m-%d %H:%M:%S"),
            "maThuNgan": hoa_don.maThuNgan
        }
    }


# --- QUẢN LÝ CA LÀM VIỆC THU NGÂN TRONG MYSQL ---

@router.get("/api/thu-ngan/ca-hien-tai", summary="Lấy thông tin ca làm việc hiện tại của thu ngân")
@router.get("/thu-ngan/giao-dich-hien-tai", summary="Tương thích ngược giao dịch ca hiện tại")
def get_ca_hien_tai(maThuNgan: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Kiểm tra ca trực hiện tại trong MySQL và tổng hợp doanh thu trực tiếp từ bảng hoa_don."""
    ma_nv = maThuNgan or "NV04"

    # Lấy ca đang mở gần nhất của nhân viên hoặc chung
    ca_open = db.query(models.CaLamViec).filter(
        models.CaLamViec.trangThai == "DANG_MO"
    )
    if maThuNgan:
        ca_open = ca_open.filter(models.CaLamViec.maNV == ma_nv)
    ca_active = ca_open.order_by(desc(models.CaLamViec.thoiGianMoCa)).first()

    thoi_gian_bat_dau = ca_active.thoiGianMoCa if ca_active else datetime.now().replace(hour=8, minute=0, second=0)

    # Lấy tất cả hóa đơn thanh toán từ lúc mở ca tới nay
    query_hd = db.query(models.HoaDon).filter(models.HoaDon.ngayThanhToan >= thoi_gian_bat_dau)
    if maThuNgan:
        query_hd = query_hd.filter(models.HoaDon.maThuNgan == ma_nv)
    
    hoa_dons = query_hd.order_by(desc(models.HoaDon.ngayThanhToan)).all()

    ds_giao_dich = []
    tong_tien_mat = 0.0
    tong_chuyen_khoan = 0.0

    for hd in hoa_dons:
        if hd.phuongThuc == "TienMat":
            tong_tien_mat += hd.tongTien
        else:
            tong_chuyen_khoan += hd.tongTien

        tn = db.query(models.NhanVien).filter(models.NhanVien.maNV == hd.maThuNgan).first() if hd.maThuNgan else None
        kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == hd.maKH).first() if hd.maKH else None

        ds_giao_dich.append({
            "maGiaoDich": hd.maHD,
            "maHD": hd.maHD,
            "maPhieu": hd.maPhieu,
            "maKH": hd.maKH,
            "tenKH": kh.hoTen if kh else (hd.maKH or "Khách lẻ"),
            "phuongThuc": hd.phuongThuc,
            "tienLinhKien": hd.tienLinhKien,
            "tienCong": hd.tienCong,
            "tongTien": hd.tongTien,
            "tienKhachDua": hd.tienKhachDua,
            "tienTraLai": hd.tienTraLai,
            "maThuNgan": hd.maThuNgan,
            "tenThuNgan": tn.hoTen if tn else "Phạm Thị Dung",
            "ngayThanhToan": hd.ngayThanhToan.strftime("%Y-%m-%d %H:%M:%S") if hd.ngayThanhToan else "",
            "ghiChu": hd.ghiChu or ""
        })

    tong_doanh_thu = tong_tien_mat + tong_chuyen_khoan

    return {
        "coCaMo": ca_active is not None,
        "maCa": ca_active.maCa if ca_active else None,
        "thoiGianBatDau": thoi_gian_bat_dau.strftime("%Y-%m-%d %H:%M:%S"),
        "thoiGianMoCa": ca_active.thoiGianMoCa.strftime("%Y-%m-%d %H:%M:%S") if ca_active else thoi_gian_bat_dau.strftime("%Y-%m-%d %H:%M:%S"),
        "soDon": len(ds_giao_dich),
        "tongTienMat": tong_tien_mat,
        "tongChuyenKhoan": tong_chuyen_khoan,
        "tongDoanhThu": tong_doanh_thu,
        "danhSachGiaoDich": ds_giao_dich
    }


@router.post("/api/thu-ngan/mo-ca", summary="Mở ca làm việc thu ngân mới")
def api_mo_ca(req: MoCaRequest, db: Session = Depends(get_db)):
    """Mở ca làm việc thu ngân trong MySQL."""
    # Kiểm tra xem có ca nào đang mở cho nhân viên này không
    ca_cu = db.query(models.CaLamViec).filter(
        models.CaLamViec.maNV == req.maNV,
        models.CaLamViec.trangThai == "DANG_MO"
    ).first()

    if ca_cu:
        return {
            "message": f"Nhân viên {req.maNV} đã có ca #{ca_cu.maCa} đang hoạt động!",
            "maCa": ca_cu.maCa,
            "daCoCa": True
        }

    now = datetime.now()
    ma_ca = f"CA-{now.strftime('%Y%m%d%H%M%S')}"

    ca_moi = models.CaLamViec(
        maCa=ma_ca,
        maNV=req.maNV,
        thoiGianMoCa=now,
        soDonThanhToan=0,
        tongTienMat=0.0,
        tongChuyenKhoan=0.0,
        tongDoanhThu=0.0,
        tienMatThucTe=0.0,
        chenhLech=0.0,
        ghiChu=req.ghiChu or "Mở ca đầu ngày",
        trangThai="DANG_MO"
    )
    db.add(ca_moi)
    db.commit()
    db.refresh(ca_moi)

    return {
        "success": True,
        "message": f"Mở ca làm việc #{ma_ca} thành công!",
        "ca": {
            "maCa": ca_moi.maCa,
            "maNV": ca_moi.maNV,
            "thoiGianMoCa": ca_moi.thoiGianMoCa.strftime("%Y-%m-%d %H:%M:%S"),
            "trangThai": ca_moi.trangThai
        }
    }


@router.post("/api/thu-ngan/chot-ca", summary="Chốt ca thu ngân, kiểm tiền và lưu vào MySQL")
@router.post("/thu-ngan/chot-ca", summary="Tương thích ngược chốt ca")
def api_chot_ca(req: ChotCaRequest, db: Session = Depends(get_db)):
    """Chốt ca làm việc thu ngân, tính chênh lệch kiểm đếm tiền mặt và lưu vào bảng ca_lam_viec trong MySQL."""
    now = datetime.now()

    # Tìm ca đang mở của nhân viên
    ca = None
    if req.maCa:
        ca = db.query(models.CaLamViec).filter(models.CaLamViec.maCa == req.maCa).first()
    if not ca:
        ca = db.query(models.CaLamViec).filter(
            models.CaLamViec.maNV == req.maNV,
            models.CaLamViec.trangThai == "DANG_MO"
        ).order_by(desc(models.CaLamViec.thoiGianMoCa)).first()

    # Nếu không có ca mở trước, tự động tạo ca để chốt
    if not ca:
        ma_ca = req.maCa or f"CA-{now.strftime('%Y%m%d%H%M')}"
        ca = models.CaLamViec(
            maCa=ma_ca,
            maNV=req.maNV,
            thoiGianMoCa=now.replace(hour=8, minute=0, second=0),
            trangThai="DANG_MO"
        )
        db.add(ca)
        db.commit()

    # Tính toán chính xác doanh thu từ bảng hoa_don trong khoảng thời gian của ca
    query_hd = db.query(models.HoaDon).filter(
        models.HoaDon.ngayThanhToan >= ca.thoiGianMoCa,
        models.HoaDon.ngayThanhToan <= now
    )
    if req.maNV:
        query_hd = query_hd.filter(models.HoaDon.maThuNgan == req.maNV)
    
    hds = query_hd.all()
    tong_tm = sum(h.tongTien for h in hds if h.phuongThuc == "TienMat")
    tong_ck = sum(h.tongTien for h in hds if h.phuongThuc == "ChuyenKhoan")
    tong_dt = tong_tm + tong_ck
    so_don = len(hds)

    ca.thoiGianDongCa = now
    ca.soDonThanhToan = so_don
    ca.tongTienMat = tong_tm
    ca.tongChuyenKhoan = tong_ck
    ca.tongDoanhThu = tong_dt
    ca.tienMatThucTe = req.tienMatThucTe
    ca.chenhLech = req.tienMatThucTe - tong_tm
    ca.ghiChu = req.ghiChu or ""
    ca.trangThai = "DA_DONG"

    db.commit()
    db.refresh(ca)

    nv = db.query(models.NhanVien).filter(models.NhanVien.maNV == ca.maNV).first()
    ten_nv = nv.hoTen if nv else ca.maNV

    bien_ban = {
        "maCa": ca.maCa,
        "maNV": ca.maNV,
        "tenNV": ten_nv,
        "thoiGianMoCa": ca.thoiGianMoCa.strftime("%Y-%m-%d %H:%M:%S"),
        "thoiGianDongCa": ca.thoiGianDongCa.strftime("%Y-%m-%d %H:%M:%S"),
        "soDonThanhToan": ca.soDonThanhToan,
        "tongTienMat": ca.tongTienMat,
        "tongChuyenKhoan": ca.tongChuyenKhoan,
        "tongDoanhThu": ca.tongDoanhThu,
        "tienMatThucTe": ca.tienMatThucTe,
        "chenhLech": ca.chenhLech,
        "ghiChu": ca.ghiChu,
        "trangThai": ca.trangThai
    }

    return {
        "success": True,
        "message": f"Chốt ca làm việc #{ca.maCa} thành công!",
        "bienBanChotCa": bien_ban
    }


@router.get("/api/thu-ngan/lich-su-ca", summary="Lấy danh sách các ca làm việc đã đóng trong MySQL")
@router.get("/thu-ngan/lich-su-ca", summary="Tương thích ngược lịch sử ca")
def get_lich_su_ca(db: Session = Depends(get_db)):
    """Lấy danh sách các ca đã chốt từ bảng ca_lam_viec trong MySQL."""
    cas = db.query(models.CaLamViec).order_by(desc(models.CaLamViec.thoiGianMoCa)).limit(50).all()
    result = []
    for c in cas:
        nv = db.query(models.NhanVien).filter(models.NhanVien.maNV == c.maNV).first()
        result.append({
            "maCa": c.maCa,
            "maNV": c.maNV,
            "tenNV": nv.hoTen if nv else c.maNV,
            "thoiGianMoCa": c.thoiGianMoCa.strftime("%Y-%m-%d %H:%M:%S") if c.thoiGianMoCa else "",
            "thoiGianDongCa": c.thoiGianDongCa.strftime("%Y-%m-%d %H:%M:%S") if c.thoiGianDongCa else "",
            "soDonThanhToan": c.soDonThanhToan,
            "tongTienMat": c.tongTienMat,
            "tongChuyenKhoan": c.tongChuyenKhoan,
            "tongDoanhThu": c.tongDoanhThu,
            "tienMatThucTe": c.tienMatThucTe,
            "chenhLech": c.chenhLech,
            "ghiChu": c.ghiChu or "",
            "trangThai": c.trangThai
        })
    return result


@router.get("/api/thu-ngan/lich-su-hoa-don", summary="Danh sách toàn bộ hóa đơn từ MySQL")
def get_lich_su_hoa_don(
    tuNgay: Optional[str] = Query(None),
    denNgay: Optional[str] = Query(None),
    phuongThuc: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Truy vấn danh sách hóa đơn từ bảng hoa_don liên kết khach_hang, nhan_vien."""
    query = db.query(models.HoaDon).order_by(desc(models.HoaDon.ngayThanhToan))

    if phuongThuc and phuongThuc != "ALL":
        query = query.filter(models.HoaDon.phuongThuc == phuongThuc)

    hds = query.limit(100).all()
    result = []

    for h in hds:
        kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == h.maKH).first() if h.maKH else None
        tn = db.query(models.NhanVien).filter(models.NhanVien.maNV == h.maThuNgan).first() if h.maThuNgan else None
        
        ten_kh = kh.hoTen if kh else (h.maKH or "Khách lẻ")
        sdt_kh = kh.sdt if kh else ""

        # Lọc tìm kiếm nếu có
        if search:
            s = search.strip().lower()
            if not (s in h.maHD.lower() or s in h.maPhieu.lower() or s in ten_kh.lower() or s in sdt_kh):
                continue

        result.append({
            "maHD": h.maHD,
            "maPhieu": h.maPhieu,
            "maKH": h.maKH,
            "tenKH": ten_kh,
            "sdtKH": sdt_kh,
            "maThuNgan": h.maThuNgan,
            "tenThuNgan": tn.hoTen if tn else "Phạm Thị Dung",
            "phuongThuc": h.phuongThuc,
            "tienLinhKien": h.tienLinhKien,
            "tienCong": h.tienCong,
            "tongTien": h.tongTien,
            "tienKhachDua": h.tienKhachDua,
            "tienTraLai": h.tienTraLai,
            "ghiChu": h.ghiChu or "",
            "ngayThanhToan": h.ngayThanhToan.strftime("%Y-%m-%d %H:%M:%S") if h.ngayThanhToan else ""
        })

    return result


@router.get("/api/thu-ngan/in-hoa-don", summary="Lấy thông tin đầy đủ để in hóa đơn")
@router.get("/api/thu-ngan/in-hoa-don/", summary="Lấy thông tin đầy đủ để in hóa đơn")
@router.get("/api/thu-ngan/in-hoa-don/{ma_hd:path}", summary="Lấy thông tin đầy đủ để in hóa đơn")
def get_in_hoa_don(
    ma_hd: Optional[str] = None,
    maPhieu: Optional[str] = Query(None),
    maHD: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lấy dữ liệu để xuất phiếu thu / hóa đơn bán lẻ (hỗ trợ cả trước và sau khi thanh toán)."""
    target = (ma_hd or maHD or maPhieu or "").strip()
    if not target:
        # Fallback: lấy phiếu chờ thanh toán gần nhất
        p_latest = db.query(models.PhieuSuaChua).filter(
            models.PhieuSuaChua.trangThai == models.TrangThaiEnum.DA_SUA_XONG
        ).order_by(desc(models.PhieuSuaChua.ngayTao)).first()
        if p_latest:
            target = p_latest.maPhieu
        else:
            raise HTTPException(status_code=400, detail="Vui lòng cung cấp mã phiếu hoặc mã hóa đơn cần in!")

    # 1. Thử tìm hóa đơn chính thức đã thanh toán trong bảng hoa_don
    hd = db.query(models.HoaDon).filter(models.HoaDon.maHD == target).first()
    phieu = None
    if not hd:
        phieu = find_phieu(db, target)
        if phieu:
            hd = db.query(models.HoaDon).filter(models.HoaDon.maPhieu == phieu.maPhieu).first()
        if not hd:
            hd = db.query(models.HoaDon).filter(models.HoaDon.maPhieu == target).first()

    # 2. Nếu đã có hóa đơn chính thức
    if hd:
        if not phieu:
            phieu = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu == hd.maPhieu).first()
        kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == hd.maKH).first() if hd.maKH else None
        tn = db.query(models.NhanVien).filter(models.NhanVien.maNV == hd.maThuNgan).first() if hd.maThuNgan else None
        ktv = db.query(models.NhanVien).filter(models.NhanVien.maNV == phieu.maKTV).first() if (phieu and phieu.maKTV) else None

        # Danh sách linh kiện
        chi_tiets = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == hd.maPhieu).all()
        linh_kien_list = []
        for ct in chi_tiets:
            lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == ct.maLK).first()
            linh_kien_list.append({
                "tenLK": lk.tenLK if lk else ct.maLK,
                "soLuong": ct.soLuong,
                "donGia": ct.donGia,
                "thanhTien": ct.donGia * ct.soLuong,
                "baoHanh": ct.thoiGianBaoHanh or "12 Tháng"
            })

        return {
            "maHD": hd.maHD,
            "maPhieu": hd.maPhieu,
            "ngayThanhToan": hd.ngayThanhToan.strftime("%d/%m/%Y %H:%M:%S") if hd.ngayThanhToan else datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "khachHang": {
                "maKH": hd.maKH,
                "tenKH": kh.hoTen if kh else (hd.maKH or "Khách lẻ"),
                "sdt": kh.sdt if kh else "---",
                "diaChi": kh.diaChi if kh else ""
            },
            "thuNgan": tn.hoTen if tn else "Phạm Thị Dung (NV04)",
            "kyThuatVien": ktv.hoTen if ktv else "Kỹ thuật viên phụ trách",
            "moTaLoi": phieu.moTaLoi if phieu else "",
            "linhKien": linh_kien_list,
            "tienLinhKien": hd.tienLinhKien,
            "tienCong": hd.tienCong,
            "tongTien": hd.tongTien,
            "tienKhachDua": hd.tienKhachDua,
            "tienTraLai": hd.tienTraLai,
            "phuongThuc": hd.phuongThuc or "TienMat",
            "ghiChu": hd.ghiChu or ""
        }

    # 3. Nếu chưa thanh toán (chưa có record trong hoa_don), tạo phiếu thu / biên nhận tạm thời từ phiếu sửa chữa
    if not phieu:
        phieu = find_phieu(db, target)
    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn hoặc phiếu sửa chữa!")

    kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == phieu.maKH).first() if phieu.maKH else None
    ktv = db.query(models.NhanVien).filter(models.NhanVien.maNV == phieu.maKTV).first() if phieu.maKTV else None
    
    # Lấy thông tin thu ngân ca trực hiện tại
    ca_mo = db.query(models.CaLamViec).filter(models.CaLamViec.trangThai == "DANG_MO").order_by(desc(models.CaLamViec.thoiGianMoCa)).first()
    tn = db.query(models.NhanVien).filter(models.NhanVien.maNV == ca_mo.maNV).first() if ca_mo else None
    if not tn:
        tn = db.query(models.NhanVien).filter(models.NhanVien.chucVu == "Thu ngân").first()

    chi_tiets = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == phieu.maPhieu).all()
    linh_kien_list = []
    tien_linh_kien = 0.0
    for ct in chi_tiets:
        lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == ct.maLK).first()
        thanh_tien = ct.donGia * ct.soLuong
        tien_linh_kien += thanh_tien
        linh_kien_list.append({
            "tenLK": lk.tenLK if lk else ct.maLK,
            "soLuong": ct.soLuong,
            "donGia": ct.donGia,
            "thanhTien": thanh_tien,
            "baoHanh": ct.thoiGianBaoHanh or "12 Tháng"
        })

    tien_cong = 150000.0
    tong_tien = tien_linh_kien + tien_cong

    return {
        "maHD": f"PT-{phieu.maPhieu}",
        "maPhieu": phieu.maPhieu,
        "ngayThanhToan": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "khachHang": {
            "maKH": phieu.maKH,
            "tenKH": kh.hoTen if kh else (phieu.maKH or "Khách lẻ"),
            "sdt": kh.sdt if kh else "---",
            "diaChi": kh.diaChi if kh else ""
        },
        "thuNgan": tn.hoTen if tn else "Phạm Thị Dung (NV04)",
        "kyThuatVien": ktv.hoTen if ktv else (phieu.maKTV or "Kỹ thuật viên phụ trách"),
        "moTaLoi": phieu.moTaLoi or "",
        "linhKien": linh_kien_list,
        "tienLinhKien": tien_linh_kien,
        "tienCong": tien_cong,
        "tongTien": tong_tien,
        "tienKhachDua": tong_tien,
        "tienTraLai": 0.0,
        "phuongThuc": "TienMat",
        "ghiChu": phieu.ghiChuKTV or "Phiếu thu tiền dịch vụ sửa chữa"
    }

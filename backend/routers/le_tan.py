import os
import re
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
import models
import ai_service

router = APIRouter(tags=["Lễ Tân"])

SHIFT_DATA_FILE = "shifts_data.json"

def load_shift_data():
    if os.path.exists(SHIFT_DATA_FILE):
        try:
            with open(SHIFT_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"thanh_toan": [], "chot_ca": [], "thong_bao_khach": []}

def save_shift_data(data):
    with open(SHIFT_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- SCHEMAS ---
class PhieuSuaCreate(BaseModel):
    maPhieu: Optional[str] = None
    maKH: Optional[str] = None
    hoTenKH: Optional[str] = None
    sdtKH: Optional[str] = None
    emailKH: Optional[str] = None
    maKTV: Optional[str] = None
    moTaLoi: Optional[str] = None
    ghiChuKTV: Optional[str] = None
    # Hỗ trợ nhận body gửi tin nhắn nếu client cũ bị cắt URL do dấu '#'
    channel: Optional[str] = None
    noiDung: Optional[str] = None
    nguoiGui: Optional[str] = None
    loai: Optional[str] = None

class GuiTinNhanRequest(BaseModel):
    maPhieu: Optional[str] = None
    channel: Optional[str] = "Gmail"
    kenh: Optional[str] = None
    noiDung: Optional[str] = None
    nguoiGui: Optional[str] = "Lễ tân"
    loai: Optional[str] = "tien_do"  # tien_do | dat_coc | hoan_thanh
    emailKhach: Optional[str] = None
    sdtKhach: Optional[str] = None

class ThuCocRequest(BaseModel):
    phuongThuc: str = "TienMat"
    tienKhachDua: Optional[float] = 0.0
    nguoiThu: Optional[str] = "Lễ tân"

class QuyetToanRequest(BaseModel):
    phuongThuc: str = "TienMat"
    tienKhachDua: Optional[float] = 0.0
    maThuNgan: Optional[str] = "NV04"
    tenThuNgan: Optional[str] = "Phạm Thị Dung"
    ghiChu: Optional[str] = ""

class ChatbotRequest(BaseModel):
    message: str
    maPhieu: Optional[str] = None
    fileData: Optional[str] = None
    fileName: Optional[str] = None
    fileMimeType: Optional[str] = None

class AIMauTinNhanRequest(BaseModel):
    maPhieu: str
    loai: str = "tiep_nhan"  # tiep_nhan | dat_coc | hoan_thanh
    channel: str = "Gmail"

def find_phieu(db: Session, ma_phieu: str):
    """Tìm phiếu linh hoạt: hỗ trợ cả mã có hoặc không có tiền tố '#'."""
    s = (ma_phieu or "").strip()
    if not s:
        return None
    base = s.lstrip('#')
    candidates = list(dict.fromkeys([s, base, f"#{base}"]))
    return db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu.in_(candidates)).first()

def clean_customer_message(text: str) -> str:
    """Loại bỏ câu dẫn của AI ('Dưới đây là...'), dấu phân cách markdown và ghi chú cuối,
    để Lễ tân có thể gửi thẳng nội dung cho khách."""
    import re
    if not text:
        return ""
    lines = [l.rstrip() for l in str(text).replace("\r\n", "\n").split("\n")]
    preamble = re.compile(r"(dưới đây là|sau đây là|đây là (mẫu|tin nhắn|nội dung)|chắc chắn rồi|mẫu tin nhắn)", re.I)
    separator = re.compile(r"^\s*([*\-_=]{3,}|`{3}\w*)\s*$")
    heading = re.compile(r"^\s*#{1,6}\s+")
    # Bỏ câu dẫn, tiêu đề markdown và dòng phân cách ở đầu
    while lines and (not lines[0].strip() or preamble.search(lines[0]) or separator.match(lines[0]) or heading.match(lines[0])):
        lines.pop(0)
    # Cắt phần ghi chú/giải thích của AI phía sau dấu phân cách
    for i, l in enumerate(lines):
        if separator.match(l) and i > 0:
            lines = lines[:i]
            break
    lines = [heading.sub("", l) for l in lines]
    out = "\n".join(lines).strip()
    out = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", out)  # SMS/Zalo không hiển thị markdown
    out = re.sub(r"#{2,}(?=[A-Za-z0-9])", "#", out)  # "##PS09" -> "#PS09"
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out or str(text).strip()


# --- ROUTE GIAO DIỆN LỄ TÂN ---
@router.get("/le-tan", include_in_schema=False)
@router.get("/le_tan.html", include_in_schema=False)
def get_le_tan_page():
    """Phục vụ trang giao diện riêng cho Lễ Tân với header chống cache tuyệt đối."""
    for p in ["frontend/le_tan.html", "le_tan.html", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "le_tan.html")]:
        if os.path.exists(p):
            return FileResponse(
                p,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    raise HTTPException(status_code=404, detail="Không tìm thấy file giao diện le_tan.html")

# --- API LỄ TÂN ---
@router.get("/nhan-vien/danh-sach-ktv", summary="Lấy danh sách KTV phục vụ tiếp nhận phiếu")
def get_danh_sach_ktv(db: Session = Depends(get_db)):
    ktvs = db.query(models.NhanVien).filter(
        models.NhanVien.chucVu.in_(["Kỹ thuật viên", "Admin"])
    ).all()
    return [{"maNV": nv.maNV, "hoTen": nv.hoTen, "chucVu": nv.chucVu, "sdt": nv.sdt} for nv in ktvs]

def generate_ma_kh_le_tan(db: Session) -> str:
    """Tự động sinh mã khách hàng tăng dần duy nhất: KH001, KH002... KH046..."""
    all_rows = db.query(models.KhachHang.maKH).all()
    max_num = 0
    for (m,) in all_rows:
        if m:
            found = re.search(r"KH(\d+)", m, re.IGNORECASE)
            if found:
                try:
                    num = int(found.group(1))
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass
    return f"KH{max_num + 1:03d}"

@router.get("/next-makh", summary="Tự động sinh mã khách hàng mới tiếp theo")
def get_next_makh(db: Session = Depends(get_db)):
    return {"nextMaKH": generate_ma_kh_le_tan(db)}

@router.post("/phieu-sua/", summary="Tạo phiếu sửa chữa mới hoặc gửi tin nhắn fallback")
@router.post("/phieu-sua", summary="Tạo phiếu sửa chữa mới hoặc gửi tin nhắn fallback")
def tao_phieu_sua(phieu: PhieuSuaCreate, db: Session = Depends(get_db)):
    # 1. Fallback nếu client cũ bị cắt URL do dấu '#' và gửi request gửi tin nhắn vào đây
    if phieu.noiDung or (not phieu.maPhieu and not phieu.maKH):
        target = None
        if phieu.maPhieu:
            target = find_phieu(db, phieu.maPhieu)
        if not target and phieu.noiDung:
            m_ps = re.search(r"#?(PS\d+)", phieu.noiDung, re.IGNORECASE)
            if m_ps:
                target = find_phieu(db, m_ps.group(1))
        if not target:
            target = db.query(models.PhieuSuaChua).filter(
                models.PhieuSuaChua.trangThai == models.TrangThaiEnum.DA_SUA_XONG
            ).order_by(models.PhieuSuaChua.ngayTao.desc()).first()
        if not target:
            target = db.query(models.PhieuSuaChua).order_by(models.PhieuSuaChua.ngayTao.desc()).first()

        if target:
            now = datetime.now()
            thong_bao = models.ThongBaoKhachHang(
                maPhieu=target.maPhieu,
                kenh=phieu.channel or "Gmail",
                nguoiGui=phieu.nguoiGui or "Lễ tân",
                noiDung=phieu.noiDung or "Thông báo từ trung tâm sửa chữa",
                thoiGian=now
            )
            db.add(thong_bao)
            db.commit()
            db.refresh(thong_bao)
            kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == target.maKH).first()
            return {
                "message": f"Đã gửi thông báo thành công qua {phieu.channel or 'Gmail'}!",
                "thongBao": {
                    "id": thong_bao.id,
                    "maPhieu": target.maPhieu,
                    "maKH": target.maKH,
                    "tenKH": kh.hoTen if kh else target.maKH,
                    "kenh": phieu.channel or "Gmail",
                    "thoiGian": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "nguoiGui": phieu.nguoiGui or "Lễ tân",
                    "noiDung": thong_bao.noiDung
                }
            }
        raise HTTPException(status_code=400, detail="Thiếu thông tin phiếu sửa chữa!")

    # 2. Xử lý tạo phiếu tiếp nhận bình thường
    if not phieu.maPhieu:
        raise HTTPException(status_code=400, detail="Mã phiếu sửa chữa là bắt buộc!")

    existing = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu == phieu.maPhieu).first()
    if existing:
        raise HTTPException(status_code=400, detail="Mã phiếu sửa chữa này đã tồn tại!")

    # Xử lý Mã khách hàng thông minh: tránh trùng mã khách
    target_makh = (phieu.maKH or "").strip()
    clean_sdt = re.sub(r"[^\d+]", "", phieu.sdtKH or "").strip()
    kh = None

    # Nếu có SĐT, kiểm tra xem khách này đã từng có trong hệ thống chưa
    if clean_sdt:
        kh = db.query(models.KhachHang).filter(models.KhachHang.sdt == clean_sdt).first()

    if kh:
        # Đã tồn tại theo số điện thoại: sử dụng mã khách đã có
        target_makh = kh.maKH
        if phieu.emailKH and not kh.email:
            kh.email = phieu.emailKH
            db.commit()
    else:
        # Khách mới: nếu mã truyền lên trống hoặc trùng với khách khác có tên khác -> sinh mã mới độc lập
        existing_by_makh = db.query(models.KhachHang).filter(models.KhachHang.maKH == target_makh).first() if target_makh else None
        if not target_makh or existing_by_makh:
            target_makh = generate_ma_kh_le_tan(db)

        kh = models.KhachHang(
            maKH=target_makh,
            hoTen=phieu.hoTenKH or f"Khách hàng {target_makh}",
            sdt=clean_sdt or "0900000000",
            email=phieu.emailKH or None
        )
        db.add(kh)
        db.commit()
        db.refresh(kh)

    ma_ktv = phieu.maKTV
    if ma_ktv:
        ktv = db.query(models.NhanVien).filter(models.NhanVien.maNV == ma_ktv).first()
        if not ktv:
            ma_ktv = None

    db_phieu = models.PhieuSuaChua(
        maPhieu=phieu.maPhieu,
        maKH=target_makh,
        maKTV=ma_ktv,
        moTaLoi=phieu.moTaLoi,
        ghiChuKTV=phieu.ghiChuKTV,
        tienDatCoc=0.0,
        daDatCoc=False,
        trangThai=models.TrangThaiEnum.KHOI_TAO
    )
    db.add(db_phieu)
    db.commit()
    db.refresh(db_phieu)
    return {
        "message": f"Lập phiếu tiếp nhận {db_phieu.maPhieu} thành công!",
        "maPhieu": db_phieu.maPhieu,
        "phieu": {
            "maPhieu": db_phieu.maPhieu,
            "maKH": db_phieu.maKH,
            "tenKH": kh.hoTen,
            "sdtKH": kh.sdt,
            "trangThai": db_phieu.trangThai.value
        }
    }

@router.get("/api/le-tan/bao-gia/{ma_phieu}", summary="Lấy chi tiết báo giá để thu cọc 30%")
def get_bao_gia_thu_coc(ma_phieu: str, db: Session = Depends(get_db)):
    """Lễ tân xem báo giá từ KTV và tính tiền cọc 30%."""
    phieu = find_phieu(db, ma_phieu)
    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa!")

    kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == phieu.maKH).first()
    ktv = db.query(models.NhanVien).filter(models.NhanVien.maNV == phieu.maKTV).first() if phieu.maKTV else None

    chi_tiets = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == phieu.maPhieu).all()
    parts = []
    tien_lk = 0.0
    for ct in chi_tiets:
        lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == ct.maLK).first()
        thanh_tien = ct.donGia * ct.soLuong
        tien_lk += thanh_tien
        parts.append({
            "maLK": ct.maLK,
            "tenLK": lk.tenLK if lk else ct.maLK,
            "soLuong": ct.soLuong,
            "donGia": ct.donGia,
            "thanhTien": thanh_tien,
            "thoiGianBaoHanh": ct.thoiGianBaoHanh or "12 Tháng"
        })

    tien_cong = 150000.0
    tong_hoa_don = tien_lk + tien_cong
    tien_dat_coc = round(tong_hoa_don * 0.3, 0)
    tien_con_lai = tong_hoa_don - tien_dat_coc

    trang_thai = phieu.trangThai.value if hasattr(phieu.trangThai, 'value') else str(phieu.trangThai)

    return {
        "maPhieu": phieu.maPhieu,
        "tenKH": kh.hoTen if kh else phieu.maKH,
        "sdtKH": kh.sdt if kh else "",
        "emailKH": kh.email if (kh and hasattr(kh, 'email') and kh.email) else "",
        "tenKTV": ktv.hoTen if ktv else "Chưa phân công",
        "moTaLoi": phieu.moTaLoi or "",
        "ghiChuKTV": phieu.ghiChuKTV or "",
        "trangThai": trang_thai,
        "daDatCoc": bool(phieu.daDatCoc),
        "tienDatCocDaThu": phieu.tienDatCoc or 0.0,
        "parts": parts,
        "tienLinhKien": tien_lk,
        "tienCong": tien_cong,
        "tongTien": tong_hoa_don,
        "tongHoaDon": tong_hoa_don,
        "tienDatCoc30": tien_dat_coc,
        "tienConLai70": tien_con_lai
    }

@router.post("/api/le-tan/thu-coc/{ma_phieu}", summary="Lễ tân thu tiền đặt cọc 30%")
def thu_tien_dat_coc(ma_phieu: str, req: ThuCocRequest, db: Session = Depends(get_db)):
    """Lễ tân xác nhận thu tiền đặt cọc 30% từ khách hàng."""
    phieu = find_phieu(db, ma_phieu)
    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa!")
    if phieu.daDatCoc:
        raise HTTPException(status_code=400, detail="Phiếu này đã được thu tiền đặt cọc rồi!")

    # Tính lại tiền cọc 30%
    chi_tiets = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == phieu.maPhieu).all()
    tien_lk = sum(ct.donGia * ct.soLuong for ct in chi_tiets)
    tong_hoa_don = tien_lk + 150000.0
    tien_coc = round(tong_hoa_don * 0.3, 0)

    # Cập nhật phiếu
    phieu.tienDatCoc = tien_coc
    phieu.daDatCoc = True
    # Chuyển trạng thái sang DangSua nếu đang ở trạng thái chờ
    if phieu.trangThai in [models.TrangThaiEnum.KHOI_TAO, models.TrangThaiEnum.DANG_KIEM_TRA]:
        phieu.trangThai = models.TrangThaiEnum.DANG_SUA

    db.commit()
    db.refresh(phieu)

    # Ghi thông báo nội bộ
    thong_bao = models.ThongBaoKhachHang(
        maPhieu=phieu.maPhieu,
        kenh="Nội Bộ",
        nguoiGui=req.nguoiThu or "Lễ tân",
        noiDung=f"ĐÃ THU CỌC 30% = {int(tien_coc):,} đ | Phương thức: {req.phuongThuc} | Tổng HD: {int(tong_hoa_don):,} đ",
        thoiGian=datetime.now()
    )
    db.add(thong_bao)
    db.commit()

    tien_tra_lai = max(0, (req.tienKhachDua or 0) - tien_coc)
    return {
        "message": f"Đã thu cọc 30% = {int(tien_coc):,} đ thành công!",
        "tienDatCoc": tien_coc,
        "tongHoaDon": tong_hoa_don,
        "tienConLai70": tong_hoa_don - tien_coc,
        "tienTraLai": tien_tra_lai,
        "phuongThuc": req.phuongThuc
    }

@router.post("/api/le-tan/quyet-toan/{ma_phieu}", summary="Lễ tân thu nốt 70% khi khách đến lấy máy")
def quyet_toan_tra_may(ma_phieu: str, req: QuyetToanRequest, db: Session = Depends(get_db)):
    """Lễ tân thu 70% còn lại, tạo hóa đơn và đổi trạng thái DaThanhToan."""
    phieu = find_phieu(db, ma_phieu)
    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa!")
    if phieu.trangThai == models.TrangThaiEnum.DA_THANH_TOAN:
        raise HTTPException(status_code=400, detail="Phiếu này đã được quyết toán hoàn tất rồi!")
    if phieu.trangThai not in [models.TrangThaiEnum.DA_SUA_XONG, models.TrangThaiEnum.DANG_SUA]:
        raise HTTPException(status_code=400, detail="Máy chưa sửa xong, chưa thể thu tiền quyết toán!")

    # Tính lại tổng hóa đơn
    chi_tiets = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == phieu.maPhieu).all()
    tien_lk = sum(ct.donGia * ct.soLuong for ct in chi_tiets)
    tien_cong = 150000.0
    tong_hoa_don = tien_lk + tien_cong
    tien_coc_da_thu = phieu.tienDatCoc or 0.0
    tien_con_lai = tong_hoa_don - tien_coc_da_thu

    # Kiểm tra hóa đơn tồn tại chưa
    existing_hd = db.query(models.HoaDon).filter(models.HoaDon.maPhieu == phieu.maPhieu).first()
    if existing_hd:
        raise HTTPException(status_code=400, detail="Hóa đơn đã tồn tại!")

    # Đảm bảo thu ngân hợp lệ
    kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == phieu.maKH).first()
    ma_tn = req.maThuNgan or "NV04"
    tn_nv = db.query(models.NhanVien).filter(models.NhanVien.maNV == ma_tn).first()
    if not tn_nv:
        tn_any = db.query(models.NhanVien).filter(models.NhanVien.chucVu.in_(["Thu ngân", "Lễ tân", "Admin"])).first()
        ma_tn = tn_any.maNV if tn_any else None

    now = datetime.now()
    ma_hd = f"HD-{phieu.maPhieu}-{int(now.timestamp()) % 100000:05d}"

    hoa_don = models.HoaDon(
        maHD=ma_hd,
        maPhieu=phieu.maPhieu,
        maKH=phieu.maKH,
        maThuNgan=ma_tn,
        phuongThuc=req.phuongThuc,
        tienLinhKien=tien_lk,
        tienCong=tien_cong,
        tongTien=tong_hoa_don,
        tienKhachDua=req.tienKhachDua or tien_con_lai,
        tienTraLai=max(0, (req.tienKhachDua or tien_con_lai) - tien_con_lai),
        ghiChu=req.ghiChu or f"Thu 70% còn lại sau đặt cọc {int(tien_coc_da_thu):,} đ",
        ngayThanhToan=now
    )
    db.add(hoa_don)

    # Cập nhật trạng thái phiếu
    phieu.trangThai = models.TrangThaiEnum.DA_THANH_TOAN
    db.commit()
    db.refresh(hoa_don)

    # Ghi lịch sử thông báo
    thong_bao = models.ThongBaoKhachHang(
        maPhieu=phieu.maPhieu,
        kenh="Nội Bộ",
        nguoiGui="Lễ tân",
        noiDung=f"ĐÃ QUYẾT TOÁN HOÀN TẤT | Thu 70% = {int(tien_con_lai):,} đ | Tổng = {int(tong_hoa_don):,} đ | HD: {ma_hd}",
        thoiGian=now
    )
    db.add(thong_bao)
    db.commit()

    return {
        "message": f"Quyết toán thành công! Đã thu {int(tien_con_lai):,} đ. Máy sẵn sàng bàn giao!",
        "maHD": ma_hd,
        "tongHoaDon": tong_hoa_don,
        "tienCocDaThu": tien_coc_da_thu,
        "tienConLaiDaThu": tien_con_lai,
        "tienTraLai": max(0, (req.tienKhachDua or tien_con_lai) - tien_con_lai),
        "phuongThuc": req.phuongThuc,
        "ngayThanhToan": now.strftime("%Y-%m-%d %H:%M:%S")
    }

@router.post("/phieu-sua/{ma_phieu}/ai-tin-nhan", summary="AI Soạn email Gmail báo khách")
def ai_tin_nhan_phieu_sua(ma_phieu: str, channel: str = Query("Gmail"), db: Session = Depends(get_db)):
    phieu = find_phieu(db, ma_phieu)
    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa!")

    kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == phieu.maKH).first()
    ten_kh = kh.hoTen if kh else phieu.maKH
    trang_thai_str = phieu.trangThai.value if hasattr(phieu.trangThai, 'value') else str(phieu.trangThai)

    msg = ai_service.generate_customer_message(
        ma_phieu=phieu.maPhieu.lstrip('#'),
        ma_kh=ten_kh,
        mo_ta_loi=phieu.moTaLoi or "",
        trang_thai=trang_thai_str,
        channel=channel,
        ghi_chu_ktv=phieu.ghiChuKTV or ""
    )
    return {"tinNhan": msg, "kenh": channel, "trangThai": trang_thai_str}

@router.post("/api/le-tan/ai-mau-tin-nhan", summary="AI Soạn 3 mẫu tin nhắn theo giai đoạn")
def ai_mau_tin_nhan(req: AIMauTinNhanRequest, db: Session = Depends(get_db)):
    """AI soạn tin theo 3 giai đoạn: tiep_nhan | dat_coc | hoan_thanh."""
    phieu = find_phieu(db, req.maPhieu)
    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu!")

    kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == phieu.maKH).first()
    ten_kh = kh.hoTen if kh else phieu.maKH

    chi_tiets = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == phieu.maPhieu).all()
    parts = []
    tien_lk = 0.0
    for ct in chi_tiets:
        lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == ct.maLK).first()
        thanh_tien = ct.donGia * ct.soLuong
        tien_lk += thanh_tien
        parts.append({"tenLK": lk.tenLK if lk else ct.maLK, "thanhTien": thanh_tien})

    tong_hoa_don = tien_lk + 150000.0
    tien_coc = round(tong_hoa_don * 0.3, 0)
    tien_con_lai = tong_hoa_don - (phieu.tienDatCoc or tien_coc)

    if req.loai == "dat_coc":
        msg = ai_service.generate_deposit_message(
            ma_phieu=phieu.maPhieu.lstrip('#'), ten_kh=ten_kh, mo_ta_loi=phieu.moTaLoi or "",
            parts_list=parts, tien_coc=tien_coc, tong_hoa_don=tong_hoa_don, channel=req.channel
        )
    elif req.loai == "hoan_thanh":
        msg = ai_service.generate_completion_message(
            ma_phieu=phieu.maPhieu.lstrip('#'), ten_kh=ten_kh,
            tien_coc=phieu.tienDatCoc or tien_coc,
            tien_con_lai=tong_hoa_don - (phieu.tienDatCoc or tien_coc),
            channel=req.channel
        )
    else:  # tiep_nhan
        trang_thai_str = phieu.trangThai.value if hasattr(phieu.trangThai, 'value') else str(phieu.trangThai)
        msg = ai_service.generate_customer_message(
            ma_phieu=phieu.maPhieu.lstrip('#'), ma_kh=ten_kh, mo_ta_loi=phieu.moTaLoi or "",
            trang_thai=trang_thai_str, channel=req.channel, ghi_chu_ktv=phieu.ghiChuKTV or ""
        )

    return {
        "tinNhan": clean_customer_message(msg),
        "loai": req.loai,
        "kenh": req.channel,
        "tenKH": ten_kh,
        "sdtKH": kh.sdt if kh else "",
        "emailKH": (kh.email if (kh and hasattr(kh, 'email') and kh.email) else ""),
        "tongHoaDon": tong_hoa_don,
        "tienCoc30": tien_coc,
        "tienConLai70": tong_hoa_don - (phieu.tienDatCoc or tien_coc)
    }

@router.post("/phieu-sua/{ma_phieu}/gui-tin-nhan", summary="Xác nhận gửi tin nhắn và lưu MySQL")
@router.post("/phieu-sua/gui-tin-nhan", summary="Xác nhận gửi tin nhắn (nhận maPhieu trong body)")
@router.post("/api/le-tan/gui-tin-nhan", summary="API riêng cho Lễ tân gửi tin nhắn")
def api_gui_tin_nhan(req: GuiTinNhanRequest, ma_phieu: Optional[str] = None, db: Session = Depends(get_db)):
    target_code = ma_phieu or req.maPhieu
    phieu = None
    if target_code:
        phieu = find_phieu(db, target_code)

    # Nếu không tìm thấy bằng code, thử tìm trong nội dung tin nhắn
    if not phieu and req.noiDung:
        import re
        m_ps = re.search(r"#?(PS\d+)", req.noiDung, re.IGNORECASE)
        if m_ps:
            phieu = find_phieu(db, m_ps.group(1))

    # Nếu vẫn chưa có, lấy phiếu vừa sửa xong hoặc phiếu mới nhất
    if not phieu:
        phieu = db.query(models.PhieuSuaChua).filter(
            models.PhieuSuaChua.trangThai == models.TrangThaiEnum.DA_SUA_XONG
        ).order_by(models.PhieuSuaChua.ngayTao.desc()).first()

    if not phieu:
        phieu = db.query(models.PhieuSuaChua).order_by(models.PhieuSuaChua.ngayTao.desc()).first()

    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa nào trong hệ thống!")

    channel_name = req.channel or req.kenh or "Gmail"
    now = datetime.now()
    thong_bao = models.ThongBaoKhachHang(
        maPhieu=phieu.maPhieu,
        kenh=channel_name,
        nguoiGui=req.nguoiGui or "Lễ tân",
        noiDung=req.noiDung or "",
        thoiGian=now
    )
    db.add(thong_bao)
    db.commit()
    db.refresh(thong_bao)

    kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == phieu.maKH).first()
    
    # Cập nhật thông tin email và SĐT khách nếu người dùng truyền lên
    if req.emailKhach and req.emailKhach.strip():
        email_clean = req.emailKhach.strip()
        if email_clean.lower().endswith("@gmai.com"):
            email_clean = email_clean[:-9] + "@gmail.com"
        if kh:
            kh.email = email_clean
            db.commit()

    if req.sdtKhach and req.sdtKhach.strip():
        if kh:
            kh.sdt = req.sdtKhach.strip()
            db.commit()

    sdt_thuc = (req.sdtKhach or (kh.sdt if kh else "") or "0900000000").strip()
    email_kh = (req.emailKhach or (kh.email if kh and hasattr(kh, 'email') and kh.email else "") or "thuha0106206@gmail.com").strip()
    if email_kh.lower().endswith("@gmai.com"):
        email_kh = email_kh[:-9] + "@gmail.com"

    import re
    from urllib.parse import quote
    clean_phone = re.sub(r"[^\d+]", "", sdt_thuc)
    link_mail = f"mailto:{email_kh}?subject={quote(f'[FrogHippo Phone] Thông báo dịch vụ #{phieu.maPhieu}')}&body={quote(req.noiDung or '')}"

    email_send_result = None
    sms_send_result = None
    gmail_web_url = None
    sms_uri = None
    res_message = ""

    # Xử lý theo kênh gửi
    if channel_name.upper() == "SMS":
        import sms_service
        try:
            sms_send_result = sms_service.send_customer_sms(
                to_phone=clean_phone,
                content=req.noiDung or "",
                customer_name=kh.hoTen if kh else phieu.maKH,
                ma_phieu=phieu.maPhieu
            )
            sms_uri = sms_send_result.get("smsUri")
            res_message = f"Đã gửi tin nhắn SMS thành công tới số {clean_phone}!"
        except Exception as sms_err:
            sms_send_result = {"success": False, "error": str(sms_err)}
            res_message = f"Lỗi gửi SMS: {sms_err}"
    else:  # Gmail / Email
        import email_service
        if email_kh and ("@" in email_kh):
            try:
                email_send_result = email_service.send_customer_email(
                    to_email=email_kh,
                    content=req.noiDung or "",
                    customer_name=kh.hoTen if kh else phieu.maKH,
                    ma_phieu=phieu.maPhieu,
                    subject=f"[FrogHippo Phone] Thông Báo Dịch Vụ Sửa Chữa #{phieu.maPhieu.lstrip('#')}"
                )
                gmail_web_url = email_send_result.get("gmailWebUrl")
                res_message = f"Đã gửi email thông báo thành công tới {email_kh} qua Gmail!"
            except Exception as err:
                email_send_result = {"success": False, "error": str(err)}
                res_message = f"Lỗi gửi Gmail: {err}"
        else:
            res_message = "Chưa có địa chỉ Email hợp lệ để gửi Gmail!"

    try:
        print(f"[THONG BAO SERVICE] Kenh: {channel_name} | Nhan: {email_kh if 'GMAIL' in channel_name.upper() else clean_phone} | Phieu #{phieu.maPhieu} | OK")
    except Exception:
        pass

    return {
        "success": True,
        "message": res_message,
        "channel": channel_name,
        "emailKhach": email_kh,
        "sdtThuc": clean_phone,
        "tenKH": kh.hoTen if kh else phieu.maKH,
        "linkMail": link_mail,
        "gmailWebUrl": gmail_web_url,
        "smsUri": sms_uri,
        "emailResult": email_send_result,
        "smsResult": sms_send_result,
        "thongBao": {
            "id": thong_bao.id,
            "maPhieu": phieu.maPhieu,
            "maKH": phieu.maKH,
            "tenKH": kh.hoTen if kh else phieu.maKH,
            "sdtKH": clean_phone,
            "emailKH": email_kh,
            "kenh": channel_name,
            "thoiGian": now.strftime("%Y-%m-%d %H:%M:%S"),
            "nguoiGui": req.nguoiGui or "Lễ tân",
            "noiDung": thong_bao.noiDung
        }
    }

@router.post("/api/le-tan/chatbot-linh-kien", summary="Chatbot tư vấn giá linh kiện từ CSDL thật & chuẩn đoán KTV")
def chatbot_linh_kien(req: ChatbotRequest, db: Session = Depends(get_db)):
    """
    Chatbot tư vấn giá linh kiện & chuẩn đoán kỹ thuật. 
    100% grounded trên Bộ Quy chuẩn, Chuẩn đoán của KTV và CSDL linh kiện thật.
    """
    # Lấy toàn bộ danh mục linh kiện thật từ DB
    all_lk = db.query(models.LinhKien).all()
    danh_muc = [
        {
            "maLK": lk.maLK,
            "tenLK": lk.tenLK,
            "giaBan": lk.giaBan,
            "soLuongTon": lk.soLuongTon
        }
        for lk in all_lk
    ]

    phieu_info = None
    if req.maPhieu:
        phieu = db.query(models.PhieuSuaChua).filter(
            models.PhieuSuaChua.maPhieu.ilike(req.maPhieu.strip())
        ).first()
        if phieu:
            kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == phieu.maKH).first()
            chi_tiets = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == phieu.maPhieu).all()
            parts = []
            for ct in chi_tiets:
                lk_item = db.query(models.LinhKien).filter(models.LinhKien.maLK == ct.maLK).first()
                parts.append({
                    "maLK": ct.maLK,
                    "tenLK": lk_item.tenLK if lk_item else ct.maLK,
                    "donGia": ct.donGia,
                    "soLuong": ct.soLuong
                })
            
            phieu_info = {
                "maPhieu": phieu.maPhieu,
                "tenKhachHang": kh.hoTen if kh else phieu.maKH,
                "moTaLoi": phieu.moTaLoi or "",
                "ghiChuKTV": phieu.ghiChuKTV or "",
                "chuanDoanKTV": phieu.chuanDoanKTV or "",
                "daDuyetChuanDoan": bool(phieu.daDuyetChuanDoan),
                "nguoiDuyetChuanDoan": phieu.nguoiDuyetChuanDoan or "Kỹ thuật viên",
                "thoiGianDuyetChuanDoan": phieu.thoiGianDuyetChuanDoan.strftime("%H:%M %d/%m/%Y") if phieu.thoiGianDuyetChuanDoan else "",
                "trangThai": phieu.trangThai.value if hasattr(phieu.trangThai, 'value') else str(phieu.trangThai),
                "parts": parts,
                "tienDatCoc": phieu.tienDatCoc or 0.0,
                "daDatCoc": bool(phieu.daDatCoc)
            }

    reply = ai_service.chat_tu_van_linh_kien(
        user_message=req.message,
        danh_muc_linh_kien=danh_muc,
        phieu_info=phieu_info,
        file_data=req.fileData,
        file_name=req.fileName,
        file_mime_type=req.fileMimeType
    )
    return {
        "reply": reply, 
        "tongSoLinhKien": len(danh_muc),
        "maPhieu": phieu_info.get("maPhieu") if phieu_info else None,
        "coChuanDoanKTV": bool(phieu_info and phieu_info.get("ghiChuKTV")),
        "fileName": req.fileName if req.fileData else None
    }

@router.get("/api/thong-bao-lich-su", summary="Lịch sử các tin nhắn thông báo đã gửi cho khách")
def get_lich_su_thong_bao(db: Session = Depends(get_db)):
    tb_list = db.query(models.ThongBaoKhachHang).order_by(
        models.ThongBaoKhachHang.thoiGian.desc()
    ).limit(100).all()

    result = []
    for tb in tb_list:
        kh_info = ""
        phieu = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu == tb.maPhieu).first()
        if phieu:
            kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == phieu.maKH).first()
            kh_info = kh.hoTen if kh else phieu.maKH

        result.append({
            "id": tb.id,
            "maPhieu": tb.maPhieu,
            "maKH": phieu.maKH if phieu else "",
            "tenKH": kh_info,
            "kenh": tb.kenh,
            "thoiGian": tb.thoiGian.strftime("%Y-%m-%d %H:%M:%S") if tb.thoiGian else "",
            "nguoiGui": tb.nguoiGui,
            "noiDung": tb.noiDung
        })

    return result

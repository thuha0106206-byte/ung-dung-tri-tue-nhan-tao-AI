import os
import re
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from database import get_db
import models
import ai_service

router = APIRouter(prefix="/api/lich-hen", tags=["Lịch Hẹn Sửa Chữa"])

# Danh sách khung giờ làm việc tiêu chuẩn (08:00 - 17:00, mỗi giờ 1 khung)
VALID_SLOTS = [
    "08:00", "09:00", "10:00", "11:00", "12:00",
    "13:00", "14:00", "15:00", "16:00", "17:00"
]
MAX_PER_SLOT = 3
MAX_PENDING_PER_PHONE = 2

# Máy chuyển trạng thái hợp lệ
VALID_TRANSITIONS = {
    "Chờ xác nhận": ["Đã xác nhận", "Đã hủy"],
    "Đã xác nhận": ["Đã đến", "Không đến", "Đã hủy"]
}

# --- SCHEMAS ---
class LichHenCreate(BaseModel):
    hoTen: str = Field(..., description="Họ tên khách hàng")
    sdt: str = Field(..., description="Số điện thoại khách hàng (10 chữ số)")
    email: Optional[str] = Field(None, description="Email/Gmail của khách hàng (nhận xác nhận lịch)")
    hangMay: Optional[str] = Field("Apple", description="Hãng máy (Apple, Samsung...)")
    model: str = Field(..., description="Dòng máy (VD: iPhone 13 Pro)")
    moTaLoi: Optional[str] = Field("", description="Mô tả lỗi hoặc triệu chứng")
    ngayHen: str = Field(..., description="Ngày hẹn định dạng YYYY-MM-DD")
    khungGio: str = Field(..., description="Khung giờ (VD: 09:00)")

class LichHenUpdateTrangThai(BaseModel):
    trangThai: str = Field(..., description="Trạng thái mới: Đã xác nhận, Đã đến, Không đến, Đã hủy")
    lyDo: Optional[str] = Field(None, description="Lý do khi hủy/đổi lịch (bắt buộc nếu hủy)")

class TaoPhieuFromLichHenRequest(BaseModel):
    maPhieu: Optional[str] = Field(None, description="Mã phiếu tùy chọn nếu muốn chỉ định")
    maKTV: Optional[str] = Field(None, description="Mã kỹ thuật viên phân công")
    ghiChu: Optional[str] = Field(None, description="Ghi chú thêm của Lễ tân")

class LichHenSendMessageRequest(BaseModel):
    channel: str = Field("Gmail", description="Kênh gửi: Gmail hoặc SMS")
    noiDung: str = Field(..., description="Nội dung tin nhắn xác nhận lịch")
    emailKhach: Optional[str] = Field(None, description="Email người nhận")
    sdtKhach: Optional[str] = Field(None, description="Số điện thoại người nhận")
    nguoiGui: Optional[str] = Field("Lễ tân", description="Người gửi")

def clean_phone(sdt: str) -> str:
    """Chuẩn hóa số điện thoại, loại bỏ dấu cách, gạch nối, chấm."""
    return re.sub(r"[\s\-\.]", "", sdt or "").strip()

def validate_phone(sdt: str) -> str:
    """Kiểm tra định dạng số điện thoại Việt Nam (10 chữ số, bắt đầu bằng 0)."""
    cleaned = clean_phone(sdt)
    if not re.match(r"^0[1-9]\d{8}$", cleaned):
        raise HTTPException(
            status_code=400,
            detail="Số điện thoại không đúng định dạng! Vui lòng nhập số điện thoại Việt Nam gồm 10 chữ số (VD: 0912345678)."
        )
    return cleaned

def generate_ma_lh(db: Session) -> str:
    """Tự động sinh mã lịch hẹn tăng dần: LH001, LH002..."""
    all_rows = db.query(models.LichHen.MaLH).all()
    max_num = 0
    for (m,) in all_rows:
        if m:
            found = re.search(r"LH(\d+)", m, re.IGNORECASE)
            if found:
                try:
                    num = int(found.group(1))
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass
    return f"LH{max_num + 1:03d}"

def generate_ma_kh(db: Session) -> str:
    """Tự động sinh mã khách hàng tăng dần: KH001, KH002..."""
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

def generate_ma_phieu(db: Session) -> str:
    """Tự động sinh mã phiếu sửa chữa không trùng lặp."""
    all_rows = db.query(models.PhieuSuaChua.maPhieu).all()
    max_num = 0
    for (m,) in all_rows:
        if m:
            found = re.search(r"PS(\d+)", m, re.IGNORECASE)
            if found:
                try:
                    num = int(found.group(1))
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass
    candidate = f"#PS{max_num + 1:02d}"
    # Đảm bảo duy nhất
    existing = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu == candidate).first()
    if existing:
        candidate = f"#PS{max_num + 2:02d}"
    return candidate


# ==============================================================================
# 1. GET /api/lich-hen/khung-gio-trong?ngay=YYYY-MM-DD
# ==============================================================================
@router.get("/khung-gio-trong", summary="Lấy danh sách khung giờ và số chỗ trống theo ngày")
def get_khung_gio_trong(
    ngay: str = Query(..., description="Ngày cần kiểm tra (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    try:
        ngay_obj = datetime.strptime(ngay.strip(), "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Định dạng ngày không hợp lệ! Vui lòng dùng định dạng YYYY-MM-DD.")

    today = date.today()
    if ngay_obj < today:
        raise HTTPException(
            status_code=422,
            detail="Không thể xem hoặc đặt lịch cho ngày trong quá khứ!"
        )

    # Kiểm tra Chủ nhật (weekday = 6)
    is_sunday = (ngay_obj.weekday() == 6)
    if is_sunday:
        return {
            "ngay": ngay,
            "ngayThu": "Chủ nhật",
            "dongCua": True,
            "thongBao": "Trung tâm FrogHippo Phone không nhận lịch hẹn vào Chủ nhật. Quý khách vui lòng chọn từ Thứ 2 đến Thứ 7.",
            "khungGio": []
        }

    # Đếm số lượng đặt trong từng khung giờ (loại trừ các lịch "Đã hủy")
    active_bookings = db.query(
        models.LichHen.KhungGio
    ).filter(
        models.LichHen.NgayHen == ngay_obj,
        models.LichHen.TrangThai != "Đã hủy"
    ).all()

    counts = {}
    for (kg,) in active_bookings:
        counts[kg] = counts.get(kg, 0) + 1

    result = []
    weekday_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    thu_str = weekday_names[ngay_obj.weekday()]

    for slot in VALID_SLOTS:
        da_dat = counts.get(slot, 0)
        con_lai = max(0, MAX_PER_SLOT - da_dat)
        result.append({
            "khungGio": slot,
            "tongCho": MAX_PER_SLOT,
            "daDat": da_dat,
            "conLai": con_lai,
            "day": da_dat >= MAX_PER_SLOT
        })

    return {
        "ngay": ngay,
        "ngayThu": thu_str,
        "dongCua": False,
        "gioLamViec": "08:00 - 17:00 (T2 - T7)",
        "khungGio": result
    }


# ==============================================================================
# 2. POST /api/lich-hen: Khách đặt lịch hẹn mới
# ==============================================================================
@router.post("", status_code=201, summary="Khách hàng đặt lịch hẹn sửa chữa")
def create_lich_hen(data: LichHenCreate, db: Session = Depends(get_db)):
    # 1. Kiểm tra thiếu trường bắt buộc
    ho_ten = (data.hoTen or "").strip()
    sdt_raw = (data.sdt or "").strip()
    model = (data.model or "").strip()
    ngay_raw = (data.ngayHen or "").strip()
    khung_gio = (data.khungGio or "").strip()
    hang_may = (data.hangMay or "Apple").strip()
    email_raw = (data.email or "").strip()
    clean_email = email_raw if email_raw and "@" in email_raw else None

    if not ho_ten or not sdt_raw or not model or not ngay_raw or not khung_gio:
        raise HTTPException(
            status_code=400,
            detail="Vui lòng điền đầy đủ các thông tin: Họ tên, Số điện thoại, Model máy, Ngày hẹn và Khung giờ!"
        )

    # 2. Kiểm tra định dạng số điện thoại
    sdt = validate_phone(sdt_raw)

    # 3. Kiểm tra ngày hẹn
    try:
        ngay_hen = datetime.strptime(ngay_raw, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Định dạng ngày hẹn không hợp lệ! Vui lòng dùng YYYY-MM-DD.")

    today = date.today()
    if ngay_hen < today:
        raise HTTPException(
            status_code=422,
            detail="Ngày hẹn không thể là ngày đã qua! Vui lòng chọn từ ngày hôm nay trở đi."
        )

    if ngay_hen.weekday() == 6:
        raise HTTPException(
            status_code=422,
            detail="Trung tâm không nhận lịch sửa chữa vào Chủ nhật! Vui lòng chọn lịch từ Thứ 2 đến Thứ 7."
        )

    # 4. Kiểm tra khung giờ ngoài giờ làm việc
    if khung_gio not in VALID_SLOTS:
        raise HTTPException(
            status_code=422,
            detail=f"Khung giờ '{khung_gio}' nằm ngoài giờ làm việc (08:00 - 17:00)! Vui lòng chọn trong các khung: {', '.join(VALID_SLOTS)}."
        )

    # 5. Kiểm tra giới hạn 3 khách / khung giờ (HTTP 409)
    current_slot_count = db.query(models.LichHen).filter(
        models.LichHen.NgayHen == ngay_hen,
        models.LichHen.KhungGio == khung_gio,
        models.LichHen.TrangThai != "Đã hủy"
    ).count()

    if current_slot_count >= MAX_PER_SLOT:
        raise HTTPException(
            status_code=409,
            detail=f"Khung giờ {khung_gio} ngày {ngay_raw} đã đủ {MAX_PER_SLOT} lịch hẹn! Quý khách vui lòng chọn khung giờ khác."
        )

    # 6. Kiểm tra số điện thoại đã có từ 2 lịch đang chờ xác nhận (HTTP 409)
    # Tìm khách hàng theo SĐT và Họ tên
    existing_kh = db.query(models.KhachHang).filter(models.KhachHang.sdt == sdt).first()
    if existing_kh:
        # Kiểm tra xem có đúng là cùng 1 người không để tránh trùng mã khách
        is_same = (
            existing_kh.hoTen.strip().lower() == ho_ten.strip().lower() or
            not existing_kh.hoTen or
            existing_kh.hoTen.startswith("Khách hàng")
        )
        if not is_same:
            # Tên khác -> Khách hàng khác dùng số này: sinh mã khách mới độc lập
            new_makh = generate_ma_kh(db)
            existing_kh = models.KhachHang(
                maKH=new_makh,
                hoTen=ho_ten,
                sdt=sdt,
                email=clean_email,
                ngayTao=datetime.now()
            )
            db.add(existing_kh)
            db.commit()
            db.refresh(existing_kh)
        else:
            if clean_email and existing_kh.email != clean_email:
                existing_kh.email = clean_email
                db.commit()
                db.refresh(existing_kh)
            pending_count = db.query(models.LichHen).filter(
                models.LichHen.MaKH == existing_kh.maKH,
                models.LichHen.TrangThai == "Chờ xác nhận"
            ).count()
            if pending_count >= MAX_PENDING_PER_PHONE:
                raise HTTPException(
                    status_code=409,
                    detail=f"Số điện thoại {sdt} hiện đã có {pending_count} lịch hẹn đang 'Chờ xác nhận'! Vui lòng chờ Lễ tân liên hệ hỗ trợ trước khi tạo thêm lịch mới."
                )
    else:
        # Tạo mới khách hàng tự động với mã KH tăng dần duy nhất
        new_makh = generate_ma_kh(db)
        existing_kh = models.KhachHang(
            maKH=new_makh,
            hoTen=ho_ten,
            sdt=sdt,
            email=clean_email,
            ngayTao=datetime.now()
        )
        db.add(existing_kh)
        db.commit()
        db.refresh(existing_kh)

    # 7. Sinh mã lịch hẹn & lưu CSDL
    ma_lh = generate_ma_lh(db)
    new_lh = models.LichHen(
        MaLH=ma_lh,
        MaKH=existing_kh.maKH,
        HangMay=hang_may,
        Model=model,
        MoTaLoi=(data.moTaLoi or "").strip(),
        NgayHen=ngay_hen,
        KhungGio=khung_gio,
        TrangThai="Chờ xác nhận",
        LyDo=None,
        MaPhieu=None,
        NgayTao=datetime.now()
    )
    db.add(new_lh)
    db.commit()
    db.refresh(new_lh)

    return {
        "message": f"Đặt lịch sửa chữa thành công! Mã lịch hẹn của Quý khách là {ma_lh}.",
        "maLH": ma_lh,
        "lichHen": {
            "maLH": new_lh.MaLH,
            "maKH": new_lh.MaKH,
            "hoTen": existing_kh.hoTen,
            "sdt": existing_kh.sdt,
            "email": existing_kh.email or "",
            "hangMay": new_lh.HangMay,
            "model": new_lh.Model,
            "moTaLoi": new_lh.MoTaLoi,
            "ngayHen": str(new_lh.NgayHen),
            "khungGio": new_lh.KhungGio,
            "trangThai": new_lh.TrangThai,
            "ngayTao": new_lh.NgayTao.strftime("%Y-%m-%d %H:%M:%S") if new_lh.NgayTao else None
        }
    }


# ==============================================================================
# 3. GET /api/lich-hen: Lấy danh sách lịch hẹn (Bộ lọc ngày & trạng thái cho Lễ tân)
# ==============================================================================
@router.get("", summary="Lấy danh sách tất cả lịch hẹn (cho Lễ tân)")
def get_danh_sach_lich_hen(
    ngay: Optional[str] = Query(None, description="Lọc theo ngày YYYY-MM-DD"),
    trang_thai: Optional[str] = Query(None, description="Lọc theo trạng thái"),
    db: Session = Depends(get_db)
):
    query = db.query(models.LichHen)

    if ngay and ngay.strip():
        try:
            ngay_obj = datetime.strptime(ngay.strip(), "%Y-%m-%d").date()
            query = query.filter(models.LichHen.NgayHen == ngay_obj)
        except Exception:
            pass

    if trang_thai and trang_thai.strip() and trang_thai != "Tất cả":
        query = query.filter(models.LichHen.TrangThai == trang_thai.strip())

    records = query.order_by(desc(models.LichHen.NgayHen), models.LichHen.KhungGio).all()

    today = date.today()
    # Thống kê nhanh
    all_today = db.query(models.LichHen).filter(models.LichHen.NgayHen == today).all()
    count_today = len(all_today)
    count_cho_xac_nhan = db.query(models.LichHen).filter(models.LichHen.TrangThai == "Chờ xác nhận").count()
    count_da_xac_nhan = db.query(models.LichHen).filter(models.LichHen.TrangThai == "Đã xác nhận").count()

    results = []
    for r in records:
        kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == r.MaKH).first()
        results.append({
            "maLH": r.MaLH,
            "maKH": r.MaKH,
            "hoTen": kh.hoTen if kh else r.MaKH,
            "sdt": kh.sdt if kh else "",
            "email": (kh.email or "") if kh else "",
            "hangMay": r.HangMay,
            "model": r.Model,
            "moTaLoi": r.MoTaLoi or "",
            "ngayHen": str(r.NgayHen),
            "khungGio": r.KhungGio,
            "trangThai": r.TrangThai,
            "lyDo": r.LyDo or "",
            "maPhieu": r.MaPhieu or "",
            "ngayTao": r.NgayTao.strftime("%Y-%m-%d %H:%M:%S") if r.NgayTao else ""
        })

    return {
        "tongSo": len(results),
        "lichHenHomNay": count_today,
        "choXacNhan": count_cho_xac_nhan,
        "daXacNhan": count_da_xac_nhan,
        "danhSach": results
    }


# ==============================================================================
# 4. GET /api/lich-hen/{ma}: Tra cứu theo mã lịch hẹn hoặc số điện thoại
# ==============================================================================
@router.get("/{ma}", summary="Tra cứu lịch hẹn theo Mã LH hoặc Số Điện Thoại")
def get_lich_hen_by_code_or_phone(ma: str, db: Session = Depends(get_db)):
    clean_ma = (ma or "").strip()
    if not clean_ma:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp Mã lịch hẹn hoặc Số điện thoại!")

    # 1. Thử tìm theo Mã LH chính xác (không phân biệt hoa thường)
    lh = db.query(models.LichHen).filter(
        models.LichHen.MaLH.ilike(clean_ma)
    ).first()

    if lh:
        kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == lh.MaKH).first()
        return {
            "type": "single",
            "lichHen": {
                "maLH": lh.MaLH,
                "maKH": lh.MaKH,
                "hoTen": kh.hoTen if kh else lh.MaKH,
                "sdt": kh.sdt if kh else "",
                "email": (kh.email or "") if kh else "",
                "hangMay": lh.HangMay,
                "model": lh.Model,
                "moTaLoi": lh.MoTaLoi or "",
                "ngayHen": str(lh.NgayHen),
                "khungGio": lh.KhungGio,
                "trangThai": lh.TrangThai,
                "lyDo": lh.LyDo or "",
                "maPhieu": lh.MaPhieu or "",
                "ngayTao": lh.NgayTao.strftime("%Y-%m-%d %H:%M:%S") if lh.NgayTao else ""
            }
        }

    # 2. Thử tìm theo Số điện thoại
    clean_sdt = clean_phone(clean_ma)
    khach = db.query(models.KhachHang).filter(models.KhachHang.sdt == clean_sdt).first()
    if khach:
        list_lh = db.query(models.LichHen).filter(
            models.LichHen.MaKH == khach.maKH
        ).order_by(desc(models.LichHen.NgayTao)).all()

        if list_lh:
            formatted_list = []
            for item in list_lh:
                formatted_list.append({
                    "maLH": item.MaLH,
                    "maKH": item.MaKH,
                    "hoTen": khach.hoTen,
                    "sdt": khach.sdt,
                    "email": (khach.email or "") if khach else "",
                    "hangMay": item.HangMay,
                    "model": item.Model,
                    "moTaLoi": item.MoTaLoi or "",
                    "ngayHen": str(item.NgayHen),
                    "khungGio": item.KhungGio,
                    "trangThai": item.TrangThai,
                    "lyDo": item.LyDo or "",
                    "maPhieu": item.MaPhieu or "",
                    "ngayTao": item.NgayTao.strftime("%Y-%m-%d %H:%M:%S") if item.NgayTao else ""
                })
            return {
                "type": "list",
                "hoTen": khach.hoTen,
                "sdt": khach.sdt,
                "email": (khach.email or "") if khach else "",
                "lichHen": formatted_list[0],  # Bản ghi mới nhất
                "danhSach": formatted_list
            }

    # 3. Không tìm thấy
    raise HTTPException(
        status_code=404,
        detail=f"Không tìm thấy lịch hẹn cho '{clean_ma}'. Vui lòng kiểm tra lại Mã lịch hẹn (VD: LH001) hoặc Số điện thoại!"
    )


# ==============================================================================
# 5. PUT /api/lich-hen/{id}/trang-thai: Cập nhật trạng thái lịch hẹn
# ==============================================================================
@router.put("/{id}/trang-thai", summary="Cập nhật trạng thái lịch hẹn")
def update_trang_thai_lich_hen(
    id: str,
    data: LichHenUpdateTrangThai,
    db: Session = Depends(get_db)
):
    clean_id = id.strip()
    lh = db.query(models.LichHen).filter(models.LichHen.MaLH.ilike(clean_id)).first()
    if not lh:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy lịch hẹn có mã '{clean_id}'!")

    current_status = lh.TrangThai
    target_status = data.trangThai.strip()
    ly_do = (data.lyDo or "").strip()

    # Kiểm tra tính hợp lệ của bước chuyển trạng thái
    allowed = VALID_TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Không thể chuyển trạng thái từ '{current_status}' sang '{target_status}'. Chỉ cho phép: {', '.join(allowed) if allowed else 'Không có'}!"
        )

    # Nếu trạng thái đích là "Đã hủy", bắt buộc phải có lý do (HTTP 400)
    if target_status == "Đã hủy":
        if not ly_do:
            raise HTTPException(
                status_code=400,
                detail="Bắt buộc phải cung cấp lý do khi hủy lịch hẹn!"
            )
        lh.LyDo = ly_do
    elif ly_do:
        lh.LyDo = ly_do

    lh.TrangThai = target_status
    db.commit()
    db.refresh(lh)

    return {
        "message": f"Cập nhật trạng thái lịch hẹn {lh.MaLH} thành '{target_status}' thành công!",
        "maLH": lh.MaLH,
        "trangThai": lh.TrangThai,
        "lyDo": lh.LyDo
    }


# ==============================================================================
# 6. POST /api/lich-hen/{id}/tao-phieu: Lễ tân tạo Phiếu sửa chữa từ lịch hẹn
# ==============================================================================
@router.post("/{id}/tao-phieu", status_code=201, summary="Lễ tân tạo Phiếu sửa chữa từ lịch hẹn")
def tao_phieu_tu_lich_hen(
    id: str,
    data: Optional[TaoPhieuFromLichHenRequest] = None,
    db: Session = Depends(get_db)
):
    clean_id = id.strip()
    lh = db.query(models.LichHen).filter(models.LichHen.MaLH.ilike(clean_id)).first()
    if not lh:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy lịch hẹn có mã '{clean_id}'!")

    # Chỉ được tạo phiếu khi lịch đang "Đã xác nhận"
    if lh.TrangThai != "Đã xác nhận":
        raise HTTPException(
            status_code=422,
            detail=f"Chỉ có thể tạo phiếu sửa chữa từ lịch hẹn ở trạng thái 'Đã xác nhận'! (Trạng thái hiện tại: '{lh.TrangThai}')."
        )

    # Đảm bảo chưa có phiếu trước đó
    if lh.MaPhieu:
        existing_phieu = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu == lh.MaPhieu).first()
        if existing_phieu:
            return {
                "message": f"Lịch hẹn {lh.MaLH} đã được tạo phiếu {lh.MaPhieu} trước đó!",
                "maPhieu": lh.MaPhieu,
                "maLH": lh.MaLH
            }

    # Sinh mã phiếu hoặc dùng mã chỉ định
    ma_phieu = (data.maPhieu.strip() if data and data.maPhieu else None) or generate_ma_phieu(db)

    # Kiểm tra trùng mã phiếu
    exist = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu == ma_phieu).first()
    if exist:
        ma_phieu = generate_ma_phieu(db)

    # Tạo mô tả tiếp nhận chi tiết
    mo_ta = f"[{lh.HangMay} {lh.Model}] {lh.MoTaLoi or 'Khách mang máy đến theo lịch hẹn ' + lh.MaLH}"

    new_phieu = models.PhieuSuaChua(
        maPhieu=ma_phieu,
        maKH=lh.MaKH,
        maKTV=(data.maKTV.strip() if data and data.maKTV else None),
        moTaLoi=mo_ta,
        ghiChuKTV=(data.ghiChu.strip() if data and data.ghiChu else f"Lập từ lịch hẹn {lh.MaLH}"),
        tienDatCoc=0.0,
        daDatCoc=False,
        trangThai=models.TrangThaiEnum.KHOI_TAO,
        ngayTao=datetime.now()
    )
    db.add(new_phieu)

    # Cập nhật lịch hẹn: gán MaPhieu và chuyển sang "Đã đến"
    lh.MaPhieu = ma_phieu
    lh.TrangThai = "Đã đến"

    db.commit()
    db.refresh(new_phieu)
    db.refresh(lh)

    kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == lh.MaKH).first()

    return {
        "message": f"Tạo phiếu sửa chữa {ma_phieu} từ lịch hẹn {lh.MaLH} thành công!",
        "maPhieu": ma_phieu,
        "maLH": lh.MaLH,
        "trangThaiLichHen": lh.TrangThai,
        "phieu": {
            "maPhieu": new_phieu.maPhieu,
            "maKH": new_phieu.maKH,
            "tenKH": kh.hoTen if kh else new_phieu.maKH,
            "sdt": kh.sdt if kh else "",
            "moTaLoi": new_phieu.moTaLoi,
            "trangThai": new_phieu.trangThai.value if hasattr(new_phieu.trangThai, 'value') else str(new_phieu.trangThai)
        }
    }


# ==============================================================================
# 7. POST /api/lich-hen/{id}/ai-soan-tin: AI Gemini soạn tin nhắn xác nhận
# ==============================================================================
@router.post("/{id}/ai-soan-tin", summary="AI Gemini soạn tin nhắn Zalo/SMS xác nhận lịch hẹn (Anti-hallucination)")
def ai_draft_confirmation_message(id: str, db: Session = Depends(get_db)):
    clean_id = id.strip()
    lh = db.query(models.LichHen).filter(models.LichHen.MaLH.ilike(clean_id)).first()
    if not lh:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy lịch hẹn có mã '{clean_id}'!")

    kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == lh.MaKH).first()
    ten_kh = kh.hoTen if kh else "Quý khách"
    sdt_kh = kh.sdt if kh else ""
    device = f"{lh.HangMay} {lh.Model}".strip()
    loi = lh.MoTaLoi or "Kiểm tra kỹ thuật định kỳ"
    ngay_str = lh.NgayHen.strftime("%d/%m/%Y")
    gio_str = lh.KhungGio

    # Nội dung chuẩn xác chỉ dùng thông tin trong lịch hẹn (Anti-hallucination)
    prompt = (
        f"Bạn là nhân viên Lễ tân trung tâm bảo hành sửa chữa điện thoại FrogHippo Phone. "
        f"Hãy soạn một tin nhắn Zalo / SMS lịch sự, thân thiện và chuyên nghiệp gửi khách hàng để XÁC NHẬN LỊCH HẸN SỬA CHỮA.\n"
        f"QUY TẮC BẮT BUỘC (ANTI-HALLUCINATION / KHÔNG BỊA CHUYỆN):\n"
        f"- CHỈ ĐƯỢC DÙNG CÁC THÔNG TIN DƯỚI ĐÂY, TUYỆT ĐỐI KHÔNG BỊA ĐẶT THÊM:\n"
        f"  + Tên khách hàng: {ten_kh}\n"
        f"  + Mã lịch hẹn: {lh.MaLH}\n"
        f"  + Thiết bị: {device}\n"
        f"  + Triệu chứng/Lỗi: {loi}\n"
        f"  + Thời gian hẹn: {gio_str} ngày {ngay_str}\n"
        f"  + Hotline hỗ trợ: 1800 6868\n"
        f"- Nhắc khách hàng khi đến trung tâm vui lòng đưa Mã lịch hẹn ({lh.MaLH}) tại quầy Lễ tân để được tiếp đón ưu tiên.\n"
        f"- Không dùng markdown (**), không viết lời dẫn 'Dưới đây là...', chỉ trả về duy nhất nội dung tin nhắn tiếng Việt hoàn chỉnh."
    )

    draft_text = ""
    # 1. Thử gọi Gemini AI nếu có key
    if ai_service.GEMINI_API_KEY and ai_service.GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            draft_text = ai_service.call_gemini_api(prompt)
        except Exception as e:
            print(f"[AI Warning] Gemini error: {e}")

    # 2. Thử OpenAI nếu chưa có kết quả
    if not draft_text and ai_service.OPENAI_API_KEY and ai_service.OPENAI_API_KEY != "your_openai_api_key_here":
        try:
            draft_text = ai_service.call_openai_api(prompt)
        except Exception as e:
            print(f"[AI Warning] OpenAI error: {e}")

    # 3. Fallback chuẩn xác 100% không bịa đặt nếu không có mạng / key
    if not draft_text:
        draft_text = (
            f"Kính chào Quý khách {ten_kh}, FrogHippo Phone xin trân trọng xác nhận lịch hẹn sửa chữa thiết bị {device} "
            f"của Quý khách vào lúc {gio_str} ngày {ngay_str} (Mã lịch: {lh.MaLH}). "
            f"Tình trạng ghi nhận: {loi}. "
            f"Khi đến cửa hàng, Quý khách vui lòng cung cấp mã {lh.MaLH} tại quầy Lễ tân để được hỗ trợ ưu tiên kiểm tra máy. "
            f"Hotline hỗ trợ miễn phí: 1800 6868. Trung tâm rất hân hạnh được phục vụ Quý khách!"
        )

    # Làm sạch tin nhắn
    clean_draft = re.sub(r"^(dưới đây là|đây là mẫu|tin nhắn gửi khách|mẫu sms:)\s*", "", draft_text.strip(), flags=re.IGNORECASE)
    clean_draft = re.sub(r"[\*#`]", "", clean_draft).strip()

    email_kh = (kh.email if kh and kh.email else "thuha0106206@gmail.com").strip()

    return {
        "maLH": lh.MaLH,
        "tenKhach": ten_kh,
        "sdtKhach": sdt_kh,
        "emailKhach": email_kh,
        "ngayHen": ngay_str,
        "khungGio": gio_str,
        "tinNhan": clean_draft
    }


@router.post("/{id}/gui-tin-nhan", summary="Kết nối gửi thông báo xác nhận lịch hẹn qua Gmail hoặc SMS")
def send_booking_message(id: str, req: LichHenSendMessageRequest, db: Session = Depends(get_db)):
    clean_id = id.strip()
    lh = db.query(models.LichHen).filter(models.LichHen.MaLH.ilike(clean_id)).first()
    if not lh:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy lịch hẹn có mã '{clean_id}'!")
    
    kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == lh.MaKH).first()
    ten_kh = kh.hoTen if kh else "Quý khách"

    # Cập nhật thông tin email/sdt khách nếu người dùng truyền lên
    if req.emailKhach and req.emailKhach.strip():
        clean_email = req.emailKhach.strip()
        if clean_email.lower().endswith("@gmai.com"):
            clean_email = clean_email[:-9] + "@gmail.com"
        if kh:
            kh.email = clean_email
            db.commit()

    if req.sdtKhach and req.sdtKhach.strip() and kh:
        kh.sdt = req.sdtKhach.strip()
        db.commit()

    sdt_thuc = (req.sdtKhach or (kh.sdt if kh else "") or "0900000000").strip()
    email_kh = (req.emailKhach or (kh.email if kh and kh.email else "") or "thuha0106206@gmail.com").strip()
    if email_kh.lower().endswith("@gmai.com"):
        email_kh = email_kh[:-9] + "@gmail.com"

    clean_phone_num = re.sub(r"[^\d+]", "", sdt_thuc)
    channel_name = req.channel or "Gmail"
    res_message = ""
    email_send_result = None
    sms_send_result = None
    gmail_web_url = None
    sms_uri = None

    from urllib.parse import quote

    if channel_name.upper() == "SMS":
        import sms_service
        try:
            sms_send_result = sms_service.send_customer_sms(
                to_phone=clean_phone_num,
                content=req.noiDung or "",
                customer_name=ten_kh,
                ma_phieu=lh.MaLH
            )
            sms_uri = sms_send_result.get("smsUri") or sms_service.make_sms_uri(clean_phone_num, req.noiDung or "")
            res_message = f"Đã kết nối SMS thành công tới số {clean_phone_num}!"
        except Exception as sms_err:
            sms_send_result = {"success": False, "error": str(sms_err)}
            res_message = f"Lỗi gửi SMS: {sms_err}"
            sms_uri = f"sms:{clean_phone_num}?body={quote(req.noiDung or '')}"
    else:  # Gmail
        import email_service
        sub = f"[FrogHippo Phone] Xác Nhận Lịch Hẹn Sửa Chữa #{lh.MaLH}"
        if email_kh and ("@" in email_kh):
            try:
                email_send_result = email_service.send_customer_email(
                    to_email=email_kh,
                    content=req.noiDung or "",
                    customer_name=ten_kh,
                    ma_phieu=lh.MaLH,
                    subject=sub
                )
                gmail_web_url = email_send_result.get("gmailWebUrl") or email_service.make_gmail_web_url(email_kh, sub, req.noiDung or "")
                res_message = f"Đã gửi email thông báo thành công tới {email_kh} qua Gmail!"
            except Exception as err:
                email_send_result = {"success": False, "error": str(err)}
                gmail_web_url = email_service.make_gmail_web_url(email_kh, sub, req.noiDung or "")
                res_message = f"Lỗi gửi Gmail: {err}"
        else:
            gmail_web_url = email_service.make_gmail_web_url("thuha0106206@gmail.com", sub, req.noiDung or "")
            res_message = "Chưa có địa chỉ Email hợp lệ để gửi Gmail!"

    return {
        "success": True,
        "message": res_message,
        "channel": channel_name,
        "emailKhach": email_kh,
        "sdtThuc": clean_phone_num,
        "tenKH": ten_kh,
        "gmailWebUrl": gmail_web_url,
        "smsUri": sms_uri,
        "emailResult": email_send_result,
        "smsResult": sms_send_result
    }


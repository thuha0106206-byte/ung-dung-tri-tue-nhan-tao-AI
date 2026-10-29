import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
import models
import ai_service

router = APIRouter(tags=["Kỹ Thuật Viên"])

# --- SCHEMAS ---
class PhieuSuaUpdate(BaseModel):
    maKTV: Optional[str] = None
    moTaLoi: Optional[str] = None
    ghiChuKTV: Optional[str] = None
    trangThai: Optional[models.TrangThaiEnum] = None

class ChiTietBaoHanhCreate(BaseModel):
    maPhieu: str
    maLK: str
    soLuong: int = 1
    donGia: float
    thoiGianBaoHanh: Optional[str] = "12 Tháng"

class DiagnoseRequest(BaseModel):
    symptoms: Optional[str] = "Điện thoại gặp sự cố cần kiểm tra"
    deviceModel: Optional[str] = "Điện thoại"

class DuyetChuanDoanRequest(BaseModel):
    maPhieu: Optional[str] = None
    nguyenNhan: Optional[str] = "Đã kiểm tra chẩn đoán kỹ thuật"
    ruiRoTiemAn: Optional[str] = ""
    phuongAnDeXuat: Optional[str] = ""
    maKTV: Optional[str] = "NV03"
    tenKTV: Optional[str] = "Lê Văn Cường"
    maLK: Optional[str] = None
    tenLK: Optional[str] = None
    giaLinhKien: Optional[float] = None
    thoiGianBaoHanh: Optional[str] = None

class BaoHanhKtvRequest(BaseModel):
    maPhieu: Optional[str] = None
    loaiBaoHanh: Optional[str] = "Bảo hành sửa chữa"  # "Bảo hành sửa chữa" hoặc "Bảo hành linh kiện"
    thoiHan: Optional[str] = "6 Tháng"
    noiDung: Optional[str] = ""
    chuanDoan: Optional[str] = None
    maKTV: Optional[str] = "NV03"
    tenKTV: Optional[str] = "Lê Văn Cường"
    maLK: Optional[str] = None
    giaLinhKien: Optional[float] = None
    danhSachLinhKien: Optional[List[dict]] = None


# --- ROUTE GIAO DIỆN KỸ THUẬT VIÊN ---
@router.get("/ky-thuat-vien", include_in_schema=False)
def get_ky_thuat_vien_page():
    """Phục vụ trang giao diện chuyên biệt cho Kỹ Thuật Viên."""
    for p in ["frontend/ky_thuat_vien.html", "ky_thuat_vien.html", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "ky_thuat_vien.html")]:
        if os.path.exists(p):
            return FileResponse(
                p,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    raise HTTPException(status_code=404, detail="Không tìm thấy file giao diện ky_thuat_vien.html")


def find_phieu(db: Session, ma_phieu: str):
    """Tìm phiếu linh hoạt: hỗ trợ cả mã có hoặc không có tiền tố '#'."""
    s = (ma_phieu or "").strip()
    if not s:
        return None
    base = s.lstrip('#')
    candidates = list(dict.fromkeys([s, base, f"#{base}"]))
    return db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu.in_(candidates)).first()


def trigger_repair_completion_notification(phieu, db: Session):
    """Tự động sinh tin nhắn hoàn thành bằng AI và gửi email thật về hòm thư khách hàng."""
    try:
        import ai_service
        import email_service
        kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == phieu.maKH).first()
        ten_kh = kh.hoTen if kh else phieu.maKH
        
        # Tính tài chính
        chi_tiets = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == phieu.maPhieu).all()
        tien_lk = sum(ct.donGia * ct.soLuong for ct in chi_tiets)
        tong_hd = tien_lk + 150000.0
        tien_coc = phieu.tienDatCoc or round(tong_hd * 0.3, 0)
        tien_con_lai = max(0.0, tong_hd - tien_coc)

        msg = ai_service.generate_completion_message(
            ma_phieu=phieu.maPhieu.lstrip('#'),
            ten_kh=ten_kh,
            tien_coc=tien_coc,
            tien_con_lai=tien_con_lai,
            channel="Gmail"
        )
        
        # Lưu vào lịch sử thông báo khách hàng
        thong_bao = models.ThongBaoKhachHang(
            maPhieu=phieu.maPhieu,
            kenh="Gmail",
            nguoiGui="Hệ thống (Hoàn thành sửa)",
            noiDung=msg,
            thoiGian=datetime.now()
        )
        db.add(thong_bao)
        db.commit()

        # Nếu khách hàng có email thật, gửi email qua email_service
        email_result = None
        if kh and kh.email and ("@" in kh.email):
            email_result = email_service.send_customer_email(
                to_email=kh.email,
                content=msg,
                customer_name=ten_kh,
                ma_phieu=phieu.maPhieu,
                subject=f"[FrogHippo Phone] Hoàn Thành Sửa Chữa Thiết Bị #{phieu.maPhieu.lstrip('#')} - Mời Quý Khách Nhận Máy"
            )
            print(f"[AUTO NOTIFICATION] Đã tự động gửi email hoàn thành tới: {kh.email} | Phiếu #{phieu.maPhieu}")
        # Gửi thông báo SMS nếu khách hàng có số điện thoại
        sms_result = None
        if kh and kh.sdt:
            try:
                import sms_service
                sms_msg = ai_service.generate_completion_message(
                    ma_phieu=phieu.maPhieu.lstrip('#'),
                    ten_kh=ten_kh,
                    tien_coc=tien_coc,
                    tien_con_lai=tien_con_lai,
                    channel="SMS"
                )
                sms_result = sms_service.send_customer_sms(
                    to_phone=kh.sdt,
                    content=sms_msg,
                    customer_name=ten_kh,
                    ma_phieu=phieu.maPhieu
                )
                thong_bao_sms = models.ThongBaoKhachHang(
                    maPhieu=phieu.maPhieu,
                    kenh="SMS",
                    nguoiGui="Hệ thống (Hoàn thành sửa)",
                    noiDung=sms_msg,
                    thoiGian=datetime.now()
                )
                db.add(thong_bao_sms)
                db.commit()
            except Exception as se:
                print(f"[AUTO NOTIFICATION SMS ERROR] {se}")

        return {"notified": True, "email": kh.email if kh else None, "emailResult": email_result, "smsResult": sms_result, "noiDung": msg}
    except Exception as e:
        print(f"[AUTO NOTIFICATION ERROR] {e}")
        return {"notified": False, "error": str(e)}

# --- API KỸ THUẬT VIÊN ---
@router.get("/api/ktv/danh-sach-phieu", summary="Lấy danh sách phiếu cho KTV")
@router.get("/phieu-sua/", summary="Lấy danh sách phiếu sửa (Có thể lọc theo KTV hoặc Khách hàng)")
def get_ds_phieu(
    maKTV: Optional[str] = Query(None, description="Lọc theo mã KTV"),
    maKH: Optional[str] = Query(None, description="Lọc theo mã/tên khách hàng"),
    db: Session = Depends(get_db)
):
    query = db.query(models.PhieuSuaChua)
    if maKTV:
        query = query.filter(models.PhieuSuaChua.maKTV == maKTV)
    if maKH:
        query = query.filter(models.PhieuSuaChua.maKH == maKH)
    phieus = query.order_by(models.PhieuSuaChua.ngayTao.desc()).all()
    results = []
    for p in phieus:
        kh = p.khachHang
        results.append({
            "maPhieu": p.maPhieu,
            "maKH": p.maKH,
            "tenKH": kh.hoTen if kh else p.maKH,
            "sdtKH": kh.sdt if kh else "",
            "emailKH": kh.email if kh else "",
            "email": kh.email if kh else "",
            "maKTV": p.maKTV,
            "moTaLoi": p.moTaLoi,
            "ghiChuKTV": p.ghiChuKTV,
            "aiTomTat": p.aiTomTat,
            "duyetBaoGia": p.duyetBaoGia,
            "ghiChuKhachHang": p.ghiChuKhachHang,
            "tienDatCoc": p.tienDatCoc,
            "daDatCoc": bool(p.daDatCoc),
            "daDuyetChuanDoan": bool(p.daDuyetChuanDoan),
            "chuanDoanKTV": p.chuanDoanKTV,
            "nguoiDuyetChuanDoan": p.nguoiDuyetChuanDoan,
            "thoiGianDuyetChuanDoan": p.thoiGianDuyetChuanDoan.isoformat() if p.thoiGianDuyetChuanDoan else None,
            "trangThai": p.trangThai.value if hasattr(p.trangThai, 'value') else str(p.trangThai),
            "ngayTao": p.ngayTao.isoformat() if p.ngayTao else None,
            "chiTietList": [
                {
                    "maLK": ct.maLK,
                    "tenLK": ct.linhKien.tenLK if ct.linhKien else ct.maLK,
                    "soLuong": ct.soLuong,
                    "donGia": ct.donGia,
                    "thoiGianBaoHanh": ct.thoiGianBaoHanh
                } for ct in (p.chiTietList or [])
            ]
        })
    return results


@router.put("/phieu-sua/{ma_phieu}/nhan-viec", summary="KTV nhận xử lý phiếu sửa chữa vào danh sách riêng")
def nhan_viec_sua_chua(
    ma_phieu: str, 
    maKTV: str = Query(..., description="Mã KTV nhận máy"),
    db: Session = Depends(get_db)
):
    """KTV bấm nhận máy để tiến hành kiểm tra."""
    phieu = find_phieu(db, ma_phieu)
    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa!")
    phieu.maKTV = maKTV
    if phieu.trangThai == models.TrangThaiEnum.KHOI_TAO:
        phieu.trangThai = models.TrangThaiEnum.DANG_KIEM_TRA
    db.commit()
    db.refresh(phieu)
    return {"message": f"KTV {maKTV} đã nhận phiếu #{ma_phieu} thành công!", "phieu": phieu}


@router.put("/phieu-sua/{ma_phieu}/trang-thai", summary="Đổi trạng thái tiến độ sửa chữa")
def update_trang_thai(ma_phieu: str, trang_thai_moi: models.TrangThaiEnum, db: Session = Depends(get_db)):
    """Cập nhật trạng thái sửa chữa của phiếu."""
    phieu = find_phieu(db, ma_phieu)
    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu")
    
    if phieu.trangThai == models.TrangThaiEnum.DA_THANH_TOAN:
        raise HTTPException(status_code=400, detail="Phiếu đã hoàn tất thanh toán, không thể thay đổi trạng thái nữa!")
    
    if phieu.trangThai == models.TrangThaiEnum.DA_SUA_XONG and trang_thai_moi != models.TrangThaiEnum.DA_THANH_TOAN:
        raise HTTPException(status_code=400, detail="Thiết bị đã sửa xong, chỉ có thể chuyển sang trạng thái 'Đã thanh toán'!")

    if phieu.trangThai == models.TrangThaiEnum.KHOI_TAO and trang_thai_moi in [models.TrangThaiEnum.DA_SUA_XONG, models.TrangThaiEnum.DA_THANH_TOAN]:
        raise HTTPException(status_code=400, detail="Phiếu phải được chuyển sang 'Đang sửa' trước khi hoàn thành!")
    
    phieu.trangThai = trang_thai_moi
    db.commit()

    # Tự động thông báo email khi hoàn thành sửa xong
    auto_notif = None
    if trang_thai_moi == models.TrangThaiEnum.DA_SUA_XONG:
        auto_notif = trigger_repair_completion_notification(phieu, db)

    return {
        "message": "Cập nhật trạng thái thành công",
        "trangThaiMoi": phieu.trangThai,
        "autoNotification": auto_notif
    }


@router.get("/phieu-sua/{ma_phieu}", summary="Xem chi tiết phiếu sửa (tương thích đa method)")
@router.post("/phieu-sua/{ma_phieu}", summary="Cập nhật thông tin phiếu sửa qua POST")
@router.put("/phieu-sua/{ma_phieu}", summary="Cập nhật ghi chú kỹ thuật & thông tin phiếu")
def update_phieu_sua(
    ma_phieu: str, 
    data: Optional[PhieuSuaUpdate] = None, 
    db: Session = Depends(get_db)
):
    target_id = ma_phieu.strip()
    candidate_ids = [target_id, target_id.lstrip('#'), f"#{target_id.lstrip('#')}"]
    phieu = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu.in_(candidate_ids)).first()
    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa")
    
    if data:
        if data.moTaLoi is not None:
            phieu.moTaLoi = data.moTaLoi
        if data.ghiChuKTV is not None:
            phieu.ghiChuKTV = data.ghiChuKTV
        if data.maKTV is not None:
            phieu.maKTV = data.maKTV
        if data.trangThai is not None:
            phieu.trangThai = data.trangThai

        db.commit()
        db.refresh(phieu)
    return phieu


@router.post("/api/ai/diagnose", summary="AI Chẩn đoán lỗi & Báo giá tư vấn sửa chữa")
@router.post("/api/ai/diagnose/", include_in_schema=False)
@router.post("/ai/diagnose", include_in_schema=False)
@router.post("/ai/diagnose/", include_in_schema=False)
@router.post("/api/ai-diagnose", include_in_schema=False)
@router.get("/api/ai/diagnose", include_in_schema=False)
@router.get("/ai/diagnose", include_in_schema=False)
def api_ai_diagnose(
    req: Optional[DiagnoseRequest] = None,
    symptoms: Optional[str] = None,
    deviceModel: Optional[str] = None
):
    """Trợ lý AI chẩn đoán nguyên nhân, rủi ro tiềm ẩn và các phương án sửa chữa (hỗ trợ cả GET & POST)."""
    sym = (req.symptoms if req else None) or symptoms or ""
    dev = (req.deviceModel if req else None) or deviceModel or "Điện thoại"
    
    if not sym.strip():
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp mô tả triệu chứng hư hỏng của thiết bị!")

    try:
        result = ai_service.diagnose_repair_symptoms(
            device_model=dev.strip(),
            symptoms=sym.strip()
        )
        return result
    except Exception as e:
        print(f"[API AI Diagnose Error] {e}")
        raise HTTPException(
            status_code=503,
            detail="Không thể kết nối dịch vụ AI lúc này, vui lòng nhập thủ công."
        )


@router.get("/api/ktv/bao-hanh", include_in_schema=False)
@router.post("/api/ktv/bao-hanh", summary="KTV lưu thông tin loại bảo hành cho phiếu sửa chữa")
@router.put("/api/ktv/bao-hanh", include_in_schema=False)
@router.get("/api/ktv/phieu-sua/{ma_phieu}/bao-hanh", summary="KTV xem thông tin bảo hành (GET)")
@router.post("/api/ktv/phieu-sua/{ma_phieu}/bao-hanh", summary="KTV lưu thông tin loại bảo hành cho phiếu sửa chữa (POST)")
@router.put("/api/ktv/phieu-sua/{ma_phieu}/bao-hanh", summary="KTV lưu thông tin loại bảo hành cho phiếu sửa chữa (PUT)")
def luu_bao_hanh_ktv(
    ma_phieu: Optional[str] = None,
    req: Optional[BaoHanhKtvRequest] = None,
    db: Session = Depends(get_db)
):
    """
    KTV cấp quyền và lựa chọn loại bảo hành:
    - Bảo hành sửa chữa
    - Bảo hành linh kiện
    Kèm thời hạn và nội dung chi tiết. Hỗ trợ đa method GET, POST, PUT.
    """
    target_id = (req.maPhieu if req else None) or ma_phieu or ""
    if not target_id:
        return {
            "success": True,
            "message": "Chính sách bảo hành FrogHippo Phone",
            "loaiBaoHanh": ["Bảo hành sửa chữa", "Bảo hành linh kiện"],
            "thoiHanMacDinh": "6 Tháng"
        }

    candidate_ids = [target_id, target_id.lstrip('#'), f"#{target_id.lstrip('#')}"]
    phieu = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu.in_(candidate_ids)).first()
    if not phieu:
        return {
            "success": False,
            "message": f"Phiếu #{target_id} chưa tồn tại hoặc đã hoàn tất",
            "maPhieu": target_id
        }

    now = datetime.now()

    # Nếu là GET request hoặc req rỗng: chỉ trả về thông tin bảo hành hiện có
    if not req or not req.noiDung:
        return {
            "success": True,
            "maPhieu": phieu.maPhieu,
            "ghiChuKTV": phieu.ghiChuKTV or "",
            "chuanDoanKTV": phieu.chuanDoanKTV or "",
            "daDuyetChuanDoan": phieu.daDuyetChuanDoan
        }

    bh_text = f"[{req.loaiBaoHanh} - Thời hạn: {req.thoiHan}] {req.noiDung.strip() if req.noiDung else 'Áp dụng chính sách bảo hành PhoneCare'}"
    
    # Cập nhật thông tin vào phiếu
    current_notes = phieu.ghiChuKTV or ""
    import re
    if "[Bảo hành" in current_notes:
        current_notes = re.sub(r"\[Bảo hành[^\]]*\].*", "", current_notes, flags=re.DOTALL).strip()
    
    phieu.ghiChuKTV = f"{current_notes}\n{bh_text}".strip() if current_notes else bh_text

    # Cập nhật chẩn đoán KTV nếu có gửi kèm
    if req.chuanDoan and req.chuanDoan.strip():
        phieu.chuanDoanKTV = req.chuanDoan.strip()
        phieu.daDuyetChuanDoan = True
        phieu.thoiGianDuyetChuanDoan = now
        phieu.nguoiDuyetChuanDoan = req.tenKTV or "Lê Văn Cường (NV03)"

    # Tự động gán linh kiện kho vào chi tiết phiếu (hỗ trợ nhiều linh kiện cùng lúc)
    parts_to_process = []
    if req.danhSachLinhKien and isinstance(req.danhSachLinhKien, list) and len(req.danhSachLinhKien) > 0:
        parts_to_process = req.danhSachLinhKien
    elif req.maLK and req.maLK.strip():
        parts_to_process = [{
            "maLK": req.maLK.strip(),
            "soLuong": 1,
            "donGia": req.giaLinhKien,
            "thoiGianBaoHanh": req.thoiHan or "12 Tháng"
        }]

    for p_item in parts_to_process:
        m_lk = (p_item.get("maLK") or "").strip()
        if not m_lk:
            continue
        lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == m_lk).first()
        if not lk:
            continue

        sl = int(p_item.get("soLuong", 1) or 1)
        gia_item = p_item.get("donGia")
        gia_ap_dung = float(gia_item) if gia_item is not None and float(gia_item) > 0 else float(lk.giaBan)
        bh_item = p_item.get("thoiGianBaoHanh") or req.thoiHan or "12 Tháng"

        ct = db.query(models.ChiTietSuaChua).filter(
            models.ChiTietSuaChua.maPhieu == phieu.maPhieu,
            models.ChiTietSuaChua.maLK == lk.maLK
        ).first()

        if not ct:
            if lk.soLuongTon < sl or lk.soLuongTon <= 0:
                raise HTTPException(status_code=400, detail=f"Linh kiện {lk.tenLK} đã hết hàng trong kho (chỉ còn {lk.soLuongTon})!")
            ct_new = models.ChiTietSuaChua(
                maPhieu=phieu.maPhieu,
                maLK=lk.maLK,
                soLuong=sl,
                donGia=gia_ap_dung,
                thoiGianBaoHanh=bh_item
            )
            db.add(ct_new)
            lk.soLuongTon -= sl
        else:
            diff_sl = sl - ct.soLuong
            ct.soLuong = sl
            ct.donGia = gia_ap_dung
            ct.thoiGianBaoHanh = bh_item
            if diff_sl > 0:
                if lk.soLuongTon < diff_sl:
                    raise HTTPException(status_code=400, detail=f"Linh kiện {lk.tenLK} không đủ tồn kho (chỉ còn {lk.soLuongTon})!")
                lk.soLuongTon -= diff_sl

    # Đồng bộ thời gian bảo hành vào chi tiết linh kiện nếu chọn Bảo hành linh kiện
    if req.loaiBaoHanh == "Bảo hành linh kiện":
        chi_tiets = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == phieu.maPhieu).all()
        for ct in chi_tiets:
            ct.thoiGianBaoHanh = req.thoiHan

    # Ghi nhận nhật ký thông báo
    thong_bao = models.ThongBaoKhachHang(
        maPhieu=phieu.maPhieu,
        kenh="Nội Bộ Kỹ Thuật",
        nguoiGui=f"KTV {req.tenKTV or phieu.nguoiDuyetChuanDoan or 'Kỹ thuật viên'}",
        noiDung=f"ĐÃ LƯU BẢO HÀNH: {bh_text}",
        thoiGian=now
    )
    db.add(thong_bao)
    db.commit()
    db.refresh(phieu)

    return {
        "success": True,
        "message": f"Đã lưu thành công {req.loaiBaoHanh} ({req.thoiHan}) cho phiếu #{phieu.maPhieu}!",
        "maPhieu": phieu.maPhieu,
        "loaiBaoHanh": req.loaiBaoHanh,
        "thoiHan": req.thoiHan,
        "noiDung": req.noiDung,
        "ghiChuKTV": phieu.ghiChuKTV
    }


@router.get("/api/ktv/duyet-chuan-doan/{ma_phieu}", summary="Xem thông tin duyệt chẩn đoán (GET)")
@router.post("/api/ktv/duyet-chuan-doan/{ma_phieu}", summary="Kỹ thuật viên kiểm tra & Phê duyệt chẩn đoán lỗi để công khai cho khách (POST)")
@router.put("/api/ktv/duyet-chuan-doan/{ma_phieu}", summary="Kỹ thuật viên kiểm tra & Phê duyệt chẩn đoán lỗi (PUT)")
def duyet_chuan_doan_ktv(
    ma_phieu: str,
    req: Optional[DuyetChuanDoanRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Quy trình kiểm soát chất lượng & tối ưu 1 bước:
    - Kỹ thuật viên kiểm tra, phê duyệt chẩn đoán, cảnh báo rủi ro và phương án giá.
    - Tìm kiếm phiếu linh hoạt hỗ trợ tiền tố '#' hoặc không có '#'.
    - Tự động gán linh kiện kho vào chi tiết sửa chữa của phiếu nếu KTV chỉ định.
    - Hỗ trợ cả GET, POST, PUT an toàn tuyệt đối.
    """
    # Xây dựng danh sách các ID ứng viên để tìm kiếm chính xác 100%
    target_raw = [ma_phieu or "", (req.maPhieu if req else None) or ""]
    candidate_ids = []
    for r in target_raw:
        s = str(r).strip()
        if s:
            candidate_ids.append(s)
            candidate_ids.append(s.lstrip('#'))
            candidate_ids.append(f"#{s.lstrip('#')}")
    candidate_ids = list(dict.fromkeys(candidate_ids))

    phieu = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu.in_(candidate_ids)).first()
    if not phieu:
        return {
            "success": False,
            "message": f"Không tìm thấy phiếu sửa chữa (Mã: {ma_phieu})",
            "maPhieu": ma_phieu
        }

    now = datetime.now()

    # Trường hợp GET request hoặc req rỗng: trả về kết quả chẩn đoán hiện có của phiếu
    if not req or not req.nguyenNhan:
        return {
            "success": True,
            "maPhieu": phieu.maPhieu,
            "daDuyetChuanDoan": phieu.daDuyetChuanDoan,
            "chuanDoanKTV": phieu.chuanDoanKTV,
            "ghiChuKTV": phieu.ghiChuKTV,
            "nguoiDuyet": phieu.nguoiDuyetChuanDoan,
            "thoiGianDuyet": phieu.thoiGianDuyetChuanDoan.strftime("%H:%M %d/%m/%Y") if phieu.thoiGianDuyetChuanDoan else None
        }

    noi_dung_chuan_doan = f"Nguyên nhân: {req.nguyenNhan.strip()}"
    if req.ruiRoTiemAn and req.ruiRoTiemAn.strip():
        noi_dung_chuan_doan += f" | Cảnh báo rủi ro: {req.ruiRoTiemAn.strip()}"
    if req.phuongAnDeXuat and req.phuongAnDeXuat.strip():
        noi_dung_chuan_doan += f" | Phương án: {req.phuongAnDeXuat.strip()}"

    # Cập nhật trạng thái duyệt
    phieu.chuanDoanKTV = noi_dung_chuan_doan
    phieu.ghiChuKTV = req.nguyenNhan.strip()
    phieu.daDuyetChuanDoan = True
    phieu.nguoiDuyetChuanDoan = req.tenKTV or req.maKTV or "Kỹ thuật viên"
    phieu.thoiGianDuyetChuanDoan = now

    # Tự động cập nhật KTV phụ trách nếu chưa có
    if not phieu.maKTV and req.maKTV:
        phieu.maKTV = req.maKTV

    # Nếu phiếu ở Khởi tạo -> chuyển sang Đang kiểm tra
    if phieu.trangThai == models.TrangThaiEnum.KHOI_TAO:
        phieu.trangThai = models.TrangThaiEnum.DANG_KIEM_TRA

    # TỰ ĐỘNG GÁN LINH KIỆN KHO VÀO PHIẾU (Tối ưu quy trình 1 bước cho KTV)
    if req.maLK and req.maLK.strip():
        lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == req.maLK.strip()).first()
        if lk:
            ct = db.query(models.ChiTietSuaChua).filter(
                models.ChiTietSuaChua.maPhieu == phieu.maPhieu,
                models.ChiTietSuaChua.maLK == lk.maLK
            ).first()
            gia_ap_dung = req.giaLinhKien if req.giaLinhKien is not None and req.giaLinhKien > 0 else lk.giaBan
            bh_ap_dung = req.thoiGianBaoHanh or "12 Tháng"
            if not ct:
                ct_new = models.ChiTietSuaChua(
                    maPhieu=phieu.maPhieu,
                    maLK=lk.maLK,
                    soLuong=1,
                    donGia=float(gia_ap_dung),
                    thoiGianBaoHanh=bh_ap_dung
                )
                db.add(ct_new)
                if lk.soLuongTon > 0:
                    lk.soLuongTon -= 1
            else:
                ct.donGia = float(gia_ap_dung)
                ct.thoiGianBaoHanh = bh_ap_dung

    # Ghi nhận nhật ký thông báo nội bộ
    thong_bao = models.ThongBaoKhachHang(
        maPhieu=phieu.maPhieu,
        kenh="Nội Bộ Kỹ Thuật",
        nguoiGui=f"KTV {phieu.nguoiDuyetChuanDoan}",
        noiDung=f"ĐÃ PHÊ DUYỆT CHẨN ĐOÁN LỖI: {req.nguyenNhan.strip()}",
        thoiGian=now
    )
    db.add(thong_bao)
    db.commit()
    db.refresh(phieu)

    return {
        "success": True,
        "message": f"Kỹ thuật viên {phieu.nguoiDuyetChuanDoan} đã PHÊ DUYỆT chẩn đoán lỗi cho phiếu #{phieu.maPhieu}. Kết quả đã sẵn sàng công khai cho khách hàng!",
        "maPhieu": phieu.maPhieu,
        "daDuyetChuanDoan": phieu.daDuyetChuanDoan,
        "chuanDoanKTV": phieu.chuanDoanKTV,
        "nguoiDuyet": phieu.nguoiDuyetChuanDoan,
        "thoiGianDuyet": phieu.thoiGianDuyetChuanDoan.strftime("%H:%M %d/%m/%Y")
    }


@router.post("/phieu-sua/{ma_phieu}/ai-tom-tat", summary="AI Tóm tắt lỗi thiết bị cho KTV")
def ai_tom_tat_phieu_sua(ma_phieu: str, db: Session = Depends(get_db)):
    """AI đọc mô tả lỗi và ghi chú KTV, dịch lại thành ngôn ngữ phổ thông dễ hiểu."""
    phieu = find_phieu(db, ma_phieu)
    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa!")
    tom_tat = ai_service.summarize_repair_ticket(phieu.moTaLoi or "", phieu.ghiChuKTV or "")
    phieu.aiTomTat = tom_tat
    db.commit()
    return {"message": "Đã tóm tắt bằng AI thành công", "aiTomTat": tom_tat}


# --- LINH KIỆN VÀ BẢO HÀNH ---
@router.get("/linh-kien/", summary="Xem danh sách linh kiện trong kho")
def get_ds_linh_kien(db: Session = Depends(get_db)):
    return db.query(models.LinhKien).all()


@router.post("/bao-hanh-chi-tiet/", summary="Gán linh kiện bảo hành/thay thế vào phiếu")
def add_bao_hanh_chi_tiet(item: ChiTietBaoHanhCreate, db: Session = Depends(get_db)):
    target_id = item.maPhieu or ""
    candidate_ids = [target_id, target_id.lstrip('#'), f"#{target_id.lstrip('#')}"]
    phieu = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu.in_(candidate_ids)).first()
    if not phieu:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy phiếu sửa #{item.maPhieu}")
    
    # Kiểm tra tồn kho linh kiện
    lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == item.maLK).first()
    if lk:
        if lk.soLuongTon < item.soLuong or lk.soLuongTon <= 0:
            raise HTTPException(status_code=400, detail=f"Linh kiện {lk.tenLK} đã hết hàng trong kho (chỉ còn {lk.soLuongTon})!")
        lk.soLuongTon -= item.soLuong

    # Kiểm tra xem linh kiện đã có trong phiếu chưa
    existing_detail = db.query(models.ChiTietSuaChua).filter(
        models.ChiTietSuaChua.maPhieu == phieu.maPhieu,
        models.ChiTietSuaChua.maLK == item.maLK
    ).first()

    if existing_detail:
        existing_detail.soLuong += item.soLuong
        existing_detail.donGia = item.donGia
        existing_detail.thoiGianBaoHanh = item.thoiGianBaoHanh or existing_detail.thoiGianBaoHanh
        db.commit()
        db.refresh(existing_detail)
        return {"message": "Đã cập nhật số lượng linh kiện trong phiếu", "data": item}

    data = item.model_dump() if hasattr(item, "model_dump") else item.dict()
    data["maPhieu"] = phieu.maPhieu  # Đồng bộ chính xác mã phiếu trong CSDL
    model_columns = {c.key for c in models.ChiTietSuaChua.__table__.columns}
    filtered_data = {k: v for k, v in data.items() if k in model_columns}

    new_detail = models.ChiTietSuaChua(**filtered_data)
    db.add(new_detail)
    db.commit()
    db.refresh(new_detail)
    return {"message": "Đã thêm linh kiện bảo hành vào phiếu", "data": item}


@router.get("/bao-hanh-chi-tiet/", summary="Xem chi tiết linh kiện qua query param")
@router.get("/bao-hanh-chi-tiet/{ma_phieu}", summary="Xem chi tiết linh kiện của 1 phiếu")
def get_chi_tiet_bao_hanh(
    ma_phieu: Optional[str] = None,
    maPhieu: Optional[str] = Query(None, description="Mã phiếu dạng query param"),
    db: Session = Depends(get_db)
):
    target = ma_phieu or maPhieu or ""
    candidate_ids = [target, target.lstrip('#'), f"#{target.lstrip('#')}"] if target else []
    
    if candidate_ids:
        details = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu.in_(candidate_ids)).all()
    else:
        details = db.query(models.ChiTietSuaChua).all()

    result = []
    for d in details:
        ten_lk = d.linhKien.tenLK if d.linhKien else d.maLK
        result.append({
            "maPhieu": d.maPhieu,
            "maLK": d.maLK,
            "tenLK": ten_lk,
            "soLuong": d.soLuong,
            "donGia": d.donGia,
            "thanhTien": d.soLuong * d.donGia,
            "thoiGianBaoHanh": d.thoiGianBaoHanh or "12 Tháng"
        })
    return result


@router.delete("/bao-hanh-chi-tiet/{ma_phieu}/{ma_lk}", summary="Xóa linh kiện khỏi phiếu và hoàn lại kho")
def delete_bao_hanh_chi_tiet(ma_phieu: str, ma_lk: str, db: Session = Depends(get_db)):
    candidate_ids = [ma_phieu, ma_phieu.lstrip('#'), f"#{ma_phieu.lstrip('#')}"]
    ct = db.query(models.ChiTietSuaChua).filter(
        models.ChiTietSuaChua.maPhieu.in_(candidate_ids),
        models.ChiTietSuaChua.maLK == ma_lk
    ).first()
    if not ct:
        raise HTTPException(status_code=404, detail="Không tìm thấy linh kiện trong phiếu này")
    
    lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == ma_lk).first()
    if lk:
        lk.soLuongTon += ct.soLuong
        
    db.delete(ct)

    db.commit()
    return {"message": "Đã xóa linh kiện khỏi phiếu và hoàn lại kho", "maLK": ma_lk}

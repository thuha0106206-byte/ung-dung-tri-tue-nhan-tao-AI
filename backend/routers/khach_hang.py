import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
import models
import ai_service

router = APIRouter(tags=["Phân hệ Khách Hàng"])

# --- SCHEMAS ---
class ChatbotKhachHangRequest(BaseModel):
    message: str
    maPhieu: Optional[str] = None
    fileData: Optional[str] = None
    fileName: Optional[str] = None
    fileMimeType: Optional[str] = None

class DuyetBaoGiaRequest(BaseModel):
    maPhieu: Optional[str] = None
    duyetBaoGia: Optional[str] = "DONG_Y" # "DONG_Y" hoac "TU_CHOI"
    ghiChu: Optional[str] = ""

class DanhGiaRequest(BaseModel):
    maPhieu: str
    soSao: int = 5
    tieuChi: Optional[str] = "Chất lượng tốt"
    noiDung: Optional[str] = ""
    tenKhachHang: Optional[str] = ""
    sdt: Optional[str] = ""

class KhieuNaiRequest(BaseModel):
    maPhieu: Optional[str] = ""
    hoTen: str
    sdt: str
    noiDung: str
    loai: Optional[str] = "Góp ý"

def find_phieu(db: Session, ma_phieu: str):
    """Tìm phiếu linh hoạt: hỗ trợ cả mã có hoặc không có tiền tố '#'."""
    s = (ma_phieu or "").strip()
    if not s:
        return None
    base = s.lstrip('#')
    candidates = list(dict.fromkeys([s, base, f"#{base}", f"##{base}"]))
    return db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu.in_(candidates)).first()

# --- ROUTE PHỤC VỤ TRANG KHÁCH HÀNG ---
@router.get("/khach-hang", include_in_schema=False)
@router.get("/khach_hang.html", include_in_schema=False)
def serve_khach_hang_page():
    for p in ["frontend/khach_hang.html", "khach_hang.html", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "khach_hang.html")]:
        if os.path.exists(p):
            return FileResponse(
                p,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    for p in ["frontend/index.html", "index.html", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "index.html")]:
        if os.path.exists(p):
            return FileResponse(
                p,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    return {"message": "Cổng Khách Hàng FrogHippo Phone"}


# --- 1. TRA CỨU TIẾN ĐỘ, BẢO HÀNH & LỊCH SỬ SỬA CHỮA ---
@router.get("/api/khach-hang/tra-cuu", summary="Tra cứu toàn diện thông tin phiếu sửa chữa cho khách")
def tra_cuu_khach_hang(
    q: str = Query(..., description="Mã phiếu (VD: PS01) hoặc Số điện thoại khách hàng"),
    db: Session = Depends(get_db)
):
    query_str = q.strip()
    if not query_str:
        raise HTTPException(status_code=400, detail="Vui lòng nhập Mã phiếu hoặc Số điện thoại!")

    # Hỗ trợ mã mẫu gợi ý (PS01, PS02, LH001) nếu chưa có trong DB
    if query_str.upper() in ["LH001", "LH002", "LH1"]:
        existing_lh = db.query(models.LichHen).filter(models.LichHen.MaLH.ilike(query_str)).first()
        if not existing_lh:
            latest_lh = db.query(models.LichHen).order_by(models.LichHen.NgayTao.desc()).first()
            if latest_lh:
                query_str = latest_lh.MaLH

    # 0. Nếu tra cứu theo Mã Lịch Hẹn (LH...)
    if query_str.upper().startswith("LH"):
        lh = db.query(models.LichHen).filter(models.LichHen.MaLH.ilike(query_str)).first()
        if lh:
            kh = db.query(models.KhachHang).filter(models.KhachHang.maKH == lh.MaKH).first()
            return {
                "type": "lich_hen",
                "lichHen": {
                    "maLH": lh.MaLH,
                    "maKH": lh.MaKH,
                    "tenKhachHang": kh.hoTen if kh else lh.MaKH,
                    "sdt": kh.sdt if kh else "",
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

    # 1. Tìm phiếu theo mã phiếu
    target_code = query_str
    if target_code.upper() in ["PS01", "PS02", "#PS01", "#PS02"]:
        sample_p = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu.ilike(target_code)).first()
        if not sample_p:
            first_p = db.query(models.PhieuSuaChua).order_by(models.PhieuSuaChua.ngayTao.desc()).first()
            if first_p:
                target_code = first_p.maPhieu

    phieu = db.query(models.PhieuSuaChua).filter(
        models.PhieuSuaChua.maPhieu.ilike(target_code)
    ).first()

    # 2. Nếu không tìm thấy theo mã phiếu, tìm theo SĐT hoặc mã KH
    khach = None
    if not phieu:
        matching_khs = db.query(models.KhachHang).filter(
            or_(
                models.KhachHang.sdt == query_str,
                models.KhachHang.maKH.ilike(query_str)
            )
        ).all()

        for k in matching_khs:
            p = db.query(models.PhieuSuaChua).filter(
                models.PhieuSuaChua.maKH == k.maKH
            ).order_by(models.PhieuSuaChua.ngayTao.desc()).first()
            if p:
                phieu = p
                khach = k
                break

    if not phieu:
        # Kiểm tra xem có lịch hẹn nào của khách hàng này không
        if matching_khs:
            for k in matching_khs:
                lh = db.query(models.LichHen).filter(models.LichHen.MaKH == k.maKH).order_by(models.LichHen.NgayTao.desc()).first()
                if lh:
                    return {
                        "type": "lich_hen",
                        "lichHen": {
                            "maLH": lh.MaLH,
                            "maKH": lh.MaKH,
                            "tenKhachHang": k.hoTen,
                            "sdt": k.sdt or "",
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
        raise HTTPException(
            status_code=404, 
            detail=f"Không tìm thấy thông tin sửa chữa hoặc lịch hẹn cho '{query_str}'. Vui lòng kiểm tra lại Mã phiếu, Mã lịch hẹn hoặc Số điện thoại!"
        )

    # 3. Lấy thông tin khách hàng
    if not khach:
        khach = db.query(models.KhachHang).filter(models.KhachHang.maKH == phieu.maKH).first()

    # 4. Lấy chi tiết linh kiện & bảo hành
    chi_tiet_db = db.query(models.ChiTietSuaChua).filter(models.ChiTietSuaChua.maPhieu == phieu.maPhieu).all()
    parts_list = []
    tong_tien_linh_kien = 0.0
    for ct in chi_tiet_db:
        lk = db.query(models.LinhKien).filter(models.LinhKien.maLK == ct.maLK).first()
        thanh_tien = float(ct.soLuong) * float(ct.donGia)
        tong_tien_linh_kien += thanh_tien
        parts_list.append({
            "maLK": ct.maLK,
            "tenLK": lk.tenLK if lk else ct.maLK,
            "soLuong": ct.soLuong,
            "donGia": ct.donGia,
            "thanhTien": thanh_tien,
            "thoiGianBaoHanh": ct.thoiGianBaoHanh or "12 Tháng"
        })

    # Tiền công niêm yết
    tien_cong = 150000.0
    # Kiểm tra hóa đơn
    hoa_don = db.query(models.HoaDon).filter(models.HoaDon.maPhieu == phieu.maPhieu).first()
    if hoa_don:
        tien_cong = hoa_don.tienCong
        tong_chi_phi = hoa_don.tongTien
    else:
        tong_chi_phi = tong_tien_linh_kien + tien_cong

    # 5. KTV phụ trách
    ktv = None
    if phieu.maKTV:
        ktv = db.query(models.NhanVien).filter(models.NhanVien.maNV == phieu.maKTV).first()

    # 6. Danh sách thông báo đã gửi
    thong_bao_db = db.query(models.ThongBaoKhachHang).filter(
        models.ThongBaoKhachHang.maPhieu == phieu.maPhieu
    ).order_by(models.ThongBaoKhachHang.thoiGian.desc()).all()
    thong_bao_list = [
        {
            "id": tb.id,
            "kenh": tb.kenh,
            "nguoiGui": tb.nguoiGui,
            "noiDung": tb.noiDung,
            "thoiGian": tb.thoiGian.strftime("%H:%M %d/%m/%Y") if tb.thoiGian else ""
        } for tb in thong_bao_db
    ]

    # 7. Danh sách đánh giá đã có
    danh_gia_db = db.query(models.DanhGiaDichVu).filter(
        models.DanhGiaDichVu.maPhieu == phieu.maPhieu
    ).order_by(models.DanhGiaDichVu.thoiGian.desc()).all()
    danh_gia_list = [
        {
            "id": dg.id,
            "soSao": dg.soSao,
            "tieuChi": dg.tieuChi,
            "noiDung": dg.noiDung,
            "thoiGian": dg.thoiGian.strftime("%d/%m/%Y %H:%M") if dg.thoiGian else ""
        } for dg in danh_gia_db
    ]

    # 8. Lịch sử các lần sửa chữa trước của khách hàng này
    lich_su_list = []
    if phieu.maKH:
        other_tickets = db.query(models.PhieuSuaChua).filter(
            models.PhieuSuaChua.maKH == phieu.maKH,
            models.PhieuSuaChua.maPhieu != phieu.maPhieu
        ).order_by(models.PhieuSuaChua.ngayTao.desc()).all()

        for ot in other_tickets:
            trang_thai_str = ot.trangThai.value if hasattr(ot.trangThai, 'value') else str(ot.trangThai)
            lich_su_list.append({
                "maPhieu": ot.maPhieu,
                "moTaLoi": ot.moTaLoi,
                "trangThai": trang_thai_str,
                "ngayTao": ot.ngayTao.strftime("%d/%m/%Y") if ot.ngayTao else ""
            })

    trang_thai_hien_tai = phieu.trangThai.value if hasattr(phieu.trangThai, 'value') else str(phieu.trangThai)

    return {
        "phieu": {
            "maPhieu": phieu.maPhieu,
            "maKH": phieu.maKH,
            "tenKhachHang": khach.hoTen if khach else phieu.maKH,
            "sdt": khach.sdt if khach else "",
            "diaChi": khach.diaChi if khach else "",
            "maKTV": phieu.maKTV,
            "tenKTV": ktv.hoTen if ktv else "Đang phân công",
            "moTaLoi": phieu.moTaLoi,
            "daDuyetChuanDoan": bool(phieu.daDuyetChuanDoan),
            "ghiChuKTV": (phieu.chuanDoanKTV or phieu.ghiChuKTV) if phieu.daDuyetChuanDoan else "⏳ Đang chờ Kỹ thuật viên kiểm tra & phê duyệt nguyên nhân",
            "chuanDoanKTV": phieu.chuanDoanKTV if phieu.daDuyetChuanDoan else None,
            "nguoiDuyetChuanDoan": phieu.nguoiDuyetChuanDoan if phieu.daDuyetChuanDoan else None,
            "thoiGianDuyetChuanDoan": phieu.thoiGianDuyetChuanDoan.strftime("%H:%M %d/%m/%Y") if (phieu.thoiGianDuyetChuanDoan and phieu.daDuyetChuanDoan) else None,
            "aiTomTat": phieu.aiTomTat if phieu.daDuyetChuanDoan else "AI sẽ tổng hợp sau khi KTV duyệt nguyên nhân.",
            "trangThai": trang_thai_hien_tai,
            "duyetBaoGia": phieu.duyetBaoGia or "CHO_DUYET",
            "ghiChuKhachHang": phieu.ghiChuKhachHang or "",
            "ngayTao": phieu.ngayTao.strftime("%d/%m/%Y %H:%M") if phieu.ngayTao else ""
        },
        "chiTietGia": {
            "parts": parts_list,
            "tienLinhKien": tong_tien_linh_kien,
            "tienCong": tien_cong,
            "tongChiPhi": tong_chi_phi,
            "daThanhToan": hoa_don is not None,
            "phuongThuc": hoa_don.phuongThuc if hoa_don else ""
        },
        "thongBaoList": thong_bao_list,
        "danhGiaList": danh_gia_list,
        "lichSuSuaChua": lich_su_list
    }


# --- 2. XÁC NHẬN / TỪ CHỐI DUYỆT BÁO GIÁ ---
@router.post("/api/khach-hang/duyet-bao-gia", summary="Khách hàng xác nhận báo giá (maPhieu trong body)")
@router.post("/api/khach-hang/duyet-bao-gia/", summary="Khách hàng xác nhận báo giá (fallback URL)")
@router.post("/api/khach-hang/duyet-bao-gia/{ma_phieu}", summary="Khách hàng xác nhận hoặc từ chối báo giá trực tuyến")
def duyet_bao_gia_online(
    req: DuyetBaoGiaRequest,
    ma_phieu: Optional[str] = None,
    db: Session = Depends(get_db)
):
    target_code = ma_phieu or req.maPhieu
    phieu = None
    if target_code:
        phieu = find_phieu(db, target_code)

    # Nếu không tìm thấy bằng code, thử tìm phiếu đang chờ duyệt gần nhất
    if not phieu:
        phieu = db.query(models.PhieuSuaChua).filter(
            models.PhieuSuaChua.duyetBaoGia.in_(["CHO_DUYET", "CHUA_DUYET", None])
        ).order_by(models.PhieuSuaChua.ngayTao.desc()).first()

    if not phieu:
        phieu = db.query(models.PhieuSuaChua).order_by(models.PhieuSuaChua.ngayTao.desc()).first()

    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa!")

    decision = (req.duyetBaoGia or "DONG_Y").upper()
    if decision not in ["DONG_Y", "TU_CHOI"]:
        raise HTTPException(status_code=400, detail="Trạng thái duyệt phải là 'DONG_Y' hoặc 'TU_CHOI'!")

    phieu.duyetBaoGia = decision
    if req.ghiChu:
        phieu.ghiChuKhachHang = req.ghiChu

    # Tự động cập nhật trạng thái phiếu nếu khách đồng ý
    if decision == "DONG_Y":
        if phieu.trangThai in [models.TrangThaiEnum.KHOI_TAO, models.TrangThaiEnum.DANG_KIEM_TRA]:
            phieu.trangThai = models.TrangThaiEnum.DANG_SUA

    now = datetime.now()
    # Ghi nhận vào lịch sử thông báo nội bộ
    thong_bao = models.ThongBaoKhachHang(
        maPhieu=phieu.maPhieu,
        kenh="Cổng Khách Hàng",
        nguoiGui="Khách Hàng Trực Tuyến",
        noiDung=f"Khách hàng đã {'ĐỒNG Ý' if decision == 'DONG_Y' else 'TỪ CHỐI'} duyệt báo giá trực tuyến!" + (f" Ghi chú: {req.ghiChu}" if req.ghiChu else ""),
        thoiGian=now
    )
    db.add(thong_bao)
    db.commit()
    db.refresh(phieu)

    msg = "Quý khách đã ĐỒNG Ý báo giá sửa chữa thành công! Kỹ thuật viên sẽ tiến hành sửa chữa ngay." if decision == "DONG_Y" else "Hệ thống đã ghi nhận Quý khách TỪ CHỐI báo giá. Chuyên viên sẽ liên hệ lại để tư vấn phương án phù hợp."
    
    return {
        "success": True,
        "message": msg,
        "maPhieu": phieu.maPhieu,
        "duyetBaoGia": phieu.duyetBaoGia,
        "trangThai": phieu.trangThai.value if hasattr(phieu.trangThai, 'value') else str(phieu.trangThai)
    }


# --- 3. ĐÁNH GIÁ DỊCH VỤ & CHẤM ĐIỂM KTV ---
@router.post("/api/khach-hang/danh-gia", summary="Khách hàng chấm điểm và đánh giá dịch vụ")
def gui_danh_gia_dich_vu(
    req: DanhGiaRequest, 
    db: Session = Depends(get_db)
):
    phieu = db.query(models.PhieuSuaChua).filter(models.PhieuSuaChua.maPhieu == req.maPhieu).first()
    if not phieu:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu sửa chữa!")

    if req.soSao < 1 or req.soSao > 5:
        raise HTTPException(status_code=400, detail="Số sao đánh giá phải từ 1 đến 5!")

    danh_gia = models.DanhGiaDichVu(
        maPhieu=req.maPhieu,
        maKH=phieu.maKH,
        tenKhachHang=req.tenKhachHang or phieu.maKH,
        sdt=req.sdt or "",
        soSao=req.soSao,
        tieuChi=req.tieuChi or "Dịch vụ tốt",
        noiDung=req.noiDung or "",
        thoiGian=datetime.now()
    )
    db.add(danh_gia)
    db.commit()
    db.refresh(danh_gia)

    return {
        "success": True,
        "message": "Cảm ơn Quý khách đã gửi đánh giá! Ý kiến của Quý khách giúp trung tâm nâng cao chất lượng phục vụ.",
        "danhGiaId": danh_gia.id
    }


# --- 4. GỬI PHẢN HỒI / KHIẾU NẠI ---
@router.post("/api/khach-hang/khieu-nai", summary="Khách hàng gửi khiếu nại hoặc phản hồi")
def gui_khieu_nai_phan_hoi(
    req: KhieuNaiRequest,
    db: Session = Depends(get_db)
):
    now = datetime.now()
    thong_bao = models.ThongBaoKhachHang(
        maPhieu=req.maPhieu or "KHIEU_NAI",
        kenh="Phản hồi khách hàng",
        nguoiGui=f"Khách hàng {req.hoTen} ({req.sdt})",
        noiDung=f"[{req.loai}] {req.noiDung}",
        thoiGian=now
    )
    db.add(thong_bao)
    db.commit()
    db.refresh(thong_bao)

    return {
        "success": True,
        "message": "Đã tiếp nhận phản hồi của Quý khách! Quản lý trung tâm sẽ liên hệ xử lý trong vòng 30 phút."
    }


# --- 5. AI CHATBOT TƯ VẤN KHÁCH HÀNG (KẾT HỢP BỘ QUY CHUẨN & CHUẨN ĐOÁN KTV) ---
@router.post("/api/khach-hang/chatbot", summary="Chatbot tư vấn khách hàng dựa trên Bộ Quy Chuẩn & Chuẩn Đoán KTV")
def chatbot_khach_hang(
    req: ChatbotKhachHangRequest,
    db: Session = Depends(get_db)
):
    """
    Chatbot giải đáp thắc mắc cho khách hàng:
    - Nếu khách đang xem phiếu sửa chữa: AI đọc Chuẩn đoán KTV (ghiChuKTV), giải thích nguyên nhân,
      rủi ro nếu không sửa, phương án xử lý, linh kiện thay thế và chính sách bảo hành.
    - Nếu khách hỏi chung: AI dựa trên Bộ Quy Chuẩn Kỹ Thuật và CSDL linh kiện thực tế để trả lời.
    """
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
        "maPhieu": phieu_info.get("maPhieu") if phieu_info else None,
        "coChuanDoanKTV": bool(phieu_info and phieu_info.get("ghiChuKTV"))
    }

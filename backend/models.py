from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database import Base

# Các trạng thái xử lý phiếu sửa chữa
class TrangThaiEnum(str, enum.Enum):
    KHOI_TAO = "KhoiTao"
    DANG_KIEM_TRA = "DangKiemTra"
    CHO_LINH_KIEN = "ChoLinhKien"
    DANG_SUA = "DangSua"
    DA_SUA_XONG = "DaSuaXong"
    DA_THANH_TOAN = "DaThanhToan"

class ChucVuEnum(str, enum.Enum):
    ADMIN = "Admin"
    LE_TAN = "Lễ tân"
    KY_THUAT_VIEN = "Kỹ thuật viên"
    THU_NGAN = "Thu ngân"

# 1. Bảng Khách Hàng
class KhachHang(Base):
    __tablename__ = "khach_hang"

    maKH = Column(String(50), primary_key=True, index=True)
    hoTen = Column(String(100), nullable=False)
    sdt = Column(String(20), nullable=True, index=True)
    diaChi = Column(String(255), nullable=True)
    email = Column(String(100), nullable=True)
    ngayTao = Column(DateTime, default=datetime.now)

    # Relationships
    phieuSuaList = relationship("PhieuSuaChua", back_populates="khachHang")
    hoaDonList = relationship("HoaDon", back_populates="khachHang")

# 2. Bảng Nhân Viên (Quản lý phân quyền hệ thống)
class NhanVien(Base):
    __tablename__ = "nhan_vien"

    maNV = Column(String(20), primary_key=True, index=True)
    hoTen = Column(String(100), nullable=False)
    chucVu = Column(String(50), nullable=False, default="Kỹ thuật viên")
    vaiTro = Column(String(50), nullable=False, default="Kỹ thuật viên")
    trangThai = Column(String(20), nullable=False, default="HOAT_DONG") # HOAT_DONG / KHOA
    quyenTruyCap = Column(Text, nullable=True) # JSON danh sách quyền
    sdt = Column(String(15), nullable=True)
    tenDangNhap = Column(String(50), nullable=False, unique=True)
    matKhau = Column(String(250), nullable=False)

    # Relationships
    phieuSuaList = relationship("PhieuSuaChua", back_populates="kyThuatVien", foreign_keys="PhieuSuaChua.maKTV")
    hoaDonList = relationship("HoaDon", back_populates="thuNgan")
    caLamViecList = relationship("CaLamViec", back_populates="nhanVien")

# 3. Bảng Linh Kiện (Quản lý Kho & Báo giá)
class LinhKien(Base):
    __tablename__ = "linh_kien"

    maLK = Column(String(50), primary_key=True, index=True)
    tenLK = Column(String(255), nullable=False)
    giaBan = Column(Float, nullable=False)
    giaNhap = Column(Float, nullable=False, default=0.0)
    soLuongTon = Column(Integer, default=0)
    tonToiThieu = Column(Integer, default=5)

    # Relationships
    chiTietList = relationship("ChiTietSuaChua", back_populates="linhKien")
    nhapKhoList = relationship("PhieuNhapKho", back_populates="linhKien")

# 4. Bảng Phiếu Sửa Chữa (Liên kết Khách Hàng, KTV, Linh Kiện, Hóa Đơn)
class PhieuSuaChua(Base):
    __tablename__ = "phieu_sua_chua"

    maPhieu = Column(String(20), primary_key=True, index=True)
    maKH = Column(String(50), ForeignKey("khach_hang.maKH", onupdate="CASCADE"), nullable=False, index=True)
    maKTV = Column(String(20), ForeignKey("nhan_vien.maNV", onupdate="CASCADE", ondelete="SET NULL"), nullable=True, index=True)
    moTaLoi = Column(Text, nullable=True)
    ghiChuKTV = Column(Text, nullable=True)
    aiTomTat = Column(Text, nullable=True)
    duyetBaoGia = Column(String(20), default="CHO_DUYET") # CHO_DUYET, DONG_Y, TU_CHOI
    ghiChuKhachHang = Column(Text, nullable=True)
    tienDatCoc = Column(Float, nullable=False, default=0.0)       # Tiền đặt cọc 30% đã thu
    daDatCoc = Column(Boolean, default=False)                      # Đã thu cọc chưa
    daDuyetChuanDoan = Column(Boolean, default=False)              # KTV đã duyệt chẩn đoán nguyên nhân chưa
    chuanDoanKTV = Column(Text, nullable=True)                     # Kết quả chẩn đoán chính thức được KTV phê duyệt
    nguoiDuyetChuanDoan = Column(String(50), nullable=True)        # KTV phê duyệt
    thoiGianDuyetChuanDoan = Column(DateTime, nullable=True)       # Thời gian phê duyệt
    trangThai = Column(Enum(TrangThaiEnum), default=TrangThaiEnum.KHOI_TAO)
    ngayTao = Column(DateTime, default=datetime.now)

    # Relationships
    khachHang = relationship("KhachHang", back_populates="phieuSuaList")
    kyThuatVien = relationship("NhanVien", back_populates="phieuSuaList", foreign_keys=[maKTV])
    chiTietList = relationship("ChiTietSuaChua", back_populates="phieuSua", cascade="all, delete-orphan")
    hoaDon = relationship("HoaDon", back_populates="phieuSua", uselist=False, cascade="all, delete-orphan")
    thongBaoList = relationship("ThongBaoKhachHang", back_populates="phieuSua", cascade="all, delete-orphan")
    danhGiaList = relationship("DanhGiaDichVu", back_populates="phieuSua", cascade="all, delete-orphan")

# 5. Bảng Chi Tiết Sửa Chữa & Bảo Hành (Composite PK: maPhieu, maLK)
class ChiTietSuaChua(Base):
    __tablename__ = "chi_tiet_sua_chua"

    maPhieu = Column(String(20), ForeignKey("phieu_sua_chua.maPhieu", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    maLK = Column(String(20), ForeignKey("linh_kien.maLK", onupdate="CASCADE"), primary_key=True)
    soLuong = Column(Integer, default=1)
    donGia = Column(Float, nullable=False)
    thoiGianBaoHanh = Column(String(50), nullable=True, default="12 Tháng")

    # Relationships
    phieuSua = relationship("PhieuSuaChua", back_populates="chiTietList")
    linhKien = relationship("LinhKien", back_populates="chiTietList")

# 6. Bảng Hóa Đơn / Giao Dịch Thanh Toán Thu Ngân (Liên kết Phiếu Sửa, Khách Hàng, Thu Ngân)
class HoaDon(Base):
    __tablename__ = "hoa_don"

    maHD = Column(String(50), primary_key=True, index=True)
    maPhieu = Column(String(20), ForeignKey("phieu_sua_chua.maPhieu", onupdate="CASCADE"), nullable=False, unique=True)
    maKH = Column(String(50), ForeignKey("khach_hang.maKH", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    maThuNgan = Column(String(20), ForeignKey("nhan_vien.maNV", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    phuongThuc = Column(String(30), nullable=False, default="TienMat") # TienMat / ChuyenKhoan
    tienLinhKien = Column(Float, nullable=False, default=0.0)
    tienCong = Column(Float, nullable=False, default=150000.0)
    tongTien = Column(Float, nullable=False)
    tienKhachDua = Column(Float, nullable=False, default=0.0)
    tienTraLai = Column(Float, nullable=False, default=0.0)
    ghiChu = Column(Text, nullable=True)
    ngayThanhToan = Column(DateTime, default=datetime.now)

    # Relationships
    phieuSua = relationship("PhieuSuaChua", back_populates="hoaDon")
    khachHang = relationship("KhachHang", back_populates="hoaDonList")
    thuNgan = relationship("NhanVien", back_populates="hoaDonList")

# 7. Bảng Ca Làm Việc & Chốt Ca Thu Ngân (Liên kết Nhân Viên Thu Ngân)
class CaLamViec(Base):
    __tablename__ = "ca_lam_viec"

    maCa = Column(String(50), primary_key=True, index=True)
    maNV = Column(String(20), ForeignKey("nhan_vien.maNV", onupdate="CASCADE"), nullable=False)
    thoiGianMoCa = Column(DateTime, nullable=False, default=datetime.now)
    thoiGianDongCa = Column(DateTime, nullable=True)
    soDonThanhToan = Column(Integer, default=0)
    tongTienMat = Column(Float, default=0.0)
    tongChuyenKhoan = Column(Float, default=0.0)
    tongDoanhThu = Column(Float, default=0.0)
    tienMatThucTe = Column(Float, default=0.0)
    chenhLech = Column(Float, default=0.0)
    ghiChu = Column(Text, nullable=True)
    trangThai = Column(String(20), default="DANG_MO") # DANG_MO / DA_DONG

    # Relationships
    nhanVien = relationship("NhanVien", back_populates="caLamViecList")

# 8. Bảng Lịch Sử Gửi Tin Nhắn Báo Khách (Lễ Tân - Khách Hàng)
class ThongBaoKhachHang(Base):
    __tablename__ = "thong_bao_khach"

    id = Column(Integer, primary_key=True, autoincrement=True)
    maPhieu = Column(String(20), ForeignKey("phieu_sua_chua.maPhieu", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    kenh = Column(String(20), default="Gmail")
    nguoiGui = Column(String(50), default="Lễ tân")
    noiDung = Column(Text, nullable=True)
    thoiGian = Column(DateTime, default=datetime.now)

    # Relationships
    phieuSua = relationship("PhieuSuaChua", back_populates="thongBaoList")

# 9. Bảng Phiếu Nhập Kho Linh Kiện (Quản lý Nhập Kho & Cập nhật tồn)
class PhieuNhapKho(Base):
    __tablename__ = "phieu_nhap_kho"

    maNhap = Column(String(50), primary_key=True, index=True)
    maLK = Column(String(50), ForeignKey("linh_kien.maLK", onupdate="CASCADE"), nullable=False)
    tenLK = Column(String(255), nullable=False)
    soLuong = Column(Integer, nullable=False, default=1)
    giaNhap = Column(Float, nullable=False, default=0.0)
    tongTien = Column(Float, nullable=False, default=0.0)
    nhaCungCap = Column(String(100), nullable=True, default="Tổng kho linh kiện")
    nguoiNhap = Column(String(50), nullable=True, default="Admin")
    ngayNhap = Column(DateTime, default=datetime.now)
    ghiChu = Column(Text, nullable=True)

    linhKien = relationship("LinhKien", back_populates="nhapKhoList")

# 10. Bảng Danh Mục Dịch Vụ Sửa Chữa & Bảng Giá Tiền Công
class DichVuSuaChua(Base):
    __tablename__ = "dich_vu"

    maDV = Column(String(50), primary_key=True, index=True)
    tenDV = Column(String(100), nullable=False)
    loaiMay = Column(String(100), nullable=False, default="Tất cả")
    tienCong = Column(Float, nullable=False, default=150000.0)
    thoiGianBaoHanh = Column(String(50), default="12 Tháng")
    moTa = Column(Text, nullable=True)
    trangThai = Column(String(20), default="HOAT_DONG")

# 11. Bảng Voucher & Khuyến Mãi
class Voucher(Base):
    __tablename__ = "voucher"

    maVoucher = Column(String(50), primary_key=True, index=True)
    tenVoucher = Column(String(100), nullable=False)
    loaiGiam = Column(String(20), default="PHAN_TRAM") # PHAN_TRAM / SO_TIEN
    giaTriGiam = Column(Float, nullable=False, default=10.0)
    donToiThieu = Column(Float, default=0.0)
    ngayHetHan = Column(DateTime, nullable=True)
    soLuong = Column(Integer, default=100)
    daDung = Column(Integer, default=0)
    trangThai = Column(String(20), default="HOAT_DONG") # HOAT_DONG / TAM_DUNG

# 12. Bảng Cấu Hình Hệ Thống & Tham Số AI
class CauHinhHeThong(Base):
    __tablename__ = "cau_hinh_he_thong"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    moTa = Column(String(255), nullable=True)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# 13. Bảng Bảng Lương Nhân Viên (Kế Toán Quản Lý)
class BangLuong(Base):
    __tablename__ = "bang_luong"

    id = Column(Integer, primary_key=True, autoincrement=True)
    maNV = Column(String(20), ForeignKey("nhan_vien.maNV", onupdate="CASCADE"), nullable=False)
    thang = Column(String(7), nullable=False)  # VD: "2026-10"
    luongCoBan = Column(Float, nullable=False, default=0.0)
    soPhieuXuLy = Column(Integer, default=0)   # Số phiếu/máy KTV/Lễ tân xử lý
    thuong = Column(Float, default=0.0)         # Thưởng doanh số
    phuCap = Column(Float, default=0.0)         # Phụ cấp thêm
    khauTru = Column(Float, default=0.0)        # Khấu trừ / phạt
    thucLinh = Column(Float, default=0.0)       # = luongCoBan + thuong + phuCap - khauTru
    trangThai = Column(String(20), default="CHO_DUYET")  # CHO_DUYET / DA_PHAT / DA_XAC_NHAN
    ghiChu = Column(Text, nullable=True)
    ngayTao = Column(DateTime, default=datetime.now)
    ngayPhat = Column(DateTime, nullable=True)

    nhanVien = relationship("NhanVien", foreign_keys=[maNV])

# 14. Bảng Đánh Giá Dịch Vụ Của Khách Hàng (Customer Feedback & Ratings)
class DanhGiaDichVu(Base):
    __tablename__ = "danh_gia_dich_vu"

    id = Column(Integer, primary_key=True, autoincrement=True)
    maPhieu = Column(String(20), ForeignKey("phieu_sua_chua.maPhieu", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    maKH = Column(String(50), nullable=True)
    tenKhachHang = Column(String(100), nullable=True)
    sdt = Column(String(20), nullable=True)
    soSao = Column(Integer, default=5) # 1 - 5 sao
    tieuChi = Column(String(255), nullable=True) # "Kỹ thuật tốt, Giá hợp lý, Nhanh chóng"
    noiDung = Column(Text, nullable=True)
    thoiGian = Column(DateTime, default=datetime.now)

    phieuSua = relationship("PhieuSuaChua", back_populates="danhGiaList")
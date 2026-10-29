-- ==============================================================
-- BẢNG LỊCH HẸN SỬA CHỮA (ONLINE REPAIR BOOKING) - FROGHIPPO PHONE
-- ==============================================================

USE `quan_ly_sua_chua`;

-- 1. TẠO BẢNG lich_hen
CREATE TABLE IF NOT EXISTS `lich_hen` (
    `MaLH` VARCHAR(20) NOT NULL PRIMARY KEY COMMENT 'Mã lịch hẹn, định dạng LH001, LH002...',
    `MaKH` VARCHAR(50) NOT NULL COMMENT 'Mã khách hàng liên kết',
    `HangMay` VARCHAR(50) NOT NULL COMMENT 'Hãng điện thoại (VD: Apple, Samsung...)',
    `Model` VARCHAR(100) NOT NULL COMMENT 'Dòng máy (VD: iPhone 13 Pro, iPhone 15...)',
    `MoTaLoi` TEXT NULL COMMENT 'Mô tả lỗi hoặc triệu chứng hỏng hóc',
    `NgayHen` DATE NOT NULL COMMENT 'Ngày khách chọn hẹn mang máy tới',
    `KhungGio` VARCHAR(20) NOT NULL COMMENT 'Khung giờ hẹn (VD: 08:00, 09:00...)',
    `TrangThai` VARCHAR(50) NOT NULL DEFAULT 'Chờ xác nhận' COMMENT 'Chờ xác nhận, Đã xác nhận, Đã đến, Không đến, Đã hủy',
    `LyDo` TEXT NULL COMMENT 'Lý do khi hủy lịch hoặc đổi lịch hẹn',
    `MaPhieu` VARCHAR(20) NULL COMMENT 'Mã phiếu sửa chữa tạo từ lịch hẹn này',
    `NgayTao` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm khách đặt lịch',
    INDEX `idx_lich_hen_makh` (`MaKH`),
    INDEX `idx_lich_hen_ngayhen` (`NgayHen`),
    INDEX `idx_lich_hen_trangthai` (`TrangThai`),
    CONSTRAINT `fk_lich_hen_khach_hang` FOREIGN KEY (`MaKH`) REFERENCES `khach_hang`(`maKH`) ON UPDATE CASCADE,
    CONSTRAINT `fk_lich_hen_phieu_sua` FOREIGN KEY (`MaPhieu`) REFERENCES `phieu_sua_chua`(`maPhieu`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. DỮ LIỆU MẪU ĐỂ TEST HỆ THỐNG
-- Đảm bảo có dữ liệu khách hàng mẫu
INSERT IGNORE INTO `khach_hang` (`maKH`, `hoTen`, `sdt`, `diaChi`, `email`, `ngayTao`) VALUES
('KH001', 'Nguyễn Văn An', '0987654321', '123 Cầu Giấy, Hà Nội', 'an.nguyen@gmail.com', NOW()),
('KH002', 'Trần Thị Mai', '0912345678', '456 Kim Mã, Ba Đình, Hà Nội', 'mai.tran@gmail.com', NOW()),
('KH003', 'Lê Hoàng Nam', '0933221100', '789 Giải Phóng, Hà Nội', 'nam.le@gmail.com', NOW());

-- Chèn 3 lịch hẹn mẫu tương ứng 3 trạng thái
INSERT INTO `lich_hen` (`MaLH`, `MaKH`, `HangMay`, `Model`, `MoTaLoi`, `NgayHen`, `KhungGio`, `TrangThai`, `LyDo`, `MaPhieu`, `NgayTao`)
VALUES
('LH001', 'KH001', 'Apple', 'iPhone 13 Pro', 'Màn hình bị sọc xanh, kính vỡ nhẹ góc trên', CURDATE(), '09:00', 'Chờ xác nhận', NULL, NULL, NOW()),
('LH002', 'KH002', 'Apple', 'iPhone 12', 'Pin tụt nhanh, dung lượng tối đa còn 76%', CURDATE(), '10:00', 'Đã xác nhận', NULL, NULL, NOW()),
('LH003', 'KH003', 'Apple', 'iPhone 14 Pro Max', 'Cổng sạc tiếp xúc chập chờn, không nhận sạc nhanh', CURDATE(), '14:00', 'Đã đến', NULL, '#PS04', NOW())
ON DUPLICATE KEY UPDATE `Model` = VALUES(`Model`);


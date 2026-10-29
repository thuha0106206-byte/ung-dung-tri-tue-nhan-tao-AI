/**
 * FrogHippo Phone - RBAC Role Guard & Access Control
 * 
 * Quy định phân quyền cốt lõi:
 * 1. Chỉ có Tác nhân ADMIN mới được phép truy cập tất cả các phân hệ:
 *    - Quản Trị Viên (Admin) [/admin]
 *    - Lễ Tân & Tiếp Nhận [/le-tan]
 *    - Thu Ngân & Thanh Toán [/thu-ngan]
 *    - Kỹ Thuật Viên Sửa Chữa [/ky-thuat-vien]
 * 2. Các tác nhân khác KHÔNG có quyền truy cập vào phân hệ của tác nhân khác:
 *    - Lễ Tân: CHỈ được truy cập [/le-tan]
 *    - Thu Ngân: CHỈ được truy cập [/thu-ngan]
 *    - Kỹ Thuật Viên: CHỈ được truy cập [/ky-thuat-vien]
 * 3. Nếu tác nhân cố tình truy cập vào phân hệ khác, hệ thống lập tức chặn lại,
 *    thông báo cảnh báo và điều hướng về đúng phân hệ của họ.
 */

(function (window) {
    'use strict';

    // 1. Lấy thông tin người dùng đang đăng nhập
    function getLoggedInUser() {
        try {
            const raw = localStorage.getItem('phonecare_user') 
                     || localStorage.getItem('phonecare_session')
                     || sessionStorage.getItem('phonecare_user')
                     || sessionStorage.getItem('phonecare_session');
            if (!raw) return null;
            const parsed = JSON.parse(raw);
            if (!parsed || (!parsed.maNV && !parsed.chucVu && !parsed.tenDangNhap)) {
                return null;
            }
            return parsed;
        } catch (e) {
            console.error("Lỗi đọc phiên làm việc:", e);
            return null;
        }
    }

    // 2. Chuẩn hóa tên vai trò
    function getNormalizedRole(user) {
        if (!user) return 'Khách hàng';
        const roleStr = (user.chucVu || user.vaiTro || '').toLowerCase().trim();
        const username = (user.tenDangNhap || '').toLowerCase().trim();

        if (roleStr.includes('admin') || roleStr.includes('quan tri') || username === 'admin') {
            return 'Admin';
        }
        if (roleStr.includes('lễ tân') || roleStr.includes('le tan') || roleStr.includes('letan') || username.includes('letan')) {
            return 'Lễ tân';
        }
        if (roleStr.includes('thu ngân') || roleStr.includes('thu ngan') || roleStr.includes('thungan') || username.includes('thungan')) {
            return 'Thu ngân';
        }
        if (roleStr.includes('kỹ thuật') || roleStr.includes('ky thuat') || roleStr.includes('ktv') || username.includes('ktv')) {
            return 'Kỹ thuật viên';
        }
        return user.chucVu || 'Nhân viên';
    }

    // 3. Đường dẫn phân hệ mặc định theo từng vai trò
    function getRoleHomeUrl(role) {
        switch (role) {
            case 'Admin':
                return '/admin';
            case 'Lễ tân':
                return '/le-tan';
            case 'Thu ngân':
                return '/thu-ngan';
            case 'Kỹ thuật viên':
                return '/ky-thuat-vien';
            default:
                return '/';
        }
    }

    // 4. Kiểm tra và thực thi chặn quyền truy cập (Chạy ngay trong <head> để ngăn hiển thị trang)
    function enforcePageAccess(allowedRoles, pageTitle) {
        const user = getLoggedInUser();

        // Trường hợp 1: Chưa đăng nhập tài khoản
        if (!user) {
            alert(
                "⚠️ YÊU CẦU ĐĂNG NHẬP!\n\n" +
                "Bạn chưa đăng nhập vào hệ thống.\n" +
                "Vui lòng đăng nhập tài khoản nhân viên để truy cập [" + pageTitle + "]."
            );
            sessionStorage.setItem('phonecare_redirect', window.location.pathname);
            window.location.replace('/?login=1');
            return false;
        }

        const currentRole = getNormalizedRole(user);

        // Trường hợp 2: Admin luôn có toàn quyền truy cập TẤT CẢ các phân hệ
        if (currentRole === 'Admin') {
            return true;
        }

        // Trường hợp 3: Người dùng thuộc danh sách vai trò cho phép của trang này
        if (allowedRoles.includes(currentRole)) {
            return true;
        }

        // Trường hợp 4: VI PHẠM PHÂN QUYỀN - Tác nhân truy cập trái phép vào phân hệ của tác nhân khác
        const correctUrl = getRoleHomeUrl(currentRole);
        alert(
            "⛔ TRUY CẬP BỊ TỪ CHỐI!\n\n" +
            "Tài khoản của bạn: " + (user.hoTen || user.tenDangNhap) + " (" + currentRole + ").\n\n" +
            "Theo quy định phân quyền của FrogHippo Phone:\n" +
            "• Chỉ có Tác nhân ADMIN mới có quyền truy cập vào các chức năng Lễ Tân, Thu Ngân và KTV.\n" +
            "• Tác nhân [" + currentRole + "] chỉ có quyền truy cập vào phân hệ của chính mình.\n\n" +
            "Hệ thống đang chuyển bạn về đúng phân hệ làm việc của bạn."
        );

        window.location.replace(correctUrl);
        return false;
    }

    // 5. Cập nhật thanh Header sau khi tải trang:
    //    - Nếu là Admin: Hiển thị đầy đủ lối tắt sang Lễ Tân, Thu Ngân, Bàn KTV
    //    - Nếu là Tác nhân khác: ẨN TOÀN BỘ nút chuyển sang các phân hệ khác (chỉ thấy Trang Chủ và phân hệ của mình)
    function setupPortalHeader(currentPortalRole) {
        document.addEventListener('DOMContentLoaded', () => {
            const user = getLoggedInUser();
            if (!user) return;

            const role = getNormalizedRole(user);

            // Cập nhật tên người dùng hiển thị ở header nếu có phần tử
            const userEl = document.getElementById('current-user-name') 
                        || document.getElementById('admin-user-name');
            if (userEl) {
                if (role === 'Admin') {
                    userEl.textContent = `${user.hoTen || 'Admin'} (Admin - Toàn quyền)`;
                } else {
                    userEl.textContent = `${user.hoTen} (${role})`;
                }
            }

            // Nếu KHÔNG PHẢI ADMIN: Ẩn tất cả các nút lối tắt sang phân hệ khác
            if (role !== 'Admin') {
                const crossLinks = document.querySelectorAll('.cross-portal-link');
                crossLinks.forEach(link => {
                    link.style.display = 'none';
                    link.classList.add('hidden');
                });
            } else {
                // Là Admin: Đảm bảo các nút lối tắt hiển thị rõ ràng
                const crossLinks = document.querySelectorAll('.cross-portal-link');
                crossLinks.forEach(link => {
                    link.style.display = 'inline-flex';
                    link.classList.remove('hidden');
                });
            }
        });
    }

    // 6. Xử lý đăng xuất tài khoản
    function handleLogout(confirmMsg) {
        const user = getLoggedInUser();
        const userName = user ? (user.hoTen || user.tenDangNhap) : 'nhân viên';
        const msg = confirmMsg || `Bạn có chắc chắn muốn đăng xuất tài khoản [${userName}] khỏi hệ thống?`;

        if (confirm(msg)) {
            localStorage.removeItem('phonecare_user');
            localStorage.removeItem('phonecare_session');
            sessionStorage.removeItem('phonecare_user');
            sessionStorage.removeItem('phonecare_session');
            window.location.href = '/';
        }
    }

    // Export các hàm ra global window
    window.AuthGuard = {
        getLoggedInUser,
        getNormalizedRole,
        getRoleHomeUrl,
        enforcePageAccess,
        setupPortalHeader,
        handleLogout
    };

    window.handleLogout = handleLogout;

})(window);

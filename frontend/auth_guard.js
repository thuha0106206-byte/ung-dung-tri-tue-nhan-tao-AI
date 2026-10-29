/**
 * FrogHippo Phone - RBAC Role Guard & Access Control
 * 
 * QUY ĐỊNH PHÂN QUYỀN TUYỆT ĐỐI:
 * 1. CHỈ CÓ TÁC NHÂN ADMIN MỚI CÓ TOÀN QUYỀN TRÊN TẤT CẢ CÁC PHÂN HỆ:
 *    - Quản Trị Viên (Admin) [/admin]
 *    - Lễ Tân & Tiếp Nhận [/le-tan]
 *    - Thu Ngân & Thanh Toán [/thu-ngan]
 *    - Kỹ Thuật Viên Sửa Chữa [/ky-thuat-vien]
 * 
 * 2. CÁC TÁC NHÂN KHÁC (LỄ TÂN, THU NGÂN, KTV) KHÔNG ĐƯỢC PHÉP TRUY CẬP VÀO PHÂN HỆ KHÁC:
 *    - Lễ Tân: CHỈ ĐƯỢC PHÉP làm việc tại [/le-tan]. Tuyệt đối bị chặn khi vào Admin, KTV, Thu Ngân.
 *    - Thu Ngân: CHỈ ĐƯỢC PHÉP làm việc tại [/thu-ngan].
 *    - Kỹ Thuật Viên: CHỈ ĐƯỢC PHÉP làm việc tại [/ky-thuat-vien].
 * 
 * 3. Nếu người dùng cố tình truy cập vào phân hệ trái phép:
 *    - Ẩn ngay lập tức nội dung trang để bảo mật.
 *    - Hiện cảnh báo từ chối truy cập.
 *    - Tự động điều hướng về đúng phân hệ làm việc của tác nhân đó.
 */

(function (window) {
    'use strict';

    // 1. Lấy thông tin tài khoản đang đăng nhập từ LocalStorage/SessionStorage
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

    // 2. Chuẩn hóa vai trò người dùng thành 4 nhóm chuẩn: 'Admin', 'Lễ tân', 'Thu ngân', 'Kỹ thuật viên'
    function getNormalizedRole(user) {
        if (!user) return 'Khách hàng';
        const roleStr = ((user.vaiTro || '') + ' ' + (user.chucVu || '')).toLowerCase().trim();
        const username = (user.tenDangNhap || '').toLowerCase().trim();

        if (roleStr.includes('admin') || roleStr.includes('quan tri') || username === 'admin') {
            return 'Admin';
        }
        if (roleStr.includes('letan') || roleStr.includes('lễ tân') || roleStr.includes('le tan') || username.includes('letan')) {
            return 'Lễ tân';
        }
        if (roleStr.includes('thungan') || roleStr.includes('thu ngân') || roleStr.includes('thu ngan') || username.includes('thungan')) {
            return 'Thu ngân';
        }
        if (roleStr.includes('ktv') || roleStr.includes('kythuat') || roleStr.includes('kỹ thuật') || roleStr.includes('ky thuat') || username.includes('ktv')) {
            return 'Kỹ thuật viên';
        }
        return user.chucVu || 'Nhân viên';
    }

    // 3. Đường dẫn phân hệ đúng thẩm quyền theo từng vai trò
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

    // 4. KIỂM SOÁT VÀ THỰC THI PHÂN QUYỀN NGHIÊM NGẶT (CHẠY NGAY TRONG <HEAD>)
    function enforcePageAccess(allowedRoles, pageTitle) {
        const user = getLoggedInUser();

        // TRƯỜNG HỢP 1: Chưa đăng nhập tài khoản
        if (!user) {
            if (document.documentElement) document.documentElement.style.display = 'none';
            alert(
                "⚠️ YÊU CẦU ĐĂNG NHẬP!\n\n" +
                "Bạn chưa đăng nhập vào hệ thống.\n" +
                "Vui lòng đăng nhập để truy cập [" + pageTitle + "]."
            );
            sessionStorage.setItem('phonecare_redirect', window.location.pathname);
            window.location.replace('/?login=1');
            return false;
        }

        const currentRole = getNormalizedRole(user);

        // TRƯỜNG HỢP 2: Admin luôn có TOÀN QUYỀN trên mọi phân hệ
        if (currentRole === 'Admin') {
            if (document.documentElement) document.documentElement.style.display = '';
            return true;
        }

        // TRƯỜNG HỢP 3: Vai trò người dùng nằm trong danh sách cho phép của phân hệ này
        if (allowedRoles.includes(currentRole)) {
            if (document.documentElement) document.documentElement.style.display = '';
            return true;
        }

        // TRƯỜNG HỢP 4: VI PHẠM PHÂN QUYỀN - Tác nhân cố tình vào phân hệ không được phép
        // Ẩn trắng trang ngay lập tức để không lộ giao diện hay dữ liệu bảo mật
        if (document.documentElement) document.documentElement.style.display = 'none';

        const correctUrl = getRoleHomeUrl(currentRole);
        const displayName = user.hoTen || user.tenDangNhap;

        alert(
            "⛔ TRUY CẬP BỊ TỪ CHỐI!\n\n" +
            "Tài khoản: " + displayName + " (" + currentRole + ").\n\n" +
            "Theo quy định phân quyền của FrogHippo Phone:\n" +
            "👉 Chỉ có Quản Trị Viên (Admin) mới có toàn quyền truy cập tất cả các phân hệ.\n" +
            "👉 Tài khoản [" + currentRole + "] KHÔNG ĐƯỢC PHÉP truy cập vào [" + pageTitle + "].\n\n" +
            "Hệ thống đang chuyển bạn về đúng phân hệ làm việc của bạn."
        );

        window.location.replace(correctUrl);
        return false;
    }

    // 5. Cập nhật thanh Header sau khi tải trang:
    //    - Cập nhật tên người dùng & vai trò
    //    - Ẩn toàn bộ link phân hệ khác nếu không phải Admin
    function setupPortalHeader(currentPortalRole) {
        document.addEventListener('DOMContentLoaded', () => {
            const user = getLoggedInUser();
            if (!user) return;

            const role = getNormalizedRole(user);

            // Cập nhật tên người dùng hiển thị ở header nếu có phần tử
            const userEl = document.getElementById('current-user-name')
                || document.getElementById('admin-user-name');
            if (userEl) {
                const path = window.location.pathname.toLowerCase();
                if (currentPortalRole === 'Admin' || path.includes('/admin')) {
                    userEl.textContent = `${user.hoTen || 'Nguyễn Văn An'} (Admin - Toàn quyền)`;
                } else if (currentPortalRole === 'Lễ tân' || path.includes('/le-tan')) {
                    // Phân hệ Lễ Tân: Ca trực chuẩn là Trần Thị Bình (Lễ Tân)
                    userEl.textContent = (role === 'Lễ tân') ? `${user.hoTen} (Lễ Tân)` : 'Trần Thị Bình (Lễ Tân)';
                } else if (currentPortalRole === 'Thu ngân' || path.includes('/thu-ngan')) {
                    // Phân hệ Thu Ngân: Ca trực chuẩn là Phạm Thị Dung (Thu Ngân)
                    userEl.textContent = (role === 'Thu ngân') ? `${user.hoTen} (Thu Ngân)` : 'Phạm Thị Dung (Thu Ngân)';
                } else if (currentPortalRole === 'Kỹ thuật viên' || path.includes('/ky-thuat-vien') || path.includes('/ktv')) {
                    // Phân hệ Kỹ Thuật Viên: Ca trực KTV
                    userEl.textContent = (role === 'Kỹ thuật viên') ? `${user.hoTen} (KTV)` : 'Kỹ thuật viên Trực ban';
                } else {
                    userEl.textContent = `${user.hoTen} (${role})`;
                }
            }

            // Nếu KHÔNG PHẢI ADMIN: Ẩn triệt để tất cả các nút lối tắt sang phân hệ khác
            const crossLinks = document.querySelectorAll('.cross-portal-link');
            if (role !== 'Admin') {
                crossLinks.forEach(link => {
                    link.style.display = 'none';
                    link.classList.add('hidden');
                });
            } else {
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

    // Export ra global window
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

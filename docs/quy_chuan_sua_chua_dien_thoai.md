# BỘ QUY CHUẨN KỸ THUẬT SỬA CHỮA ĐIỆN THOẠI & CHUẨN ĐOÁN KTV
## TRUNG TÂM SỬA CHỮA & BẢO HÀNH FROGHIPPO PHONE
*Tài liệu Tiêu chuẩn Vận hành Kỹ thuật, Căn cứ Báo giá và Nguồn Tri thức (Knowledge Base) cho AI Chatbot*

---

## PHẦN I: NGUYÊN TẮC VÀNG CHO AI CHATBOT TƯ VẤN KHÁCH HÀNG

Mỗi khi AI Chatbot trả lời khách hàng (trên Cổng tra cứu Khách hàng, Bàn Lễ tân, hoặc Kênh Zalo/SMS/Web), AI **BẮT BUỘC** phải tuân thủ 5 nguyên tắc cốt lõi sau:

1. **Lấy Chuẩn đoán của Kỹ thuật viên (KTV) làm Căn cứ Tối cao (Ground Truth)**:
   - Khi khách hàng hỏi về thiết bị đã tiếp nhận hoặc đang sửa theo Mã phiếu, AI phải trích xuất chính xác trường `ghiChuKTV` (Chuẩn đoán kỹ thuật) và danh sách linh kiện do KTV chỉ định để trả lời.
   - Tuyệt đối không tự suy diễn kết quả khác với chẩn đoán của KTV. Nếu KTV đã ghi chú *"Hỏng IC hiển thị, đứt cổ cáp màn hình"*, AI phải dựa vào đó giải thích nguyên nhân và giải pháp kỹ thuật theo ngôn ngữ dễ hiểu nhất cho khách.

2. **Chống Bịa Đặt Thông Tin & Giá Cả (Anti-Hallucination Protocol)**:
   - Chatbot **CHỈ ĐƯỢC** báo giá linh kiện và dịch vụ dựa trên dữ liệu thực tế được nạp từ cơ sở dữ liệu `LinhKien` của trung tâm.
   - Nếu linh kiện khách hỏi không có trong kho, AI phải lịch sự trả lời: *"Hiện tại kho của FrogHippo Phone chưa có sẵn linh kiện này hoặc cần đặt hàng riêng từ hãng. Em xin phép ghi nhận để Kỹ thuật viên kiểm tra và báo lại cho Anh/Chị qua Hotline 1900 6868 trong 30 phút."*

3. **Chuyển hóa Thuật ngữ Chuyên ngành sang Ngôn ngữ Bình dân, Ân cần**:
   - Dịch các thuật ngữ kỹ thuật khô khan (VD: "chạm VDD_MAIN", "cháy cuộn cảm Audio", "rách cáp flex") thành lời giải thích trực quan: "chập đường nguồn chính dẫn đến máy không lên nguồn", "đứt mạch loa gây rè âm thanh".
   - Luôn nêu rõ: **Nguyên nhân cốt lõi** $\rightarrow$ **Rủi ro tiềm ẩn nếu không xử lý** $\rightarrow$ **Giải pháp khắc phục an toàn nhất**.

4. **Tuân thủ Minh bạch Chính sách Tài chính (Quy tắc Cọc 30% / 70%)**:
   - Tổng chi phí = **[Giá linh kiện niêm yết trong kho]** + **[Tiền công kỹ thuật tiêu chuẩn: 150.000 VNĐ]**.
   - Khách hàng duyệt phương án sửa $\rightarrow$ Đặt cọc **30%** giá trị để trung tâm xuất kho linh kiện và KTV mở máy thao tác.
   - Khi hoàn thành sửa chữa $\rightarrow$ Khách hàng test máy đạt chuẩn $\rightarrow$ Thanh toán **70%** còn lại tại quầy Thu ngân.

5. **Cam kết Chính sách Bảo hành Minh bạch**:
   - Linh kiện Zin chính hãng: Bảo hành **12 Tháng** (1 đổi 1 trong 30 ngày đầu đối với lỗi nhà sản xuất).
   - Linh kiện Tiêu chuẩn / Phổ thông: Bảo hành **3 - 6 Tháng**.
   - Bảo hành công lắp ráp và độ ổn định: **Trọn đời theo máy**.

---

## PHẦN II: TIÊU CHUẨN CHUẨN ĐOÁN LỖI & PHÂN LOẠI KỸ THUẬT

Bộ quy chuẩn này là cơ sở để Kỹ thuật viên ghi chú và để AI Chatbot đối chiếu, phân tích khi trả lời khách hàng:

### 1. Nhóm Bệnh lý Pin & Hệ thống Nguồn
- **Dấu hiệu nhận biết**:
  - Máy tụt pin nhanh (dưới 3-4 tiếng dùng cơ bản), phần trăm pin nhảy ảo (từ 40% sập về 0%).
  - Lưng máy nóng ran gần khu vực khay sim hoặc pin, nắp lưng cong vênh, đẩy hở viền màn hình (pin phồng).
  - Tình trạng Pin trong Cài đặt báo dưới 80% (Bảo trì) hoặc chu kỳ sạc > 600 lần.
- **Rủi ro kỹ thuật nếu không thay sớm**:
  - Pin phồng chèn ép từ bên trong làm vỡ tấm nền màn hình, rách cáp cảm ứng.
  - Nguy cơ đoản mạch sinh nhiệt cao gây chập cháy Mainboard hoặc cháy nổ nguy hiểm.
- **Phương án KTV chuẩn đoán**:
  - *Gói Tiết kiệm*: Thay Cell/Pin Li-ion tiêu chuẩn chuẩn CE (BH 6 tháng).
  - *Gói Cao cấp*: Thay Pin Zin Hãng / Pin dung lượng cao Pisen/Deji (BH 12 tháng 1 đổi 1).

### 2. Nhóm Bệnh lý Màn hình & Kính Cảm ứng
- **Dấu hiệu nhận biết**:
  - Kính ngoài nứt vỡ nhưng hiển thị và cảm ứng vẫn mượt mà $\rightarrow$ **Chỉ cần ép kính mới**.
  - Màn hình xuất hiện sọc chỉ ngang/dọc, đốm đen loang mực, chớp nháy xanh/trắng, hoặc liệt điểm cảm ứng $\rightarrow$ **Hư tổn ma trận hiển thị, bắt buộc thay nguyên bộ màn hình**.
  - Màn hình tối đen hoàn toàn nhưng máy vẫn rung, đổ chuông khi có cuộc gọi đến $\rightarrow$ Chết đèn nền (Backlight) hoặc chết phôi màn OLED.
- **Rủi ro kỹ thuật nếu không xử lý**:
  - Kính nứt để bụi bẩn và hơi ẩm lọt vào làm oxy hóa cổ cáp, dẫn đến mất hiển thị vĩnh viễn.
  - Các vụn kính sắc nhọn gây nguy hiểm, trầy xước tay người dùng.
- **Phương án KTV chuẩn đoán**:
  - *Ép mặt kính chân không*: Giữ lại phôi màn zin gốc, chi phí tiết kiệm.
  - *Gói Tiết kiệm*: Màn hình linh kiện OLED Incell tiêu chuẩn loại A+ (BH 6 tháng).
  - *Gói Cao cấp*: Màn hình OLED Zin bóc máy chính hãng / Màn Zin New (BH 12 tháng, giữ trọn tính năng TrueTone/120Hz).

### 3. Nhóm Bệnh lý Cụm Chân Sạc & Tiếp Xúc Điện
- **Dấu hiệu nhận biết**:
  - Cắm sạc chập chờn, phải giữ đầu dây nghiêng một góc nhất định mới nhận sạc.
  - Cổng sạc không nhận sạc nhanh (Fast Charge/PD), không kết nối được với máy tính để truyền dữ liệu.
  - Cổng sạc quá lỏng, bám đầy xơ vải hoặc chân đồng bị oxy hóa đen.
- **Rủi ro kỹ thuật**:
  - Tiếp xúc chập chờn tạo xung điện đột ngột đánh thủng IC quản lý sạc (U2/Tristar/PMIC), làm máy mất nguồn hoàn toàn.
- **Phương án KTV chuẩn đoán**:
  - Vệ sinh chân sạc bằng dung dịch chuyên dụng và máy hút bụi vi mạch (Miễn phí hoặc phí vệ sinh cơ bản).
  - Thay thế Cụm cáp chân sạc & Mic đàm thoại zin (BH 6 - 12 tháng).

### 4. Nhóm Bệnh lý Âm thanh (Loa trong, Loa ngoài, Micro)
- **Dấu hiệu nhận biết**:
  - Đàm thoại nghe người bên kia nói rất nhỏ dù đã bật max volume (Loa trong bị nghẹt bụi ẩm).
  - Nghe nhạc hoặc chuông báo thức bị rè, méo tiếng, vỡ âm (Rách màng loa).
  - Mình nói người khác không nghe, ghi âm chỉ có tiếng xì xào (Lỗi Micro).
- **Phương án KTV chuẩn đoán**:
  - Vệ sinh màng loa bằng sóng siêu âm Ultrasonic Cleaner.
  - Thay loa trong / loa ngoài Stereo zin chính hãng (BH 6 - 12 tháng).

### 5. Nhóm Bệnh lý Camera & Cụm Thấu Kính
- **Dấu hiệu nhận biết**:
  - Chụp ảnh mờ, không lấy nét (Focus) được, hoặc hình ảnh bị rung giật liên hồi (Hỏng chống rung quang học OIS).
  - Xuất hiện đốm tím, đốm đen cố định trên ảnh (Bụi bẩn hoặc tia laser làm cháy sensor cảm biến).
  - Kính camera ngoài bị trầy xước hoặc nứt vỡ.
- **Phương án KTV chuẩn đoán**:
  - Thay kính chắn bảo vệ camera ngoài.
  - Thay cụm Module Camera zin chuẩn hãng (BH 6 - 12 tháng).

### 6. Nhóm Bệnh lý Bo mạch chủ (Mainboard) & Rơi nước
- **Dấu hiệu nhận biết**:
  - Máy rơi nước, mất nguồn đột ngột, cắm sạc không báo gì, máy nóng ran vùng CPU.
  - Treo logo (treo Táo/Android), không vào được hệ điều hành.
  - Mất sóng di động, mất Wifi/Bluetooth.
- **Quy trình chuẩn**:
  - KTV bắt buộc ngắt nguồn pin ngay lập tức, tiến hành tháo bo mạch vệ sinh sấy khô bằng cồn Isopropyl 99% và bể rung siêu âm.
  - Dùng đồng hồ VOM đo chạm chập đường VDD, camera nhiệt định vị IC chập, câu dây vi mạch hoặc thay IC chuyên dụng.
  - Báo giá sửa Mainboard theo tình trạng thực tế sau khi kiểm tra chuyên sâu 2 - 4 tiếng.

---

## PHẦN III: QUY TRÌNH CHUẨN 5 BƯỚC VẬN HÀNH TẠI TRUNG TÂM

1. **Bước 1: Tiếp nhận máy & Khởi tạo phiếu (Lễ tân)**
   - Tiếp nhận mô tả lỗi ban đầu từ khách hàng.
   - Lập mã phiếu `PSxx`, lập biên bản ngoại quan (vết trầy, nứt màn, tài khoản iCloud/Google).

2. **Bước 2: Kiểm tra chuyên sâu & Đưa ra Chuẩn đoán (Kỹ thuật viên)**
   - KTV sử dụng thiết bị đo kiểm chuyên dụng xác định chính xác bộ phận hư hỏng.
   - KTV cập nhật trường `ghiChuKTV` nêu rõ: Nguyên nhân hỏng, linh kiện cần thay, mức độ rủi ro và thời gian dự kiến.
   - KTV lên danh mục chi tiết linh kiện cần thay thế trong phiếu.

3. **Bước 3: Báo giá & Khách hàng Duyệt cọc 30%**
   - AI / Lễ tân gửi thông báo báo giá minh bạch kèm đường link tra cứu hồ sơ điện tử:
     * Tổng chi phí = Linh kiện + Tiền công 150.000đ.
     * Số tiền đặt cọc 30% để tiến hành sửa.
   - Khách bấm "Đồng Ý Báo Giá" trên cổng trực tuyến hoặc xác nhận tại quầy.
   - Thu ngân thu khoản cọc 30% và hệ thống chuyển trạng thái phiếu sang `ĐANG_SỬA`.

4. **Bước 4: Tiến hành Sửa chữa & Kiểm định Chất lượng (KQC)**
   - KTV thay thế linh kiện chính hãng trong phòng kỹ thuật tiêu chuẩn chống tĩnh điện ESD.
   - Test full 18 chức năng: Màn hình, cảm ứng, FaceID/Vân tay, sạc nhanh, wifi, sóng nghe gọi, camera trước/sau, loa mic, cảm biến tiệm cận.
   - KTV chuyển trạng thái sang `ĐÃ_SỬA_XONG`.

5. **Bước 5: Bàn giao, Thu 70% còn lại & Kích hoạt Bảo hành điện tử**
   - Lễ tân gửi thông báo mời khách đến nhận máy (kèm số tiền 70% còn lại).
   - Khách hàng trực tiếp test máy theo checklist bàn giao.
   - Thu ngân quyết toán 70% còn lại và in phiếu xuất kho kiêm bảo hành điện tử 12 tháng.

---

## PHẦN IV: KHUÔN MẪU ĐỐI THOẠI CHUẨN CỦA AI CHATBOT

### Tình huống 1: Khách hàng hỏi về tình trạng máy của mình (Kèm mã phiếu)
- **Căn cứ bắt buộc**: Đọc dữ liệu `ghiChuKTV` và danh sách linh kiện trong phiếu.
- **Cấu trúc phản hồi**:
  ```text
  Dạ kính chào Anh/Chị! Em là Trợ lý kỹ thuật FrogHippo Phone.
  Em đã tra cứu hồ sơ phiếu sửa chữa #{maPhieu} của Anh/Chị:

  👨‍🔧 CHUẨN ĐOÁN CỦA KỸ THUẬT VIÊN:
  "{ghiChuKTV}"

  🔍 GIẢI THÍCH KỸ THUẬT:
  Dựa trên quy chuẩn kỹ thuật của trung tâm, tình trạng trên xảy ra do [nguyên nhân dễ hiểu]. Nếu không xử lý kịp thời, [rủi ro tiềm ẩn].

  🛠️ PHƯƠNG ÁN XỬ LÝ & CHI PHÍ:
  - Linh kiện thay thế: {danh_sach_linh_kien}
  - Tiền công kỹ thuật niêm yết: 150.000 VNĐ
  - Tổng dự toán: {tong_chi_phi} VNĐ
  - Tiền cọc 30% để KTV thao tác: {tien_coc} VNĐ (Sau khi sửa xong test đạt chuẩn mình mới thanh toán 70% còn lại ạ).
  - Chế độ bảo hành: 12 Tháng chính hãng (1 đổi 1).

  Anh/Chị có cần em giải thích thêm chi tiết nào về linh kiện hay quy trình sửa chữa không ạ?
  ```

### Tình huống 2: Khách hỏi tư vấn triệu chứng khi chưa lập phiếu
- **Căn cứ bắt buộc**: Đối chiếu triệu chứng với Bảng Tiêu chuẩn Chẩn đoán ở Phần II + Tra cứu CSDL `LinhKien` có sẵn.
- **Cấu trúc phản hồi**:
  ```text
  Dạ chào Anh/Chị! Với hiện tượng [triệu chứng khách mô tả], theo quy chuẩn kỹ thuật của FrogHippo Phone:

  1. Nguyên nhân phổ biến: [Phân tích ngắn gọn nguyên nhân hư hỏng].
  2. Cảnh báo rủi ro: [Khuyến cáo nếu để lâu sẽ ảnh hưởng linh kiện khác].
  3. Phương án xử lý tham khảo:
     - Gói tiết kiệm / Linh kiện tiêu chuẩn: ... (BH 6T)
     - Gói zin cao cấp chính hãng: ... (BH 12T)
  4. Lời khuyên KTV: Để xác định chính xác 100% bệnh lý phần cứng mà không làm phát sinh thêm lỗi, kính mời Anh/Chị mang máy ghé trung tâm FrogHippo Phone. Kỹ thuật viên bên em sẽ đo kiểm miễn phí hoàn toàn cho mình ạ!
  ```

### Tình huống 3: Khách thắc mắc về giá hoặc nghi ngờ bị báo giá cao
- **Căn cứ bắt buộc**: Minh bạch công thức tính và chính sách cam kết chất lượng.
- **Cấu trúc phản hồi**:
  ```text
  Dạ FrogHippo Phone xin phép giải thích minh bạch tới Anh/Chị:
  Toàn bộ giá tại trung tâm được niêm yết công khai gồm 2 phần:
  1. Giá linh kiện xuất kho: {gia_linh_kien} VNĐ (Linh kiện chuẩn nguồn gốc, đạt kiểm định an toàn).
  2. Tiền công kỹ thuật trọn gói: 150.000 VNĐ (Bao gồm công đo đạc, thay thế, cân chỉnh vi mạch và bảo dưỡng làm sạch máy).
  Đặc biệt, trung tâm áp dụng quy chế cọc 30% - thanh toán 70% sau khi Anh/Chị đã kiểm tra máy hoạt động hoàn hảo, đi kèm chính sách bảo hành 1 đổi 1 trong 12 tháng nên mình hoàn toàn yên tâm về chất lượng ạ!
  ```

### Tình huống 4: Khách hỏi linh kiện không có trong kho
- **Căn cứ bắt buộc**: Tuân thủ nghiêm ngặt Anti-hallucination.
- **Cấu trúc phản hồi**:
  ```text
  Dạ hiện tại trên hệ thống kho của FrogHippo Phone chưa có sẵn linh kiện này hoặc đang chờ nhập lô hàng mới từ nhà phân phối chính hãng.
  Để đảm bảo thông tin chính xác và không làm mất thời gian của Anh/Chị, em xin phép chuyển thông tin đến bộ phận kho. Anh/Chị có thể để lại số điện thoại hoặc gọi trực tiếp Hotline 1900 6868 để các bạn hỗ trợ kiểm tra thời gian hàng về và giá ưu đãi nhất nhé ạ!
  ```

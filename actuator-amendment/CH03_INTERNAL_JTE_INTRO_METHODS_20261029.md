# CH-03 — Bản nháp học thuật nội bộ Introduction & Methods cho JTE (29/10/2026)
**TRẠNG THÁI:** BẢN NHÁP CHƯA CÓ KẾT QUẢ NHIỆT ĐƯỢC NGHIỆM THU; KHÔNG SẴN SÀNG NỘP. Dấu [CẦN...] là thông tin còn thiếu, không được tự điền. Sử dụng cùng đề tài, MathWorks reference 24.2.1.5 và quy tắc nghiên cứu trong JTE-040/JTE-042; chưa đại diện Porsche Taycan hay thử nghiệm thực tế.

**Tiêu đề Việt đề xuất (cần kiểm đếm từ theo JTE):** Ảnh hưởng sai lệch cảm biến nhiệt độ đến điều khiển làm mát pin xe điện bằng chất lỏng

**Keywords (English/Vietnamese):** Battery thermal management / Quản lý nhiệt pin; Temperature sensor bias / Sai lệch cảm biến nhiệt độ; Liquid cooling / Làm mát bằng chất lỏng; Maximum-temperature feedback / Phản hồi nhiệt độ cực đại; Closed-loop simulation / Mô phỏng vòng kín; Fault injection / Chèn sai lệch.

## 1. Đặt vấn đề — bản nháp dựa trên công trình đã đối chiếu
Hệ thống quản lý nhiệt pin (battery thermal management system — BTMS) điều chỉnh công suất làm mát dựa trên tín hiệu nhiệt độ nhằm kiểm soát điều kiện vận hành của bộ pin. Trong các cấu trúc điều khiển sử dụng nhiệt độ cực đại làm biến phản hồi, tín hiệu của một phần tử đo có thể bị che lấp bởi những phần tử nóng hơn hoặc làm thay đổi kênh quyết định lệnh làm mát. Do đó, độ lớn sai lệch tại một kênh không nhất thiết tương ứng trực tiếp với thay đổi lệnh điều khiển và càng không thể được đồng nhất với thay đổi nhiệt độ thật trong hệ thống vòng kín.

Những nghiên cứu trước đã phát triển nhiều hướng liên quan đến lỗi cảm biến và quản lý nhiệt pin. Dey và cộng sự [1] xét phát hiện, cô lập và ước lượng lỗi cảm biến trong hệ pin lithium-ion; Bhaskar và cộng sự [2] nghiên cứu tái tạo tín hiệu đo lỗi của pack pin; Naguib và cộng sự [3] kết hợp mô hình vật lý và mạng nơ-ron để phát hiện lỗi nhiệt, trong đó có lỗi cảm biến và thành phần làm mát, trên cấu hình làm mát bằng không khí. Các kết quả này cho thấy mô hình hóa hoặc chẩn đoán sai lệch cảm biến không phải đóng góp mới độc lập. Các nghiên cứu gần đây về mô hình nhiệt phân bố và observer còn khảo sát lỗi cảm biến theo không gian và độ lớn [4–6]. [CẦN ĐỐI CHIẾU TOÀN VĂN F05–F07: chính xác mức độ xem xét coolant command, true thermal response và mô hình đối chứng trước khi khóa Research Gap.]

Trên cơ sở đó, công trình này được **thiết kế** để xem xét câu hỏi hẹp hơn: khi một kênh nhiệt độ đưa vào bộ chọn cực đại nhận sai lệch âm cố định, ảnh hưởng của sai lệch đó truyền qua bộ điều khiển làm mát chất lỏng và động học bộ chấp hành như thế nào; trong những điều kiện nào thay đổi tín hiệu đo không làm đổi lệnh, và khi nào có thể phân biệt thay đổi nhiệt độ thật với độ nhạy số học của mô hình. Nghiên cứu sử dụng một bộ mô hình và cấu trúc điều khiển tham chiếu đã khóa, không đề xuất thuật toán phát hiện lỗi mới hoặc một bộ điều khiển tối ưu mới. **Đóng góp ứng viên** là quy trình đánh giá khép kín giữa cơ chế che lấp tín hiệu đo, sự kiện chuyển mức điều khiển và đáp ứng nhiệt vòng kín, với các ca đối chứng âm được khai báo trước. Những đóng góp này chỉ có thể xác nhận sau khi có mô phỏng được nghiệm thu và hoàn tất đối chiếu tài liệu.

## 2. Đối tượng và phương pháp — bản nháp chuẩn bị trước mô phỏng
### 2.1. Mô hình và đường tín hiệu
Mô hình được lựa chọn là `Battery_Pack_Thermal_Management` thuộc bộ `Battery-Pack-Model-Simscape` của MathWorks, tag 24.2.1.5, nguồn SLX được ghim theo SHA-256 trong hồ sơ dự án. Môi trường mô phỏng mục tiêu là MATLAB/Simulink R2024b Update 10. Mô hình chứa 312 kênh nhiệt độ tính toán; số lượng này mô tả các kênh tín hiệu mô phỏng, không được xem là số cảm biến vật lý trong một bộ pin thương mại. Hệ thống điều khiển `FlwR_calc` nhận nhiệt độ cực đại tại cổng 1 và nhiệt độ môi trường tại cổng 2. Nhánh cảm biến tạo sai lệch chỉ tác động đến tín hiệu đưa vào điều khiển, không trực tiếp thay đổi các trạng thái nhiệt do mô hình vật lý tính toán.

Tín hiệu điều khiển `u_core` được phân biệt với đầu ra động học bộ chấp hành, lưu lượng khối lượng của chất làm mát và công suất điện phụ. Chỉ chuyển từ giá trị lệnh chuẩn hóa sang đơn vị vật lý khi đã kiểm tra ánh xạ và đường tín hiệu liên quan trong bản mô hình nguồn. Mọi trường hợp so sánh phải ghi phiên bản phần mềm, mã nguồn, SHA mô hình, điều kiện đầu, cấu hình solver, tốc độ lấy mẫu, tải và biến môi trường.

### 2.2. Biểu diễn sai lệch đo
Với `N=312`, tại thời điểm `t`, gọi `T_i,true(t)` là nhiệt độ mô hình của kênh `i`, còn `j` là một kênh sai lệch cố định trong suốt một ca. Mô hình lỗi được định nghĩa:
`T_i,meas(t) = T_i,true(t) + b * 1(i=j)`, trong đó `b<=0` [K].
`Tmax,true(t)=max_i T_i,true(t)`, `Tmax,meas(t)=max_i T_i,meas(t)`.

Ở **cùng một vector trạng thái**, nếu `j` là kênh nóng nhất, việc giảm nhiệt độ đo tại kênh này làm thay đổi giá trị cực đại nhiều nhất bằng độ lớn sai lệch và bị giới hạn bởi khoảng cách tới kênh nóng thứ hai. Đây là tính chất đại số của phép chọn cực đại, **không** phải chênh lệch nhiệt độ thật giữa hai quỹ đạo vòng kín.

### 2.3. Đối chứng và chọn kênh lỗi
Hai cấu hình đối chứng `B0L` (clone chỉ bổ sung logger) và `C0` (clone có nhánh lỗi nhưng `b=0`) phải được kiểm chứng tương đương trên cùng điều kiện đầu, tải, solver, chu kỳ bộ chấp hành và thời gian mô phỏng, với ngữ nghĩa dấu thời gian đã được chứng nhận. Việc chỉ biên dịch thành công hoặc kiểm thử logger tổng hợp không đáp ứng điều kiện so sánh nhiệt.

**Ma trận tối thiểu đã định trước theo hồ sơ JTE-040:** Sau khi có baseline toàn chu kỳ 0–2400 s được nghiệm thu, ba chỉ số kênh `j_hot`, `j_mid`, `j_cold` được lựa chọn theo quy tắc đã khai báo trên toàn vector nhiệt độ không lỗi trong khoảng 1800–2400 s, sau đó cố định chỉ số cho từng ca lỗi `b=-2 K`. [CẦN BỔ SUNG: định nghĩa thứ hạng chi tiết, quy tắc xử lý đồng hạng, ID ba kênh và SHA manifest sau khi baseline hợp lệ.] Mức `-2 K` là mức khảo sát giả định; không suy diễn thành thông số độ chính xác của cảm biến thương mại. Các ca không thay đổi lệnh hoặc không có chênh lệch nhiệt phân biệt được vẫn được lưu và phân tích.

Các mức bổ sung `-1` hoặc `-3 K`, hồ sơ tải thứ hai và phân tích chu kỳ lấy mẫu chỉ được thực hiện khi có ma trận mở rộng được khai báo trước. Cửa sổ kỹ thuật 0–340 s với các mốc 330–334 s/330–338 s phục vụ kiểm tra hệ thống ban đầu, **không thay thế** baseline 1800–2400 s dùng để chọn kênh lỗi.

### 2.4. Chỉ tiêu và kiểm chứng sai số
Chỉ tiêu đầu ra bao gồm `Tmax,true(t)`, độ trải nhiệt `max_i T_i(t)-min_i T_i(t)`, `Tmax,meas(t)`, thời gian và giá trị chuyển mức `u_core`, trạng thái đầu ra bộ chấp hành, và `DeltaTmax,true(t)=Tmax,true,bias(t)-Tmax,true,C0(t)`. Cần phân biệt hiệu đỉnh riêng của hai quỹ đạo và đỉnh của hiệu tại từng thời điểm. Công suất bơm [W], năng lượng [Wh] và thời gian vượt ngưỡng chỉ báo cáo khi đường tín hiệu hoặc ngưỡng nhiệt có cơ sở kỹ thuật được xác minh.

Độ nhạy số học được đánh giá bằng cách thay đổi độ chính xác solver tại chu kỳ bộ chấp hành đã khóa, rồi khảo sát riêng ảnh hưởng thay đổi chu kỳ lấy mẫu nếu được duyệt. Sai khác hai quỹ đạo chỉ được xem là đáp ứng nhiệt phân biệt được khi có bất định số học định lượng cùng chính sách căn chỉnh dấu thời gian sự kiện. Không dùng số lượng lớn mẫu thời gian trong cùng một phép mô phỏng tất định để tạo p-value như các mẫu thực nghiệm độc lập.

### 2.5. Giới hạn và trạng thái dữ liệu
Kết quả được giới hạn ở mô hình tham chiếu và các điều kiện mô phỏng được báo cáo. Bộ nhiệt độ 312 kênh không đại diện trực tiếp mạng cảm biến thương mại, chưa có thí nghiệm xe thật và chưa có hiệu chuẩn thông số nhiệt từ mẫu pin vật lý. Tại ngày 29/10/2026, lỗi chứng nhận `G-M3` và chứng cứ trạng thái ban đầu của Simscape chưa được giải quyết; chưa có bộ kết quả nhiệt vòng kín của mô hình sửa đổi đủ điều kiện cho mục Kết quả và Bàn luận. Chỉ hoàn thiện Abstract, Results và Conclusion sau khi kiểm chứng dữ liệu.

## References (DANH MỤC TẠM, metadata đã đối chiếu ở các mức khác nhau; chuẩn hóa IEEE trước nộp)
[1] Dey et al., *Sensor Fault Detection, Isolation, and Estimation in Lithium-Ion Batteries*, IEEE TCST (2016), DOI 10.1109/TCST.2016.2538200.
[2] Bhaskar et al., *Faulty Sensor Signal Reconstruction in Li-Ion Battery Packs*, IEEE TTE 11(1), 359–368 (2025), DOI 10.1109/TTE.2024.3390652.
[3] Naguib et al., *Thermal fault detection of lithium-ion battery packs through an integrated physics and deep neural network based model*, Communications Engineering 4, 79 (2025), DOI 10.1038/s44172-025-00409-2.
[4] Chen et al., *Sensor fault diagnosis for distributed thermal process of large-format lithium-ion battery*, Journal of Power Sources 654, 237795 (2025), DOI 10.1016/j.jpowsour.2025.237795.
[5] *Model-based thermal fault detection and localization for large-format Li-ion battery*, Journal of Energy Storage 147, 120209 (2026), DOI 10.1016/j.est.2025.120209. [CẦN CHỐT TÁC GIẢ]
[6] Zhou et al., *Lightweight quantitative diagnosis of thermal faults in large-format Li-ion batteries*, Applied Thermal Engineering 304, 132511 (2026), DOI 10.1016/j.applthermaleng.2026.132511.

**Editorial:** Khối tham khảo trên chưa phải danh mục cuối; kiểm tra đủ tác giả/năm/tập/số/trang/DOI và thứ tự xuất hiện trước khi định dạng JTE.

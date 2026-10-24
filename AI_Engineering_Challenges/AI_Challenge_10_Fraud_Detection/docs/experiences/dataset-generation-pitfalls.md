# Bẫy khi sinh dataset làm lệch metrics hoặc lộ nhãn

**Found:** 2026-10-24 (ước lượng trước khi code, chưa đo)
**Scope:** generator (A) và cách đọc metrics (C): phân phối amount, chọn mã cho fraud, gán `claim_id`, FP tự nhiên.
**Artifact at time of discovery:** chưa có code; liên quan `src/generator/`, `src/rules/`
**Status:** có số đo sơ bộ (1,800 claim hợp lệ, seed 2024, 2026-10-24) - số chính thức đo lại sau khi generate đủ 2,000 claim và chạy engine

Mỗi mục: dự đoán -> cách xử lý khi sinh dữ liệu -> số đo thật (điền sau).

## 1. FP tự nhiên của upcoding

- **Dự đoán:** amount hợp lệ = giá chuẩn x log-normal dao động 15% => khoảng 2.5% claim hợp lệ tự vượt mean + 2 SD, tức khoảng 40-45 claim trên 1,800 claim hợp lệ.
- **Ảnh hưởng:** FPR vẫn thấp hơn nhiều so với 20%, nhưng precision giảm.
- **Xử lý:** chấp nhận (đúng quyết định "cho phép FP tự nhiên"), báo trong metrics report phần 3 và writeup.
- **Số đo sơ bộ:** 57 claim (3.2%), cao hơn dự đoán. Lý do: log-normal lệch phải, đuôi trên dày hơn phân phối chuẩn nên tỷ lệ vượt mean + 2 SD lớn hơn 2.5%.
- **Bài học:** ước lượng tỷ lệ vượt ngưỡng theo phân phối chuẩn sẽ thấp hơn thực tế khi amount sinh bằng log-normal. Số chính thức sẽ khác vì claim upcoded làm tăng mean / SD (mục 2).
- **Số đo thật:** (chưa có)

## 2. Masking làm giảm recall của upcoding

- **Dự đoán:** mean/SD tính cả claim upcoded => nếu nhiều claim upcoded dồn vào 1 mã, ngưỡng mean + 2 SD bị đẩy lên và một số claim upcoded không vượt ngưỡng.
- **Xử lý:** rải 30 claim upcoded ra nhiều mã (1 mã 1 claim upcoded là tốt nhất). Không dùng P-1003 cho upcoding vì P-1003 dành cho amount clustering.
- **Nếu recall upcoding vẫn thấp:** đổi sang leave-one-out (xem `../business-rule/upcoding.md`).
- **Số đo thật:** (chưa có)

## 3. FP tự nhiên của rapid re-submission

- **Dự đoán:** 500 member, mỗi người khoảng 3-4 claim => sẽ có cặp ngẫu nhiên cùng diagnosis cách nhau <= 7 ngày, ước khoảng 10-20 claim hợp lệ bị flag.
- **Xử lý:** chấp nhận và báo cáo. Sau khi generate đếm ngay; nếu vượt nhiều so với ước lượng thì xem lại cách rải ngày khám của một member.
- **Số đo sơ bộ:** 32 claim, gấp khoảng 2 lần dự đoán. Vẫn xa ngưỡng FPR 20%; chưa đổi cách rải ngày, chờ số chính thức.
- **Số đo thật:** (chưa có)

## 4. Lộ nhãn qua thứ tự `claim_id`

- **Dự đoán:** nếu sinh claim hợp lệ trước rồi chèn fraud sau và gán ID theo thứ tự sinh, claim fraud sẽ nằm cụm ở cuối dãy ID (vd `CLM-01801` -> `CLM-02000`). Người đọc dataset nhìn là biết dữ liệu giả.
- **Xử lý:** sinh xong toàn bộ claim, sắp theo `claim_date` (thứ tự phụ ngẫu nhiên theo seed), rồi mới gán `claim_id`.
- **Kiểm:** sau khi generate, xem phân bố vị trí ID của claim fraud.

## 5. Lộ nhãn qua định dạng amount

- **Đã gặp (khi rà plan, trước khi code):** plan cũ làm tròn claim hợp lệ tới 1,000 và claim clustering tới 100 => mọi amount không chia hết cho 1,000 (vd 48,300) chắc chắn là fraud clustering.
- **Xử lý:** mọi amount làm tròn tới 100, cả hợp lệ lẫn fraud.
- **Bài học:** mọi quy tắc định dạng (làm tròn, kiểu số, cách viết mã) phải giống nhau giữa claim hợp lệ và fraud.

## 6. Lộ nhãn qua quy mô provider

- **Đã gặp (chạy thử Phase 2):** chia trước 62 claim cho mỗi bệnh viện weekday-only rồi vẫn cho bốc thêm => nhóm này có 84-95 claim, bệnh viện thường 15-27. 10 bệnh viện lớn nhất luôn là nhóm weekday-only.
- **Xử lý:** mỗi bệnh viện weekday-only nhận ngẫu nhiên 62-70 claim và không nhận thêm. Đo lại: 63-69 so với bệnh viện thường 31-45.
- **Bài học:** ràng buộc đặt riêng cho một nhóm provider (số claim tối thiểu, chỉ ngày thường) có thể biến nhóm đó thành ngoại lệ thống kê. Sau khi sinh, so phân phối của nhóm đặc biệt với nhóm còn lại.

## 7. Số member sát ngưỡng kiểm

- **Đo sơ bộ:** chọn member đều cho 1,800 claim hợp lệ => 483 member khác nhau, chỉ trên ngưỡng 480 một chút (kỳ vọng với 2,000 claim là ~491).
- **Rủi ro:** đổi seed hoặc đổi số claim có thể làm Phase 5 fail ở ngưỡng 480.
- **Xử lý nếu fail:** chia trước mỗi member 1 claim hợp lệ (phương án đã cân nhắc khi chốt ngưỡng), không hạ ngưỡng.

## Rule derived

- Mọi FP tự nhiên được chấp nhận phải có số đo thật trong metrics report, không chỉ ước lượng.
- Generator không được để thứ tự hay định dạng của dữ liệu tiết lộ nhãn ground truth.

## Related

- `../business-rule/fraud-injection.md`, `../business-rule/upcoding.md`, `../business-rule/metrics.md`
- `../decisions/tech-and-structure.md` (hiệu năng B5, đo thời gian C4)

# Nhúng fraud vào dataset (A3)

Tổng hợp cách sinh 8 pattern fraud. Chi tiết "chuẩn" của từng rule xem các file cùng thư mục.

## Nguyên tắc chung

- Đếm theo **claim** (phương án C): tổng **200 claim fraud** / 2,000 claim (10%), đúng "~200 fraudulent claims (~10%)" của đề.
- Mỗi claim fraud mang **đúng 1 pattern** trong ground truth (giới hạn có chủ đích; thực tế 1 claim có thể nhiều pattern).
- Claim hợp lệ được phép tự nhiên kích hoạt rule (FP tự nhiên), đếm và báo trong metrics.
- Seed cố định để tái lập dataset.
- Amount của claim fraud thuộc pattern không dựa vào amount (duplicate, rapid, unbundling, phantom, weekend, mismatch): hệ số dao động kẹp trong [0.85, 1.15] (khoảng +-1 SD), để không vô tình dính upcoding hay clustering. Claim hợp lệ không kẹp (giữ FP tự nhiên có chủ đích).
- Amount làm tròn tới 1,000 VNĐ; riêng claim clustering lấy trong 47,500-49,999, làm tròn tới 100 VNĐ.
- Sau khi generate, generator (A) chỉ kiểm cấu trúc: đủ số claim theo pattern, mỗi mã >= 30 claim 1 mã, mỗi bệnh viện weekday-only >= 60 claim, không có nhóm duplicate ngoài 15 cặp chèn, không provider nào khác vượt 30 claim/ngày. Generator không chép lại logic rule.
- Kiểm chéo bằng engine ở C (test tích hợp chạy engine trên dataset thật): mỗi claim fraud chỉ dính đúng rule của pattern mình. Ngoại lệ đã biết: 6 claim trong ngày phantom (dính thêm phantom), cặp duplicate tự thỏa điều kiện rapid re-submission, nhưng rule rapid bỏ qua cặp trùng unique key duplicate (xem `duplicate-and-rapid-resubmission.md`) nên không bị flag 2 lần.

## Số lượng và cách sinh

| Pattern | Số claim | Cách sinh |
|---|---|---|
| Duplicate | 30 (15 cặp) | 2 claim cùng member + provider + date + diagnosis. Dữ liệu đã qua validate input, không có double-submit => 2 claim độc lập, **cả 2 mang nhãn fraud**. |
| Rapid re-submission | 30 (15 cặp) | 2 claim cùng member + diagnosis, **cách nhau 1-7 ngày** (không cùng ngày để không thành duplicate). Cả 2 mang nhãn fraud. |
| Upcoding | 30 | Amount = giá chuẩn x 1.6-2.5. Xem `upcoding.md`. |
| Unbundling | 25 | `procedure_codes` = đủ thành phần của 1 bundle. Xem `bundling.md`. |
| Phantom billing | 25 | 1 provider-day có **31 claim**: 25 claim nhãn phantom + 6 claim nhãn upcoding / mismatch (tính vào số của 2 pattern đó). Ngày thường, provider không thuộc nhóm weekday-only. |
| Weekend surgical anomaly | 20 | Procedure surgical vào thứ Bảy / Chủ nhật tại 10 bệnh viện weekday-only, 2 claim mỗi bệnh viện. Xem `weekday-only-providers.md`. |
| Diagnosis-procedure mismatch | 20 | Procedure ngoài danh sách hợp lệ của diagnosis. Xem `diagnosis-procedure-mismatch.md`. |
| Amount clustering | 20 | P-1003, amount 47,500-49,999. Xem `amount-clustering.md`. |
| **Tổng** | **200** | |

Ràng buộc cho 6 claim trong ngày phantom: chỉ dùng pattern xét được trên từng claim (upcoding, mismatch); không dùng duplicate / rapid (cần cặp claim) hay weekend (ngày phantom là ngày thường).

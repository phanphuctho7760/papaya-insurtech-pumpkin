# Trọng số rule (B3)

Đề yêu cầu: "Each rule has a configurable severity weight (1-5)" và "Scoring weights are justified".

## Tiêu chí chấm trọng số

1. **Độ chắc chắn của tín hiệu**: có lý do hợp lệ nào tạo ra cùng dấu hiệu không.
2. **Thiệt hại tài chính**: nếu là fraud thật, insurer mất bao nhiêu.

Mốc từ ví dụ output của đề: upcoding = 4, amount clustering = 2.

## Bảng trọng số

| Rule | Weight | Lý do |
|---|---|---|
| Duplicate | 5 | Dữ liệu đã qua validate => trùng unique key gần như chắc chắn là fraud; thiệt hại trả 2 lần cho cùng một lần khám. |
| Phantom billing | 4 | > 30 claim/ngày là bất thường rất rõ, thiệt hại lớn; nhưng rule flag mọi claim của ngày đó, có thể lẫn claim hợp lệ. |
| Upcoding | 4 | Theo ví dụ của đề. Thiệt hại trực tiếp; là ngưỡng thống kê nên khoảng 2% claim hợp lệ vẫn có thể vượt. |
| Diagnosis-procedure mismatch | 4 | Bất hợp lý y khoa rõ ràng; đôi khi do nhập sai mã. |
| Unbundling | 3 | Rule tất định, chắc chắn là tách gói; nhưng số tiền chênh chỉ khoảng 10% giá gói. |
| Rapid re-submission | 3 | Tái khám cùng bệnh trong 7 ngày vẫn có thể hợp lệ. |
| Weekend anomaly | 2 | Tín hiệu gián tiếp; lịch làm việc của bệnh viện có thể thay đổi. |
| Amount clustering | 2 | Theo ví dụ của đề. Tín hiệu yếu nhất; claim hợp lệ tự rơi vào dải (vd giá không BHYT 48,000 VNĐ). |

Tổng trọng số: 27. Trọng số là cấu hình, có thể chỉnh mà không sửa code.

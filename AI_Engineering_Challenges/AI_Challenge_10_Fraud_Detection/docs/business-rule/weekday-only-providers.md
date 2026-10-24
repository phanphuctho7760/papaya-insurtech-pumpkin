# Provider không làm cuối tuần (weekday-only)

Phục vụ pattern "weekend surgical anomaly" (rule 6).

## Nguồn trong đề

- Dataset: "20 weekend surgical anomalies (surgical procedures on weekends from providers who never operate on weekends)".
- Rule: "surgical procedures on weekends from providers with < 5% historical weekend volume".

## Quy tắc sinh dữ liệu

- Generator chọn **10 bệnh viện** (loại provider có phẫu thuật) làm weekday-only.
- Claim hợp lệ của nhóm này chỉ rơi vào thứ Hai - thứ Sáu.
- 20 claim fraud weekend surgical được chèn vào thứ Bảy / Chủ nhật, chia đều 2 claim cho mỗi provider weekday-only.
- Procedure surgical: P-3001, P-3002, P-3003, B-3101, B-3102 (xem `catalog.md`).
- Danh sách provider weekday-only được ghi lại sau khi generate.

## Điểm còn mở

- Cách tính "historical weekend volume" (bàn ở B1). Với ~40 claim/provider và 2 claim fraud cuối tuần, tỷ lệ là 2/40 = 5%, đúng biên ngưỡng => bắt buộc loại các claim đang xét ra khỏi phép tính.

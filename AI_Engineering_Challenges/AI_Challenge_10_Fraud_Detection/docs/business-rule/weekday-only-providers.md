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

## Cách tính tỷ lệ cuối tuần (đã chốt)

- Rule 6 tính tỷ lệ cuối tuần trên **toàn bộ claim** của provider, đúng nguyên văn đề.
- Generator cho mỗi bệnh viện weekday-only **>= 60 claim**. 2 claim fraud cuối tuần => 2/60 = 3.3% < 5% => rule bắt được.
- Lý do: với ~40 claim/provider, 2/40 = 5% không < 5% => bỏ sót.
- Không đưa khái niệm cấp cứu vào phạm vi.

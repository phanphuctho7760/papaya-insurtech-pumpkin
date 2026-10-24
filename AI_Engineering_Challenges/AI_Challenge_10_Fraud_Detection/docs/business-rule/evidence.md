# Evidence (B2)

Đề yêu cầu: "Each flag includes specific, actionable evidence (not just 'flagged by rule 3')".

## Nguyên tắc

- Ngôn ngữ: **tiếng Anh** (theo ví dụ output của đề).
- Mỗi evidence có đủ 3 phần: **giá trị quan sát** của claim, **giá trị so sánh + ngưỡng** của rule, **claim liên quan** (nếu có).
- Mã procedure / diagnosis luôn kèm **tên tiếng Anh** (xem `catalog.md`, `icd-10.md`) để người thẩm định đọc hiểu không cần tra mã.
- Số tiền định dạng có dấu phân cách hàng nghìn và đơn vị VND.

## Mẫu cho 8 rule

| # | Rule | Mẫu evidence |
|---|---|---|
| 1 | Duplicate | `Duplicate of CLM-00456: same member MEM-0042, provider PRV-007, date 2024-03-15, diagnosis K35.8 (Acute appendicitis) - 2 claims share this key` |
| 2 | Rapid re-submission | `Re-submitted 3 days after CLM-00456 (2024-03-12) for the same member MEM-0042 and diagnosis J06.9 (Acute upper respiratory infection) - window: 7 days` |
| 3 | Upcoding | `Submitted amount 900,000 VND for procedure P-4003 (Dental filling) is 8.3 standard deviations above the mean of 410,000 VND (threshold 530,000 VND, based on 95 claims)` |
| 4 | Unbundling | `Procedures P-3001 (Laparoscopic appendectomy) + P-3010 (General anesthesia) billed separately for 21,400,000 VND instead of bundle B-3101 (Appendectomy package) at 19,000,000 VND` |
| 5 | Phantom billing | `Provider PRV-012 submitted 31 claims on 2024-06-18 (threshold: more than 30 per day)` |
| 6 | Weekend anomaly | `Surgical procedure P-3001 (Laparoscopic appendectomy) on Saturday 2024-05-11 at provider PRV-003, whose weekend volume is 3.3% (2 of 60 claims, threshold < 5%)` |
| 7 | Diagnosis-procedure mismatch | `Procedure P-3001 (Laparoscopic appendectomy) is not valid for diagnosis K02.1 (Dental caries); valid procedures: P-4001, P-4002, P-4003` |
| 8 | Amount clustering | `Amount 48,500 VND is 97% of the 50,000 VND auto-approval threshold (band 47,500-49,999)` |

Số liệu trong mẫu là minh họa; evidence thật lấy số từ dataset.

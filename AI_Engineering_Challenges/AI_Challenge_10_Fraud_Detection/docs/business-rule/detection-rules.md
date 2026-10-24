# 8 detection rule

Tổng hợp business của 8 rule. Nguồn: `AI_Challenge_10.md`, mục Detection Rules. Dữ liệu tham chiếu (procedure, bundle, cặp hợp lệ): `catalog.md`.

Quy ước chung:
- Mỗi rule xét từng claim, trả về flag (có / không) kèm evidence cụ thể có số liệu. Mẫu evidence: `evidence.md`.
- Một claim có thể bị nhiều rule flag (dù ground truth chỉ gán 1 pattern).

| # | Rule | Nguyên văn đề | Điều kiện flag | Chi tiết |
|---|---|---|---|---|
| 1 | Duplicate | same member + provider + date + diagnosis | Unique key `(member_id, provider_id, claim_date, diagnosis_code)` có >= 2 claim => flag tất cả claim trong nhóm | `duplicate-and-rapid-resubmission.md` |
| 2 | Rapid re-submission | same member + same diagnosis within 7 days | Cặp claim cùng `(member_id, diagnosis_code)` cách nhau 0-7 ngày, **trừ** cặp trùng unique key duplicate => flag cả 2 claim | `duplicate-and-rapid-resubmission.md` |
| 3 | Upcoding | amount > 2 standard deviations above mean for that procedure code | `submitted_amount` > mean + 2 x SD của các claim cùng mã procedure; mean/SD tính trên toàn bộ claim cùng mã | `upcoding.md` |
| 4 | Unbundling | multiple individual procedures when a bundled code exists | `procedure_codes` chứa **đủ tất cả** thành phần của một bundle | `bundling.md` |
| 5 | Phantom billing | provider submits > 30 claims in a single day | Provider có > 30 claim trong cùng `claim_date` => flag mọi claim của provider ngày đó | `fraud-injection.md` |
| 6 | Weekend anomaly | surgical procedures on weekends from providers with < 5% historical weekend volume | Claim có procedure surgical, `is_weekend` = 1, và tỷ lệ claim cuối tuần của provider (tính trên toàn bộ claim của provider) < 5% | `weekday-only-providers.md` |
| 7 | Diagnosis-procedure mismatch | procedure not clinically associated with diagnosis | Có ít nhất 1 mã trong `procedure_codes` không nằm trong danh sách hợp lệ của `diagnosis_code` | `diagnosis-procedure-mismatch.md` |
| 8 | Amount clustering | claim amounts within 5% below the 50,000 auto-approval threshold (47,500-49,999) | 47,500 <= `submitted_amount` <= 49,999 (VNĐ) | `amount-clustering.md` |

## Ghi chú

- Rule 4 (unbundling): các mã thành phần đều là cặp hợp lệ với diagnosis của gói, nên claim unbundled không dính rule 7.
- Rule 3: mã có < 10 claim thì không xét.
- Rule 6: provider có lịch bình thường có khoảng 28% claim rơi vào cuối tuần (theo lịch 2024), không bị flag. Mỗi bệnh viện weekday-only có >= 60 claim để 2 claim fraud cuối tuần chỉ chiếm 2/60 = 3.3% < 5%.
- Không đưa khái niệm cấp cứu vào phạm vi (đề không nhắc tới).

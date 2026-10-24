# Định dạng file dataset (A5)

## Chung

- Định dạng: CSV theo RFC 4180, phân cách cột bằng `,`, encoding UTF-8, có dòng header.
- Tên provider tự đặt không chứa dấu `,`.

## claims.csv (input của engine, đúng 10 cột của đề)

| Cột | Định dạng | Ví dụ |
|---|---|---|
| claim_id | chuỗi, duy nhất | `CLM-00123` |
| member_id | chuỗi | `MEM-0042` |
| provider_id | chuỗi | `PRV-007` |
| provider_name | chuỗi, không chứa `,` | `Benh vien Da khoa An Phuc` |
| claim_date | `YYYY-MM-DD` | `2024-03-15` |
| claim_type | `OUTPATIENT` / `INPATIENT` / `DENTAL` | `INPATIENT` |
| diagnosis_code | mã ICD-10 | `K35.8` |
| procedure_codes | danh sách mã, phân cách bằng `\|` | `P-3001\|P-3010` |
| submitted_amount | số nguyên VNĐ, không dấu phân cách hàng nghìn | `18250000` |
| is_weekend | `1` / `0` | `0` |

Đọc `procedure_codes`: `split("|")` => list. Mã không bao giờ chứa `|`.

## ground_truth.csv (chỉ dùng để đo metrics, engine không đọc)

| Cột | Định dạng | Ví dụ |
|---|---|---|
| claim_id | khớp claims.csv | `CLM-00123` |
| is_fraud | `1` / `0` | `1` |
| fraud_pattern | tên pattern hoặc rỗng nếu hợp lệ | `upcoding` |

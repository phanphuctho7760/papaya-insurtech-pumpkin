# Duplicate và Rapid re-submission

## Nguồn trong đề

- Rule 1 Duplicate: "same member + provider + date + diagnosis".
- Rule 2 Rapid re-submission: "same member + same diagnosis within 7 days".

## Giả định

- Dữ liệu đã qua validate input, không có double-submit. Hai claim trùng là hai claim độc lập và là fraud.

## Duplicate

- **Unique key**: `(member_id, provider_id, claim_date, diagnosis_code)`. Một claim hợp lệ phải là duy nhất theo key này.
- Nhóm claim theo key; nhóm có >= 2 claim => mọi claim trong nhóm là duplicate, **flag tất cả**.

## Rapid re-submission

- Cặp claim cùng `(member_id, diagnosis_code)`, cách nhau 0-7 ngày.
- **Bỏ qua cặp có cùng unique key duplicate** (đã thuộc rule Duplicate), để không flag 2 lần.
- Cặp cùng member + diagnosis + ngày nhưng khác provider: không phải duplicate => vẫn thuộc rapid re-submission.
- Flag cả 2 claim trong cặp.

## Sinh dữ liệu

- Duplicate: 15 cặp (30 claim), cả 2 claim mang nhãn fraud.
- Rapid: 15 cặp (30 claim), cách nhau 1-7 ngày, cả 2 claim mang nhãn fraud.

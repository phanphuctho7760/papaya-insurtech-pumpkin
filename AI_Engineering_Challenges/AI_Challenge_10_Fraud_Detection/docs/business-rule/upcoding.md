# Upcoding (khai nâng mức)

## Thuật ngữ

Upcoding: khai số tiền (hoặc mã) đắt hơn dịch vụ thực tế đã làm. Ví dụ trám răng giá chuẩn 400,000, khai 900,000.

## Nguồn trong đề

- Dataset: "30 upcoded claims (amount > 2 standard deviations above mean for that procedure)".
- Rule 3: "amount > 2 standard deviations above mean for that procedure code".

## Thế nào là "chuẩn"

- Mỗi procedure / bundle có giá chuẩn (xem `catalog.md`).
- Claim hợp lệ: amount = giá chuẩn x hệ số log-normal, dao động khoảng 15%.
- Vì claim hợp lệ chỉ có 1 mã, "mean for that procedure" = mean amount của các claim có cùng mã đó.

## Lưu ý: "2 SD" không phải "gấp 2 lần"

- Ngưỡng rule = mean + 2 x SD. Với dao động 15%, SD khoảng 15% mean => ngưỡng khoảng 1.3 lần mean.
- Ví dụ trám răng: mean 400,000, SD khoảng 60,000 => ngưỡng khoảng 520,000.

## Quy tắc sinh fraud

- Claim upcoded: amount = giá chuẩn x hệ số 1.6-2.5 (vượt ngưỡng 2 SD, vẫn gần thực tế).

## Cách tính mean / SD (đã chốt ở B1)

- Tính mean và SD trên **toàn bộ claim có cùng mã**, gồm cả claim upcoded. Giữ đúng chữ của đề ("mean for that procedure code").
- Hệ quả đã biết (masking): claim upcoded làm tăng mean và SD => ngưỡng mean + 2 SD bị đẩy lên, một số claim upcoded có thể không vượt ngưỡng => giảm recall.
- Cách xử lý: đo recall của rule upcoding trên dataset trước. Chỉ khi không đạt mục tiêu mới đổi sang loại trừ claim đang xét (leave-one-out). Ghi kết quả đo và quyết định vào writeup.

## Số claim tối thiểu

- Mã có < 10 claim: **không xét upcoding** (không đủ dữ liệu lịch sử để kết luận khai giá cao).
- Generator sinh mỗi mã >= 30 claim để mọi mã đều được xét.

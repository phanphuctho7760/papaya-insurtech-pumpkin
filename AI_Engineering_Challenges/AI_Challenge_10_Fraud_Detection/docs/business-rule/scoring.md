# Scoring (B4)

Đề yêu cầu: "Composite score = weighted sum of triggered rules, normalized to 0-100" và "Output ranked list of claims by risk score".

## 3 bước cho mỗi claim

1. **8 rule kiểm tra điều kiện** => mỗi rule trả về có / không + evidence (`detection-rules.md`, `evidence.md`).
2. **Weighted scoring**: `total = tổng weight của các rule bị flag` (weight: `scoring-weights.md`).
3. **Scoring scale (0-100)**: `risk_score = round(100 x (1 - e^(-0.25 x total)))`.

Bước 2 và 3 là một công thức áp cho mọi claim; xử lý theo từng loại case chỉ nằm ở bước 1.

## Vì sao chọn công thức bão hòa (k = 0.25)

| Cách | Công thức | Ví dụ đề (4 + 2 = 6) | Chỉ Duplicate (5) | Chỉ Clustering (2) |
|---|---|---|---|---|
| Chia tổng weight | total / 27 x 100 | 22 | 19 | 7 |
| Chia mốc trần 10 | min(100, total / 10 x 100) | 60 | 50 | 20 |
| **Bão hòa** | **100 x (1 - e^(-0.25 x total))** | **78** | **71** | **39** |

- Khớp đúng ví dụ output của đề (score 78 cho upcoding + clustering): 1 - e^(-1.5) = 0.777.
- Không bao giờ vượt 100 dù dính nhiều rule.
- Một rule mạnh đơn lẻ vẫn cho score cao (Duplicate => 71), phản ánh đúng mức rủi ro.

Bảng tham chiếu: total 2 => 39, 3 => 53, 4 => 63, 5 => 71, 6 => 78, 8 => 86, 10 => 92.

## Xếp hạng và output

- Sắp xếp `risk_score` giảm dần; bằng điểm thì số flag nhiều hơn trước, sau đó theo `claim_id`.
- Output gồm **toàn bộ 2,000 claim**; claim không dính rule có `risk_score` = 0 và `flags: []`.
- Mỗi flag có `rule`, `severity` (= weight của rule), `evidence`. Format theo ví dụ của đề.

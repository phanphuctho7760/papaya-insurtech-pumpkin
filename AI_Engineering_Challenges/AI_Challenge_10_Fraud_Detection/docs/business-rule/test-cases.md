# Test cases (C1)

Đề yêu cầu: "At least 15 unit tests covering individual rules and edge cases". Kế hoạch: 19 test.

| # | Rule | Test | Kết quả mong đợi |
|---|---|---|---|
| 1 | Duplicate | 2 claim trùng unique key | Flag cả 2 |
| 2 | Duplicate | Cùng member + date + diagnosis, khác provider | Không flag duplicate |
| 3 | Rapid | Cùng member + diagnosis, cách 7 ngày | Flag |
| 4 | Rapid | Cách 8 ngày | Không flag |
| 5 | Rapid | Cặp trùng unique key duplicate | Không flag rapid |
| 6 | Upcoding | Amount > mean + 2 SD | Flag |
| 7 | Upcoding | Mã có < 10 claim | Không xét, không flag |
| 8 | Unbundling | Đủ thành phần của bundle | Flag |
| 9 | Unbundling | Thiếu 1 thành phần | Không flag |
| 10 | Phantom | Provider có 31 claim trong ngày | Flag |
| 11 | Phantom | Đúng 30 claim | Không flag |
| 12 | Weekend | Surgical cuối tuần, provider có tỷ lệ cuối tuần 3.3% | Flag |
| 13 | Weekend | Cuối tuần nhưng không phải surgical | Không flag |
| 14 | Mismatch | K02.1 + P-3001 | Flag |
| 15 | Mismatch | Cặp hợp lệ | Không flag |
| 16 | Clustering | Amount 47,500 và 49,999 | Flag |
| 17 | Clustering | Amount 47,499 và 50,000 | Không flag |
| 18 | Scoring | total = 6 (4 + 2) | risk_score = 78 |
| 19 | Scoring | Không có flag | risk_score = 0, flags rỗng |

## Test tích hợp (ngoài 19 unit test)

- Chạy engine trên `claims.csv` thật, so với `ground_truth.csv`: mỗi claim fraud chỉ dính rule của pattern mình, trừ ngoại lệ đã ghi trong `fraud-injection.md`.
- Thời gian chạy 2,000 claim < 30 giây.

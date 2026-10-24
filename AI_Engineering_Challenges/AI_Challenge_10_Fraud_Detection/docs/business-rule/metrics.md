# Metrics (C2)

Đề yêu cầu: "Report precision and recall against the known fraudulent claims. Target: >= 70% recall with <= 20% false positive rate".
Định nghĩa TP / FP / FN / TN, precision, recall, FPR: xem `catalog.md`, mục "Thuật ngữ đánh giá".

## Dự đoán fraud

- Engine trả score 0-100; ground truth chỉ có fraud / không fraud => cần ngưỡng đổi score thành có / không.
- Metrics chính: **dự đoán fraud khi `risk_score` > 0** (có >= 1 flag).
- Lý do: đề ưu tiên recall >= 70%; ngưỡng cao hơn (vd >= 40) sẽ bỏ sót các fraud chỉ dính rule yếu (weekend, clustering = 39 điểm), khoảng 40 claim = 20% số fraud.
- FPR = FP / (FP + TN) (định nghĩa chuẩn).

## Bảng bổ sung theo ngưỡng

- Report thêm recall và FPR tại các ngưỡng score 0, 40, 70 để thấy đánh đổi.
- Ý nghĩa thực tế: nếu người thẩm định chỉ xem claim score cao thì bỏ sót bao nhiêu fraud.

## Metrics report (C3)

Report gồm 4 phần:

1. **Tổng thể**: TP, FP, FN, TN, precision, recall, FPR; so với mục tiêu recall >= 70%, FPR <= 20%.
2. **Theo pattern**: mỗi pattern có bao nhiêu claim fraud, bắt được bao nhiêu (chỉ ra rule yếu, vd upcoding bị masking).
3. **FP tự nhiên theo rule**: đếm báo nhầm theo từng rule (chứng minh dữ liệu có nhiễu thật).
4. **Bảng theo ngưỡng**: recall / FPR tại ngưỡng score 0, 40, 70.

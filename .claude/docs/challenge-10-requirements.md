# Challenge 10 - Phân rã yêu cầu

Phân rã yêu cầu của AI Challenge 10 - Fraud Detection Scoring Engine thành các mục chính và chi tiết.
Nguồn: `.tmp/pumpkin-main/Hiring/AI_Engineering_Challenges/AI_Challenge_10.md` (R1-R7) và `.tmp/pumpkin-main/Hiring/AI_Engineering_Challenges/README.md` (R8).
Giai đoạn: New Task (theo Task_Lifecycle). Chưa chọn công nghệ.

## Danh sách yêu cầu gốc (R)

| Mã | Yêu cầu | Nguồn |
|---|---|---|
| R1 | Ước lượng và báo timeline | Đề, mục Note |
| R2 | Sinh dataset 2,000 claim, 10 cột, nhúng ~200 fraud theo 8 pattern, có ground truth | Đề, mục Dataset |
| R3 | Dữ liệu tham chiếu: >= 5 bundle, >= 10 cặp diagnosis-procedure hợp lệ, bộ mã dùng chung | Đề, mục Detection Rules |
| R4 | 8 rule phát hiện, mỗi flag có evidence cụ thể | Đề, mục Detection Rules + Evaluation Criteria |
| R5 | Weight 1-5 cấu hình được, score 0-100, ranked list, JSON per claim, giải thích weight | Đề, mục Output + Scoring + Evaluation Criteria |
| R6 | Precision, recall so với ground truth; recall >= 70%, FPR <= 20%; metrics report | Đề, mục Metrics + Submission |
| R7 | >= 15 unit test (từng rule + edge case); 2,000 claim chạy < 30 giây | Đề, mục Evaluation Criteria |
| R8 | Repo GitHub, writeup, log hội thoại AI nguyên văn (bắt buộc, thiếu là trượt), không one-shot | README chung |

## Mục chính và chi tiết

### A. Tạo dataset

- A1. Schema 10 cột, 2,000 claim, ~500 member, ~50 provider, năm 2024; `is_weekend` suy ra từ `claim_date`. (R2)
- A2. Dữ liệu tham chiếu: bộ mã ICD-10 và procedure, >= 5 bundle, >= 10 cặp diagnosis-procedure hợp lệ, danh sách procedure surgical. Dùng chung cho mục B. (R3)
- A3. Nhúng ~200 fraud theo 8 pattern, đúng số lượng đề. (R2)
- A4. Nhãn ground truth cho từng claim. (R2)
- A5. Xuất file dataset để nộp. (R8)

### B. Viết rule logic (engine)

- B1. 8 rule phát hiện. (R4)
- B2. Evidence cụ thể, có số liệu cho từng flag. (R4)
- B3. Weight 1-5 cấu hình được, kèm lý do chọn. (R5)
- B4. Score 0-100, output JSON per claim, danh sách xếp hạng theo score. (R5)
- B5. Ràng buộc hiệu năng: 2,000 claim < 30 giây. (R7)

### C. Kiểm chứng

- C1. >= 15 unit test cho từng rule và edge case. (R7)
- C2. Precision và recall so với ground truth; mục tiêu recall >= 70%, FPR <= 20%. (R6)
- C3. Metrics report. (R6)
- C4. Đo thời gian chạy để chứng minh B5. (R7)

### D. Bàn giao (không phải code)

- D1. Ước lượng timeline gửi Papaya. (R1)
- D2. Writeup trong README: cách tiếp cận, quyết định, lý do chọn weight. (R5, R8)
- D3. Log hội thoại AI nguyên văn, bắt buộc. (R8)
- D4. Repo GitHub chứa đủ dataset, scored output, metrics report. (R8)

## Quyết định đã chốt

- Giai đoạn hiện tại: New Task. Chọn công nghệ để sau (có thể làm ở Claude Code).
- Timeline mục tiêu 4-6 giờ, chưa cam kết đến khi phân tích xong đề.
- Duplicate: dữ liệu đã qua validate input, không có double-submit; hai claim trùng là hai claim độc lập và là fraud. Rule flag cả 2 claim trong cặp, cả 2 mang nhãn fraud.

## Câu hỏi mở (bàn khi đi vào chi tiết từng mục)

| Mục | Câu hỏi |
|---|---|
| A3 | "30 duplicate claims" là 30 claim (15 cặp) hay 30 cặp (60 claim)? Đề xuất 15 cặp để giữ tổng ~200. |
| A3 / B1 | Phantom billing: đề yêu cầu 25 claim nhưng rule là > 30 claim/provider/ngày. Gán nhãn cả ngày bất thường (31 claim) hay giữ 25 và chấp nhận 6 FP? |
| A3 / B1 | Weekend anomaly: "never operate on weekends" (Dataset) và "< 5% historical weekend volume" (Rule) không khớp; cách tính "historical"; danh sách surgical. |
| A2 / B1 | Upcoding: `submitted_amount` là cấp claim, "mean per procedure" là cấp procedure; quy đổi thế nào. |
| A2 | Diagnosis-procedure: tập mã phải khép kín để claim hợp lệ không bị flag hàng loạt. |
| A3 | Amount clustering: claim hợp lệ có được rơi vào 47,500-49,999 không. |
| B4 | Ví dụ output của đề (severity 4 + 2, score 78) không khớp chuẩn hóa tuyến tính; chọn cách chuẩn hóa. |
| C2 | Định nghĩa "dự đoán fraud" (có >= 1 flag hay score > ngưỡng); FPR = FP/(FP+TN) hay 1 - precision. |
| A4 | Một claim có được mang nhiều pattern fraud không. |

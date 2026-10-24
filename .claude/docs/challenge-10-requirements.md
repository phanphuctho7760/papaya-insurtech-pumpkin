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
- Timeline 5-7h (kế hoạch 6h): dataset 1.5h, logic 1.75h, unit test 1.25h (gồm C2, C3, C4), buffer 1.5h. Ghi tại `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/README.md`.
- A: viết code generator, ràng buộc sinh đủ các pattern fraud theo đề.
- A: dữ liệu hợp lệ được phép tự nhiên kích hoạt rule (FP tự nhiên), đếm và báo trong metrics.
- A2: diagnosis dùng mã ICD-10 thật; procedure dùng mã tự đặt `P-xxxx`. Xem `docs/business-rule/icd-10.md`.
- A4: tách input (`claims.csv`, chỉ 10 cột của đề) và ground truth (`ground_truth.csv`: claim_id, is_fraud, fraud_pattern). Engine không đọc ground truth.
- A: seed cố định để tái lập dataset.
- A3: một claim fraud chỉ mang 1 pattern (giới hạn có chủ đích; thực tế có thể nhiều).
- A3: có nhóm provider weekday-only. Xem `docs/business-rule/weekday-only-providers.md`.
- Cách đếm fraud: phương án C, đếm theo claim, tổng 200 claim fraud. Duplicate 15 cặp (30 claim). Phantom: 1 provider-day có 31 claim = 25 claim nhãn phantom + 6 claim nhãn upcoding/mismatch.
- Provider: 50 provider, 3 loại (bệnh viện, phòng khám, nha khoa); 10 bệnh viện weekday-only, mỗi provider nhận 2 claim weekend fraud.
- Đơn vị VNĐ, giữ nguyên số của đề; mặt bằng giá bệnh viện tư.
- A2 đã ghi: `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/docs/business-rule/` (catalog, icd-10, upcoding, bundling, diagnosis-procedure-mismatch, amount-clustering, weekday-only-providers).
- Claim hợp lệ có đúng 1 mã procedure; amount = giá chuẩn x log-normal dao động 15%; upcoded = giá chuẩn x 1.6-2.5.
- Unbundling flag khi claim chứa đủ tất cả thành phần của bundle.
- Amount clustering dùng P-1003 (giá chuẩn 40,000, dao động 15%).
- A3: rapid re-submission 15 cặp (30 claim), cả 2 claim mang nhãn fraud, cách nhau 1-7 ngày. Tổng hợp: `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/docs/business-rule/fraud-injection.md`.
- A5: CSV RFC 4180 (phân cách `,`), `procedure_codes` phân cách `|`, ngày `YYYY-MM-DD`, amount số nguyên VNĐ, `is_weekend` 1/0, ground truth file riêng. Xem `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/docs/dataset-format.md`.
- Mục A: đã chốt xong.
- Duplicate: dữ liệu đã qua validate input, không có double-submit; hai claim trùng là hai claim độc lập và là fraud. Rule flag cả 2 claim trong cặp, cả 2 mang nhãn fraud.

## Câu hỏi mở (bàn khi đi vào chi tiết từng mục)

| Mục | Câu hỏi |
|---|---|
| B1 | Weekend anomaly: cách tính "historical weekend volume" (loại claim đang xét). |
| B1 | Upcoding: mean/SD có loại claim upcoded ra không (masking); số claim tối thiểu mỗi mã. |
| B1 | Duplicate claim cũng thỏa rapid re-submission: rule rapid có loại trừ không. |
| B4 | Ví dụ output của đề (severity 4 + 2, score 78) không khớp chuẩn hóa tuyến tính; chọn cách chuẩn hóa. |
| C2 | Định nghĩa "dự đoán fraud" (có >= 1 flag hay score > ngưỡng); FPR = FP/(FP+TN) hay 1 - precision. |

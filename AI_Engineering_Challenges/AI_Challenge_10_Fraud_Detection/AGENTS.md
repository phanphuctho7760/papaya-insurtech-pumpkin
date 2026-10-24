# AGENTS.md - AI Engineering Challenges

Thư mục này tập trung cho **AI Challenge 10 - Fraud Detection Scoring Engine** (Advanced, 3 điểm, ước lượng của đề 4-6 giờ).
Code đặt trong thư mục này (`AI_Challenge_10_Fraud_Detection/`).

## Cấu trúc dự kiến của `AI_Challenge_10_Fraud_Detection/`

```
AI_Challenge_10_Fraud_Detection/
|-- README.md          # writeup nộp bài: cách tiếp cận, quyết định, trọng số, metrics, Agent Workflow
|-- AGENTS.md          # hướng dẫn agent cấp project
|-- src/               # source code
`-- conversations/     # log hội thoại AI nguyên văn (bắt buộc nộp)
    `-- README.md      # mục lục log: phiên nào, công cụ nào, nội dung chính
```

## Lưu log hội thoại AI

- Claude Chat: đang cân nhắc lưu bằng skill `/noteconversaion-clacowo-bunhy`.
- Claude Code: lưu bằng tính năng export.
- Mọi log đặt trong `conversations/`, giữ nguyên văn, không chỉnh sửa lại nội dung. `conversations/README.md` liệt kê từng file log.
- Agent nhắc người dùng lưu log khi kết thúc mỗi phiên làm việc quan trọng.

## Tài liệu phải đọc

- Đề: `../../.tmp/pumpkin-main/Hiring/AI_Engineering_Challenges/AI_Challenge_10.md`
- Quy định chung: `../../.tmp/pumpkin-main/Hiring/AI_Engineering_Challenges/README.md`
- Ghi chú Handbook cho Challenge 10: `../../.claude/docs/handbook-notes-challenge-10.md`. Nhắc người dùng theo bảng "Khi nào nhắc" khi họ phân tích đề, chọn giải pháp, ước lượng timeline, viết README, review output AI, đặt tên / viết evidence theo domain bảo hiểm.
- Phân rã yêu cầu A/B/C/D, quyết định đã chốt, câu hỏi mở: `../../.claude/docs/challenge-10-requirements.md`. Cập nhật file này khi có quyết định mới.

## Papaya chấm gì (từ README chung)

- Software design: cách chia nhỏ bài toán, cấu trúc giải pháp.
- Attention to detail: edge case, những điều đề không nói rõ.
- Polish: kết quả "đúng cảm giác", không chỉ chạy được.
- Learning velocity: tiếp thu domain bảo hiểm nhanh.
- **One-shot = trượt.** Phải thấy được quá trình chỉ đạo, bắt lỗi AI, đánh đổi.
- **Bắt buộc nộp log hội thoại AI nguyên văn** (export / transcript), thiếu là tự động trượt.
- Có thể bị hỏi lại mọi quyết định khi phỏng vấn: mọi thứ trong bài phải hiểu và giải thích được.

## Yêu cầu cốt lõi của đề (checklist)

- [ ] Dataset 2,000 claim, ~500 member, ~50 provider, năm 2024, có `is_weekend`.
- [ ] Nhúng ~200 claim gian lận (~10%) theo 8 pattern với số lượng đúng đề, có ground-truth label.
- [ ] 8 rule: duplicate, rapid re-submission, upcoding, unbundling (>= 5 bundle), phantom billing, weekend anomaly, diagnosis-procedure mismatch (>= 10 cặp hợp lệ), amount clustering.
- [ ] Output mỗi claim: `claim_id`, `risk_score` 0-100, `flags[]` gồm `rule`, `severity`, `evidence` cụ thể (có số liệu).
- [ ] Severity weight 1-5 cấu hình được; score = weighted sum chuẩn hóa 0-100; danh sách xếp hạng theo score.
- [ ] Giải thích lý do chọn trọng số.
- [ ] Metrics: precision, recall; mục tiêu recall >= 70%, FPR <= 20%.
- [ ] >= 15 unit test (từng rule + edge case).
- [ ] Xử lý 2,000 claim < 30 giây.
- [ ] Ước lượng và báo timeline.
- [ ] Nộp: dataset, scored output, metrics report, writeup (`README.md`), log hội thoại AI (`conversations/`).

## Quyết định cần chốt (cập nhật khi đã chốt)

| Chủ đề | Trạng thái |
|---|---|
| Ngôn ngữ / stack | Chưa chốt |
| Cách đo FPR (trên tập claim hợp lệ hay trên tập bị flag) | Chưa chốt |
| Một claim có được dính nhiều pattern gian lận không | Chưa chốt |
| Cách chuẩn hóa score về 0-100 | Chưa chốt |
| Ngưỡng score để tính "dự đoán là fraud" khi đo metrics | Chưa chốt |
| Bộ mã ICD-10 / procedure / bundle / cặp diagnosis-procedure | Chưa chốt |
| Cách lưu và xuất log hội thoại AI | Chat: `/noteconversaion-clacowo-bunhy` (đang cân nhắc); Code: export. Lưu vào `conversations/` |

## Quy ước cho agent

- Làm theo phase: phân tích đề -> so sánh >= 2 giải pháp -> plan -> code -> test -> review -> writeup. Không nhảy thẳng vào code.
- Người dùng review 100% plan / assumption trước khi code.
- Không one-shot: chia việc nhỏ, mỗi bước có kiểm chứng.
- Ghi lại mọi assumption về chỗ đề mơ hồ vào bảng "Quyết định cần chốt" và vào writeup.
- Code ưu tiên dễ đọc, tránh trừu tượng thừa; không thêm tính năng ngoài đề.

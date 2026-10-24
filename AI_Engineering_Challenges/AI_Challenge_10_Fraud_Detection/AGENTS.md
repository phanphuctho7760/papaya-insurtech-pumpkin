# AGENTS.md - AI Engineering Challenges

Thư mục này tập trung cho **AI Challenge 10 - Fraud Detection Scoring Engine** (Advanced, 3 điểm, ước lượng của đề 4-6 giờ).
Code đặt trong thư mục này (`AI_Challenge_10_Fraud_Detection/`).

## Cấu trúc dự kiến của `AI_Challenge_10_Fraud_Detection/`

```
AI_Challenge_10_Fraud_Detection/
|-- README.md          # writeup nộp bài: cách tiếp cận, quyết định, trọng số, metrics, Agent Workflow
|-- AGENTS.md          # hướng dẫn agent cấp project
|-- docs/
|   |-- business-rule/  # business của 8 rule, catalog
|   |-- requirements/   # original-brief.md (đề gốc), phân rã yêu cầu + quyết định đã chốt
|   |-- handbook-notes.md
|   |-- backlog/        # ticket A/B/C/D: việc gì, vì sao, tiêu chí xong
|   |-- experiences/    # bẫy / rủi ro khi implement
|   `-- decisions/      # thiết kế kỹ thuật: công nghệ, cấu trúc, định dạng dữ liệu
|-- src/               # source code, chi tiết: docs/decisions/tech-and-structure.md
|-- tests/             # pytest
|-- data/              # claims.csv, ground_truth.csv
|-- output/            # scored_output.json, metrics_report.md
`-- conversations/     # log hội thoại AI nguyên văn (bắt buộc nộp)
    `-- README.md      # mục lục log: phiên nào, công cụ nào, nội dung chính
```

## Lưu log hội thoại AI

- Claude Chat: đang cân nhắc lưu bằng skill `/noteconversaion-clacowo-bunhy`.
- Claude Code: lưu bằng tính năng export.
- Mọi log đặt trong `conversations/`, giữ nguyên văn, không chỉnh sửa lại nội dung. `conversations/README.md` liệt kê từng file log.
- Agent nhắc người dùng lưu log khi kết thúc mỗi phiên làm việc quan trọng.

## Tài liệu phải đọc

- Đề gốc (Challenge 10 + quy định chung, nguyên văn): `docs/requirements/original-brief.md`
- Ghi chú Handbook cho Challenge 10: `docs/handbook-notes.md`. Nhắc người dùng theo bảng "Khi nào nhắc" khi họ phân tích đề, chọn giải pháp, ước lượng timeline, viết README, review output AI, đặt tên / viết evidence theo domain bảo hiểm.
- Phân rã yêu cầu A/B/C/D, quyết định đã chốt, câu hỏi mở: `docs/requirements/challenge-10-requirements.md`. Cập nhật file này khi có quyết định mới.

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

## Quyết định

Quyết định đã chốt và câu hỏi mở: `docs/requirements/challenge-10-requirements.md` (nguồn duy nhất, không chép lại ở đây).

## Quy ước cho agent

- Làm theo phase: phân tích đề -> so sánh >= 2 giải pháp -> plan -> code -> test -> review -> writeup. Không nhảy thẳng vào code.
- Người dùng review 100% plan / assumption trước khi code.
- Không one-shot: chia việc nhỏ, mỗi bước có kiểm chứng.
- Ghi lại mọi assumption về chỗ đề mơ hồ vào `docs/requirements/challenge-10-requirements.md` và vào writeup.
- Code ưu tiên dễ đọc, tránh trừu tượng thừa; không thêm tính năng ngoài đề.

## Quy ước tài liệu (theo skill `pjdoc-mgmt-claco-bunhy`)

- Việc cần làm: ticket ở `docs/backlog/{idea,todo,done}/NN-<slug>.md`; plan thực thi cùng số ở `.claude/docs/plans/{todo,done}/NN-<slug>.md` (root repo). Trạng thái nằm ở ticket, chi tiết thực thi nằm ở plan.
- Quyết định kỹ thuật **mới** ghi theo định dạng ADR của skill: `docs/decisions/ADR-NNN-<title>.md`. Các file hiện có trong `docs/decisions/` giữ nguyên định dạng.
- Bẫy / rủi ro đã gặp hoặc ước lượng: `docs/experiences/`.
- Không dùng changelog: lịch sử commit và log hội thoại là đủ.
- Ngôn ngữ: doc dưới `docs/`, `.claude/docs/` và `AGENTS.md` viết tiếng Việt; code, comment, commit message viết tiếng Anh.
- Trước mỗi commit chạy `/pjdoc-mgmt-claco-bunhy pre-commit`. Khi viết code Python áp dụng `/pyfriend-claco-bunhy`.

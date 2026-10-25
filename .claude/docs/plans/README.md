# Plans

**Đọc khi:** bắt đầu thực thi một ticket trong `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/docs/backlog/`.
**Không chứa:** trạng thái ticket (nằm ở ticket), business rule.

- Plan dùng chung số với ticket. `todo/` = đang chờ / đang làm, `done/` = xong; chuyển bằng `git mv`, giữ nguyên số.
- Đường dẫn trong plan (`docs/...`, `src/...`) tính từ thư mục project `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/`.

## DONE

- [01 - A: Sinh dataset](done/01-dataset-generator.md) - ticket #01, xong 2026-10-24. Generator 2,000 claim + 200 fraud theo 8 pattern, CLI `generate`, kiểm cấu trúc tự động.
- [02 - B: Engine 8 rule + scoring](done/02-rule-engine.md) - ticket #02, xong 2026-10-25. Load input + weights, 8 rule có evidence, scoring 0-100 + xếp hạng, CLI `score`, test hệ thống S1-S9.
- [03 - C: Unit test, metrics, đo thời gian](done/03-tests-and-metrics.md) - ticket #03, xong 2026-10-25. 19 test business, module + CLI `metrics`, `output/metrics_report.md` (recall 100%, FPR 2.6%, 0.018 s), test tích hợp trên dataset thật.

## TODO

Trống. Ticket chưa có plan: xem `docs/backlog/README.md`.

# 01 - A: Sinh dataset

**Status:** todo
**Type:** feature
**Priority:** 1
**Effort:** M (kế hoạch 1.5h)
**Plan:** `.claude/docs/plans/todo/01-dataset-generator.md` (root repo)
**Related:** #02, #03

## What

Generator Python sinh `data/claims.csv` (2,000 claim, 10 cột của đề) và `data/ground_truth.csv` (200 claim fraud theo 8 pattern), seed cố định.

## Why / value

B và C cần dataset để chạy rule và đo metrics. Dataset sai số lượng hoặc lộ nhãn thì metrics không có ý nghĩa.

## Acceptance criteria

- Chạy 1 lệnh sinh 2 file CSV đúng `docs/decisions/dataset-format.md`; chạy lại cùng seed ra file giống hệt.
- Số claim fraud theo pattern đúng `docs/business-rule/fraud-injection.md` (tổng 200).
- Kiểm cấu trúc tự động pass: mỗi mã >= 30 claim 1 mã, mỗi bệnh viện weekday-only >= 60 claim, không có nhóm duplicate ngoài 15 cặp, chỉ 1 provider-day > 30 claim.
- Ghi số đo thật vào `docs/experiences/dataset-generation-pitfalls.md` (phần đo được ngay sau generate).

## Notes

Kiểm chéo rule với nhãn thuộc #03.

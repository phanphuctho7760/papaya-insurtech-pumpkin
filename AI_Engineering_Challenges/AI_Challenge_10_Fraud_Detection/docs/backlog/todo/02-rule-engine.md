# 02 - B: Engine 8 rule + scoring

**Status:** todo
**Type:** feature
**Priority:** 2
**Effort:** M (kế hoạch 1.75h)
**Plan:** `.claude/docs/plans/todo/02-rule-engine.md` (repo root)
**Related:** #01, #03

## What

Engine đọc `claims.csv`, chạy 8 rule, sinh evidence, tính `risk_score` 0-100, xuất `output/scored_output.json` xếp hạng giảm dần.

## Why / value

Phần chính của đề: "All 8 rules implemented correctly", evidence cụ thể, trọng số cấu hình được.

## Acceptance criteria

- 8 rule đúng `docs/business-rule/detection-rules.md`; evidence đúng `evidence.md`.
- Trọng số đọc từ `src/config/weights.json`, kiểm 1-5 khi load.
- Score đúng `scoring.md` (ví dụ 4 + 2 => 78); output toàn bộ claim, xếp hạng giảm dần.
- Engine không đọc `ground_truth.csv`.

## Notes

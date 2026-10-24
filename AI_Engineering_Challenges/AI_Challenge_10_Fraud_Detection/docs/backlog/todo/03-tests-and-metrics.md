# 03 - C: Unit test, metrics, đo thời gian

**Status:** todo
**Type:** feature
**Priority:** 3
**Effort:** M (kế hoạch 1.25h)
**Plan:** none yet
**Related:** #01, #02

## What

19 unit test, test tích hợp trên dataset thật, metrics report 4 phần, đo thời gian xử lý 2,000 claim.

## Why / value

Đề chấm >= 15 unit test, recall >= 70% với FPR <= 20%, và < 30 giây.

## Acceptance criteria

- 19 test trong `docs/business-rule/test-cases.md` pass bằng pytest.
- Test tích hợp: mỗi claim fraud dính rule của pattern mình; dính thêm rule ngoài ngoại lệ đã ghi thì báo rõ.
- `output/metrics_report.md` đủ 4 phần theo `metrics.md`, có thời gian chạy.
- Điền "Số đo thật" trong `docs/experiences/dataset-generation-pitfalls.md`.

## Notes

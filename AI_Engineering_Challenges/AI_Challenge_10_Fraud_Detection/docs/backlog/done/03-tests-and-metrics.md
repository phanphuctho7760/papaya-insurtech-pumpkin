# 03 - C: Unit tests, metrics, runtime

**Status:** done
**Type:** feature
**Priority:** 3
**Effort:** M (planned 1.25h)
**Plan:** `.claude/docs/plans/done/03-tests-and-metrics.md` (repo root)
**Related:** #01, #02

## What

19 unit tests, an integration test on the real dataset, a 4-part metrics report, and the runtime of scoring 2,000 claims.

## Why / value

The brief grades >= 15 unit tests, recall >= 70% with FPR <= 20%, and < 30 seconds.

## Acceptance criteria

- The 19 tests in `docs/business-rule/test-cases.md` pass under pytest.
- Integration test: every fraud claim triggers the rule of its own pattern; any extra rule outside the recorded exception is reported clearly.
- `output/metrics_report.md` has the 4 parts of `metrics.md` and the runtime.
- The engine re-check is recorded in `docs/experiences/dataset-generation-pitfalls.md` (items with a "Real measurement").

## Notes

Known test gap, accepted (2026-10-25): no test catches upcoding's `>` (amount > mean + 2 SD, `src/rules/upcoding.py`) being changed to `>=`. Catching it needs a claim whose amount equals the threshold exactly, and the threshold is a float computed from the SD, so such a fixture is hard to build and fragile. The `>` choice follows the brief ("> 2 standard deviations") and is recorded in `docs/business-rule/upcoding.md`. Every other boundary of the 8 rules is pinned by a test (mutation-checked in plan 03).

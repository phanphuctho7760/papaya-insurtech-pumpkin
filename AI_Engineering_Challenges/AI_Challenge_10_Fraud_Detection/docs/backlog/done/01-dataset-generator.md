# 01 - A: Generate the dataset

**Status:** done
**Type:** feature
**Priority:** 1
**Effort:** M (planned 1.5h)
**Plan:** `.claude/docs/plans/done/01-dataset-generator.md` (repo root)
**Related:** #02, #03

## What

A Python generator that writes `data/claims.csv` (2,000 claims, the 10 columns of the brief) and `data/ground_truth.csv` (200 fraudulent claims across 8 patterns), with a fixed seed.

## Why / value

B and C need a dataset to run the rules and measure metrics. A dataset with wrong counts or leaked labels makes the metrics meaningless.

## Acceptance criteria

- One command writes both CSV files per `docs/decisions/dataset-format.md`; re-running with the same seed produces identical files.
- Fraudulent claims per pattern match `docs/business-rule/fraud-injection.md` (200 in total).
- Automatic structural checks pass: every code has >= 30 single-code claims, every weekday-only hospital has >= 60 claims, no duplicate group besides the 15 injected pairs, exactly 1 provider-day with > 30 claims.
- Real measurements are recorded in `docs/experiences/dataset-generation-pitfalls.md` (the part measurable right after generation).

## Notes

Cross-checking rules against labels belongs to #03.

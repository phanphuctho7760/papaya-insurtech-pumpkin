# 02 - B: 8-rule engine + scoring

**Status:** done
**Type:** feature
**Priority:** 2
**Effort:** M (planned 1.75h)
**Plan:** `.claude/docs/plans/done/02-rule-engine.md` (repo root)
**Related:** #01, #03

## What

The engine reads `claims.csv`, runs the 8 rules, builds the evidence, computes a 0-100 `risk_score`, and writes `output/scored_output.json` ranked in descending order.

## Why / value

The core of the brief: "All 8 rules implemented correctly", concrete evidence, configurable weights.

## Acceptance criteria

- The 8 rules match `docs/business-rule/detection-rules.md`; evidence matches `evidence.md`.
- Weights are read from `src/config/weights.json` and checked to be 1-5 on load.
- The score matches `scoring.md` (e.g. 4 + 2 => 78); the output covers every claim, ranked in descending order.
- The engine never reads `ground_truth.csv`.

## Notes

# ADR-005: The metrics command re-runs the score pipeline instead of reading scored_output.json

## Status

Accepted (2026-10-25)

## Context

The brief asks for precision / recall against the ground truth and for scoring 2,000 claims in under 30 seconds; the metrics report must carry both (ticket #03, C2-C4). `output/scored_output.json` holds exactly the brief's 3 fields per claim (`claim_id`, `risk_score`, `flags`, see `docs/business-rule/scoring.md`), so it carries no runtime. A metrics step that only reads that file has no real runtime to report.

## Decision

`uv run python src/cli.py metrics` runs the whole score pipeline itself, then evaluates:

1. load catalog, weights, `claims.csv` -> 8 rules -> score -> write `output/scored_output.json`, timed with `time.perf_counter()` (one in-process run; Python startup excluded). `score` and `metrics` share this code (`run_score` in `src/cli.py`), so `score` behaves exactly as before.
2. read `data/ground_truth.csv` (only `src/metrics/` reads it; the engine never does) and stop with exit 1, listing every problem, if it is malformed or its `claim_id` set differs from the scored claims (same stance as ADR-002);
3. write `output/metrics_report.md`: header (dataset, seed, weights, runtime) + the 4 parts of `docs/business-rule/metrics.md` + the fraud claims flagged by an extra rule, split into the expected phantom-day exception (derived from `data/generation_summary.json`) and unexpected ones.

## Rationale

- The runtime in the report is a real measurement of the same run whose scores are evaluated, not a number copied from another command.
- The scored output keeps the brief's exact format; nothing is added to it for the metrics' sake.
- One command reproduces both submission artifacts (`scored_output.json`, `metrics_report.md`) from `data/`.

## Consequences

- `metrics` overwrites `output/scored_output.json`; with the same inputs the file is byte-identical.
- If the ground truth is invalid, `scored_output.json` is already written when `metrics` exits 1. Accepted: scoring does not depend on the ground truth.
- The report is deterministic except its runtime line.
- `tests/test_integration_dataset.py` asserts the < 30 s limit on the same load -> rules -> score span, independently of the CLI.

## Alternatives Considered

- **`metrics` reads an existing `scored_output.json`:** rejected; no runtime is available, and the report could evaluate a stale file scored with other weights.
- **Add the runtime (or a rank / total-weight field) to `scored_output.json`:** rejected; the output must keep exactly the brief's 3 fields (plan #02, decision 7).
- **`score` writes the runtime to a side file that `metrics` reads:** rejected; an extra file format and a second place where the two artifacts can drift apart.

## References

- Ticket #03, plan `.claude/docs/plans/done/03-tests-and-metrics.md` (decisions 2, 3, 6)
- `docs/business-rule/metrics.md`, `docs/requirements/challenge-10-requirements.md` (C2-C4)
- ADR-002

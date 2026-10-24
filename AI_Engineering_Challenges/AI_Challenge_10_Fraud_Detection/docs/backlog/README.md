# Backlog

**Read when:** you need to know which Challenge 10 work is in progress, in what order, and what "done" means.
**Does not contain:** business rules (see `../business-rule/`), technical decisions (see `../decisions/`), execution detail (see `.claude/docs/plans/` at the repo root).

- The folder is the status: `idea/` (not committed to), `todo/` (committed: `todo` or `doing`), `done/` (`done` or `rejected`). Change status across folders with `git mv`.
- A ticket shares its number with the plan for the same work; a new number = the highest existing number + 1, never reused.
- Refer to tickets by number (`#01`), not by path.

| # | Ticket | Type | Status | Priority |
|---|---|---|---|---|
| 01 | [A - Generate the dataset](done/01-dataset-generator.md) | feature | done | 1 |
| 02 | [B - 8-rule engine + scoring](todo/02-rule-engine.md) | feature | doing | 2 |
| 03 | [C - Unit tests, metrics, runtime](todo/03-tests-and-metrics.md) | feature | todo | 3 |
| 04 | [D - Writeup and submission](todo/04-writeup-and-submission.md) | chore | todo | 4 |

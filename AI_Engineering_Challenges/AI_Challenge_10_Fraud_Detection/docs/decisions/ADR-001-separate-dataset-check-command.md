# ADR-001: Dataset checks are a separate `check` command, not part of `generate`

## Status

Accepted (2026-10-24)

## Context

The execution plan for ticket #01 said the structural checks would "run at the end of `generate` and stop on failure". The first implementation did exactly that: `cmd_generate` wrote the files, then called `check_dataset` and exited with code 1 on any problem.

That coupled two different jobs in one command. Checking an existing dataset (after a manual edit, after pulling the repository, or from the integration tests of #03) meant regenerating it first, and `generate` both produced the files and judged them.

## Decision

Generation and checking are two commands:

- `cli.py generate [--seed] [--out]` builds and writes the files, nothing else.
- `cli.py check [--data]` reads a dataset directory and runs the structural checks; exit code 1 on failure.

Each CLI function does one thing; `check_dataset` stays a pure function of a directory plus the catalog.

## Rationale

- One function, one job: generating is a write, checking is a read-only verification.
- `check` works on any directory, including one that was not just generated, so it is reusable by #03 and by a reviewer who only has the committed `data/`.
- The checks read the files back from disk in either design, so splitting loses no coverage.

## Consequences

- A user must run `generate` then `check`; `generate` prints a reminder to run `check`.
- `generate` can write files that would fail `check`. Acceptable: nothing consumes the files automatically, and the committed `data/` is verified with `check` before commit.
- `README.md` documents both commands; the check list is in `dataset-checks.md`.

## Alternatives Considered

- **Run the checks at the end of `generate` (the original plan):** rejected; mixes writing and verifying, and cannot check an existing dataset without regenerating it.
- **`generate --check` flag:** rejected; still two jobs behind one command, and it adds an option without adding a capability over running `check` afterwards.
- **Write to a temporary directory, check, then move into place:** rejected; protects against half-valid output that nothing reads automatically, at the cost of extra file handling.

## References

- Ticket #01, plan `.claude/docs/plans/done/01-dataset-generator.md` (Phase 5)
- `dataset-checks.md`

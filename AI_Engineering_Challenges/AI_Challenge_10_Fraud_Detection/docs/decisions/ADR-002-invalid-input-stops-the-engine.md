# ADR-002: Invalid claims input stops the engine instead of skipping rows

## Status

Accepted (2026-10-24)

## Context

The engine (ticket #02) reads `data/claims.csv`. Several rules depend on every value being well-formed and known to the catalog: the mismatch rule looks a diagnosis up in `valid_pairs`, the upcoding rule groups amounts by code, the weekend rule reads `surgical` from the catalog. An unknown code or a malformed amount does not crash these rules; it makes them silently wrong (an unknown diagnosis has no valid pairs, so every claim with it is a "mismatch"; a skipped row shifts a code's mean and SD).

## Decision

`src/claims.py` validates the whole file before any rule runs:

- exactly the 10 columns of `dataset-format.md`, in order;
- unique `claim_id`;
- `claim_date` is a valid `YYYY-MM-DD` date;
- `submitted_amount` is a positive integer;
- `is_weekend` is `0` or `1`;
- every diagnosis and procedure / bundle code exists in the catalog.

Any problem => the CLI prints the full list of problems to stderr and exits 1. No row is skipped.

## Rationale

- A fraud score computed on partly invalid input looks trustworthy and is not; a hard stop is the only outcome that cannot be misread.
- Listing every problem in one run (instead of stopping at the first) lets the input be fixed in one pass, the same pattern as `CatalogError` and the `check` command (ADR-001).

## Consequences

- One bad row blocks scoring of the whole batch. Acceptable for a batch tool whose input is generated and checked (`check`) in this repository.
- System test S4 (plan #02) covers the loader errors.

## Alternatives Considered

- **Skip invalid rows with a warning:** rejected; skipped rows change the statistics other claims are compared against (upcoding mean / SD, provider weekend ratio, provider-day counts), and a warning in a log is easy to miss.
- **Score invalid rows anyway (no validation):** rejected; unknown codes would produce false mismatch flags with plausible-looking evidence.
- **Stop at the first problem:** rejected; forces one fix-and-rerun cycle per problem.

## References

- Ticket #02, plan `.claude/docs/plans/todo/02-rule-engine.md` (decision 5)
- `dataset-format.md`, ADR-001

# ADR-003: Only rule weights are configurable; rule thresholds are code constants

## Status

Accepted (2026-10-24)

## Context

The brief asks for "a configurable severity weight (1-5)" per rule. Each rule also has thresholds: 7 days (rapid), 2 SD and a 10-claim minimum (upcoding), more than 30 claims per day (phantom), < 5% weekend volume (weekend), the 50,000 VND threshold and the 47,500-49,999 band (clustering). These could live in config next to the weights, or in the code.

## Decision

- `src/config/weights.json` holds the 8 weights and nothing else; it is validated on load (8 known rule names, integers 1-5).
- Thresholds are named constants at the top of each rule file in `src/rules/`. Evidence text reads the same constants, so a threshold is never typed into a sentence by hand.

## Rationale

- Matches the brief exactly: weights are a tuning knob for reviewers; thresholds are part of each rule's definition and are quoted from the brief.
- Thresholds are coupled to the dataset design (e.g. the >= 60-claim weekday-only hospitals exist because of the 5% threshold, see `../business-rule/weekday-only-providers.md`). Making them configurable invites a change that silently breaks that design.
- A constant next to the rule that uses it is easier to read and to explain line by line in the interview than a lookup into a config file.

## Consequences

- Changing a threshold needs a code change, a test update (the business tests in `../business-rule/test-cases.md` assert the boundaries) and a review. Intended.
- The weights file stays small enough to validate strictly.

## Alternatives Considered

- **Thresholds in a `rules.json` config:** rejected; not asked by the brief, adds validation code for values that should not change, and decouples a rule's number from its definition.
- **Thresholds hard-coded in the evidence strings:** rejected; the evidence and the rule could drift apart.

## References

- Ticket #02, plan `.claude/docs/plans/todo/02-rule-engine.md` (decision 6)
- `../business-rule/scoring-weights.md`, `../business-rule/detection-rules.md`

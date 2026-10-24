# Weekday-only providers

Supports the "weekend surgical anomaly" pattern (rule 6). Terms (weekday-only provider, weekend anomaly, surgical): see `glossary.md`.

## Source in the brief

- Dataset: "20 weekend surgical anomalies (surgical procedures on weekends from providers who never operate on weekends)".
- Rule: "surgical procedures on weekends from providers with < 5% historical weekend volume".

## Data generation

- The generator picks **10 hospitals** (the provider type that does surgery) as weekday-only.
- Legitimate claims of this group fall only on Monday - Friday.
- The 20 weekend surgical fraud claims are placed on Saturday / Sunday, 2 claims for each weekday-only provider.
- Surgical procedures: P-3001, P-3002, P-3003, B-3101, B-3102 (see `catalog.md`).
- The list of weekday-only providers is recorded after generation.

## Weekend ratio (settled)

- Rule 6 computes the weekend ratio over **all claims** of the provider, as the brief words it.
- The generator gives each weekday-only hospital **>= 60 claims** (a random 62-70 legitimate claims, with no extra ones, so this group does not become the 10 largest hospitals). 2 weekend fraud claims => 2/60 = 3.3% < 5% => the rule catches them.
- Reason: with ~40 claims per provider, 2/40 = 5% is not < 5% => missed.
- The emergency concept is out of scope.

## What counts as a surgical weekend claim (settled 2026-10-24)

- **Surgical:** at least 1 code in `procedure_codes` is a procedure or bundle with `surgical = true` in the catalog.
- **Weekend:** taken from the `is_weekend` column of the input; the day name in the evidence (`Saturday`) is derived from `claim_date`.

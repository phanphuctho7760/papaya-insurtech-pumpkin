# ADR-004: All 20 hospitals get the same claim volume; fraud providers follow legit volume

## Status

Accepted (2026-10-24)

## Context

Each weekday-only hospital needs >= 60 claims, so its 2 weekend fraud claims stay below the 5% weekend-volume threshold (`../business-rule/weekday-only-providers.md`). The first generator gave only these 10 hospitals a pre-assigned 62-70 claims. The review of #01 measured 67-78 claims for them versus 33-49 for the other 10 hospitals: sorting hospitals by volume revealed the group that holds the 20 `weekend_anomaly` claims.

## Decision

- 150 legitimate claims move from DENTAL to OUTPATIENT codes: P-4001, P-4002, P-4003 and B-4101 go down to 60 each (P-4004 stays 60); P-1001 240, P-1002 160, P-1004 110, P-1005 100, P-1006 100, B-1001 130. Total stays 1,800.
- All 20 hospitals are pre-assigned a random 58-62 OUTPATIENT / INPATIENT claims (`HOSPITAL_PREASSIGNED_RANGE` in `src/generator/legit.py`); the remaining claims go to any eligible provider, weekday-only hospitals included. 58 legitimate + 2 weekend frauds keeps every weekday-only hospital at >= 60.
- Fraud claims draw their provider weighted by legitimate volume: the provider of a random legitimate claim of the same claim type (`_Injector._provider` in `src/generator/fraud.py`).

## Rationale

- Weekday-only and regular hospitals now overlap: 70-86 versus 68-79 claims (seed 2024).
- The pre-assignment alone made clinics tiny, and a uniform fraud provider draw then gave clinics a ~24% fraud rate versus ~9% for hospitals, a new label leak. Drawing by legitimate volume brings every provider type close to the 10% base rate (hospital 10%, dental 10%, clinic 3-12% across seeds).
- Moving DENTAL claims keeps every code at >= 60 legitimate claims except P-1003, P-3002 and P-3010, so the upcoding spread (at most 2 per code, codes with >= 60 claims) still holds.

## Consequences

- Known limitation, accepted by the user: the 20 clinics get only ~1-15 claims each per year, which looks thin next to hospitals (~70-85) and dental providers (20-46). Not a label leak.
- Dental volume per provider dropped (300 legitimate DENTAL claims for 10 providers).
- Every natural-FP measurement changed with the new random sequence; re-measured in `../experiences/dataset-generation-pitfalls.md`.

## Alternatives Considered

- **Keep the code, document the leak:** rejected; a reviewer sorting hospitals by volume finds the weekday-only group at once.
- **Pre-assign all hospitals without moving DENTAL claims:** rejected; with 1,350 OUTPATIENT / INPATIENT claims, clinics would have been left with ~6 claims each.
- **Lower the weekday-only floor to 50 (pre-assign 48-52) so clinics get ~15-20 claims:** rejected; changes a settled business-rule number and narrows the margin under 5% (2/50 = 4%).
- **Cut clinics to 10 in `providers.json` and add 10 dental providers:** rejected; clinics would grow to ~20 claims but dental providers would shrink to ~15.
- **Give the leftover OUTPATIENT claims to clinics only:** rejected with the above; clinics only reach ~10 claims.

## References

- Ticket #01 (review fixes after closing)
- `../business-rule/weekday-only-providers.md`, `../business-rule/fraud-injection.md`, `../business-rule/upcoding.md`
- `../experiences/dataset-generation-pitfalls.md` items 5 and 6

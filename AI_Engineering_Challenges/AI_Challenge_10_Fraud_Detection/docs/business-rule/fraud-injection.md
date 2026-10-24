# Injecting fraud into the dataset (A3)

How the 8 fraud patterns are generated. Each rule's own definition is in the file of the same folder.

## General principles

- Counted per **claim** (option C): **200 fraud claims** out of 2,000 (10%), matching the brief's "~200 fraudulent claims (~10%)".
- Each fraud claim carries **exactly 1 pattern** in the ground truth (a deliberate limit; in reality one claim can have several).
- Legitimate claims may trigger a rule on their own (natural FPs); they are counted and reported in the metrics.
- Fixed seed, so the dataset is reproducible.
- Amount of fraud claims in patterns not based on amount (duplicate, rapid, unbundling, phantom, weekend, mismatch): the factor is re-drawn until it falls inside [0.85, 1.15] (about +-1 SD, truncated rather than clamped), so they do not trigger upcoding or clustering by accident. Clamping was rejected: it piles amounts onto exactly `price x 0.85` / `price x 1.15`, which leaks the label. Legitimate claims are not truncated (natural FPs kept on purpose).
- Every amount (legitimate and fraud) is rounded to 100 VND; clustering claims take 47,500-49,999. Legitimate and fraud claims are never rounded differently: a different format would leak the label.
- Fraud claims pick their provider weighted by legitimate volume (the provider of a random legitimate claim of the same claim type), so no provider type gets an outlier fraud rate.
- After generation, the generator (A) only checks structure and label placement: claim counts per pattern, >= 30 single-code claims per code, >= 60 claims per weekday-only hospital, no duplicate group besides the 15 injected pairs, no other provider above 30 claims per day, and each label sitting on the structure it was injected into (`../decisions/dataset-checks.md`). The generator does not copy the rule logic.
- Cross-check with the engine in C (integration test running the engine on the real dataset): each fraud claim triggers only the rule of its own pattern. Known exceptions: the 6 claims on the phantom day (also trigger phantom); a duplicate pair also meets the rapid re-submission condition, but the rapid rule skips pairs sharing the duplicate unique key (see `duplicate-and-rapid-resubmission.md`), so it is not flagged twice.

## Counts and generation

| Pattern | Claims | How |
|---|---|---|
| Duplicate | 30 (15 pairs) | 2 claims with the same member + provider + date + diagnosis. The data has passed input validation, so there is no double-submit => 2 independent claims, **both labelled fraud**. |
| Rapid re-submission | 30 (15 pairs) | 2 claims with the same member + diagnosis, **1-7 days apart** (never the same day, so they do not become a duplicate). Both labelled fraud. |
| Upcoding | 30 | Amount = standard price x 1.6-2.5. See `upcoding.md`. |
| Unbundling | 25 | `procedure_codes` = all components of 1 bundle. See `bundling.md`. |
| Phantom billing | 25 | 1 provider-day with **31 claims**: 25 labelled phantom + 3 labelled upcoding + 3 labelled mismatch (counted in those 2 patterns). A weekday, at a hospital outside the weekday-only group. |
| Weekend surgical anomaly | 20 | Surgical procedure on Saturday / Sunday at the 10 weekday-only hospitals, 2 claims per hospital. See `weekday-only-providers.md`. |
| Diagnosis-procedure mismatch | 20 | Procedure outside the diagnosis's valid list. See `diagnosis-procedure-mismatch.md`. |
| Amount clustering | 20 | P-1003, amount 47,500-49,999. See `amount-clustering.md`. |
| **Total** | **200** | |

Constraint on the 6 extra claims of the phantom day: only patterns that can be judged on a single claim (upcoding, mismatch); not duplicate / rapid (they need a pair) nor weekend (the phantom day is a weekday).

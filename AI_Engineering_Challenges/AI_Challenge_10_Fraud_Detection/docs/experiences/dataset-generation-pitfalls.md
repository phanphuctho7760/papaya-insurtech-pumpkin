# Dataset generation pitfalls that skew metrics or leak labels

**Found:** 2026-10-24 (estimated before coding, then measured)
**Scope:** generator (A) and how metrics are read (C): amount distribution, code choice for fraud, `claim_id` assignment, provider volume, natural FPs.
**Artifact at time of discovery:** `src/generator/`; cross-checked against the rules in #03
**Status:** measured on the full 2,000-claim dataset (seed 2024) with a rough script following each rule's definition. Last re-measured 2026-10-24 after the #01 review fixes (amount truncation, provider volume). Re-checked by the engine in #03.

Each item: prediction -> how generation handles it -> real measurement.

## 1. Natural FPs of upcoding

- **Prediction:** legit amount = standard price x log-normal with 15% spread => about 2.5% of legit claims exceed mean + 2 SD on their own, i.e. about 40-45 of the 1,800 legit claims.
- **Impact:** FPR stays far below 20%, but precision drops.
- **Handling:** accepted (the "natural FPs are allowed" decision); reported in section 3 of the metrics report and in the writeup.
- **Lesson:** the first rough measurement on clean data gave 57 claims (3.2%), above the prediction. The log-normal is right-skewed, so its upper tail is heavier than a normal one and more than 2.5% exceed mean + 2 SD.
- **Real measurement (2,000 claims):** 18 legit claims exceed mean + 2 SD (1.0% of 1,800), because the 30 upcoded claims push each code's SD up. No fraud claim of another pattern exceeds the threshold (their amount factor stays within +-15%).
- **Further lesson:** the natural FPs of a statistical rule must be measured on the dataset with fraud already in it; clean data gives a number that is off in the wrong direction.

## 2. Masking lowers upcoding recall

- **Prediction:** mean / SD include the upcoded claims => if many upcoded claims sit on one code, the mean + 2 SD threshold rises and some of them stay below it.
- **Handling:** spread the 30 upcoded claims over many codes (at most 2 per code, only codes with >= 60 legit claims). P-1003 is never upcoded because it is reserved for amount clustering.
- **If upcoding recall is still low:** switch to leave-one-out (see `../business-rule/upcoding.md`).
- **Real measurement:** 30/30 upcoded claims exceed mean + 2 SD. Masking happens (it lowers the natural FPs, item 1) but misses no upcoded claim => leave-one-out not needed yet.

## 3. Natural FPs of rapid re-submission

- **Prediction:** 500 members with about 3-4 claims each => some random pairs share a diagnosis within <= 7 days, about 10-20 legit claims flagged.
- **Handling:** accepted and reported. If the count is far above the estimate, revisit how one member's visit dates are spread.
- **Real measurement (2,000 claims):** 24 legit claims sit in a pair with the same member + diagnosis <= 7 days apart (excluding the duplicate key), next to the 30 injected rapid claims. No fraud claim of another pattern is caught (the generator blocks it when placing fraud). Every re-generation changes the random sequence, so this number moves (20-32 seen so far).

## 4. Label leak through `claim_id` order

- **Prediction:** generating legit claims first, injecting fraud after and assigning IDs in generation order puts the fraud claims at the end of the ID range (e.g. `CLM-01801` -> `CLM-02000`). Anyone reading the dataset sees it is fake.
- **Handling:** generate every claim, sort by `claim_date` (secondary order random by seed), then assign `claim_id`.
- **Check:** after generation, look at where the fraud IDs fall. Reviewed for #01: spread evenly over the deciles, the only cluster is the phantom day (31 claims on one date, unavoidable).

## 5. Label leak through amount format and value

- **Met (plan review, before code):** the old plan rounded legit claims to 1,000 and clustering claims to 100 => any amount not divisible by 1,000 (e.g. 48,300) was surely clustering fraud.
- **Handling:** every amount is rounded to 100, legit and fraud alike.
- **Met again (review of #01):** fraud claims of non-amount patterns clamped their amount factor to [0.85, 1.15], so every factor outside piled onto exactly `price x 0.85` or `price x 1.15`. 36 single-code claims had one of those two amounts, all of them fraud.
- **Handling:** the factor is re-drawn until inside [0.85, 1.15] (truncated distribution, no pile-up). Measured after the fix: 0 fraud and 3 legit claims at those two amounts. Remaining, accepted: 100% of non-amount fraud lies within +-15% of the price versus 68% of legit claims; filtering on it lifts the fraud rate only from 10% to ~11%.
- **Lesson:** every format rule (rounding, number type, code spelling) and every value-shaping rule (clamping, bounds) must act the same on legit and fraud claims, or leave no visible trace such as a pile-up.

## 6. Label leak through provider volume

- **Met (Phase 2 dry run):** pre-assigning 62 claims to each weekday-only hospital and still letting them draw more => this group had 84-95 claims, regular hospitals 15-27.
- **Met again (review of #01):** the first fix (62-70 claims for weekday-only hospitals, none extra) still left them at 67-78 versus 33-49 for regular hospitals: the 10 largest hospitals were the weekday-only ones. The fix after that (below) made clinics so small that drawing fraud providers uniformly gave clinics a ~24% fraud rate versus ~9% for hospitals.
- **Handling:**
  - 150 legit claims moved from DENTAL to OUTPATIENT codes, and all 20 hospitals get the same pre-assigned 58-62 OUTPATIENT / INPATIENT claims, weekday-only or not. See `../decisions/ADR-004-equal-volume-for-all-hospitals.md`.
  - Fraud providers are drawn weighted by legit volume (the provider of a random legit claim of the same type).
- **Real measurement (seed 2024):** weekday-only 70-86 claims, regular hospitals 68-79 (phantom hospital excluded). Fraud rate: hospital 163/1,555 (10%), dental 34/334 (10%), clinic 3/111 (3%; varies 3-12% across seeds around the 10% base, sample of ~110).
- **Known limitation, accepted:** clinics get only 3-8 claims each (1-15 across seeds), dental providers 20-46.
- **Lesson:** a constraint placed on one provider group (a minimum claim count, weekdays only) can make that group a statistical outlier, and fixing it can move the outlier elsewhere. After generation, compare the distribution of the special group with the rest, and the fraud rate per provider type.

## 7. Member count close to the check threshold

- **Rough measurement:** uniform member choice for the 1,800 legit claims => 483 distinct members, just above the 480 threshold (expected ~491 with 2,000 claims).
- **Risk:** a new seed or claim count could fail the 480 check.
- **Handling if it fails:** pre-assign one legit claim to every member (the option weighed when the threshold was set); do not lower the threshold.
- **Real measurement (2,000 claims):** 494 members.

## 8. Natural FPs of amount clustering

- **Prediction (`../business-rule/amount-clustering.md`):** about 6% of legit P-1003 claims fall into 47,500-49,999 on their own.
- **Real measurement (2,000 claims):** 4/90 legit P-1003 claims (4.4%) are in the band, next to the 20 injected clustering claims. Small sample (90 claims): earlier generations gave 2/90 and 6/90.

## 9. Fraud claims accidentally caught by another rule

- **Risk:** a randomly placed fraud claim can form a rapid pair with another claim, repeat a unique key, fall on a weekend at a weekday-only hospital, or have an amount above the upcoding threshold / inside the clustering band => the #03 cross-check sees 1 claim caught by 2 rules.
- **Handling:** when placing each fraud claim the generator checks the unique key, the member + diagnosis 7-day window, and weekdays at weekday-only hospitals; non-amount patterns keep their amount factor within +-15%; phantom is generated last so no other claim lands on the 31-claim provider-day.
- **Real measurement (2,000 claims):** `check` passes: only 1 provider-day > 30 (31 claims), exactly 15 duplicate groups, the only weekend claims at weekday-only hospitals are the 20 weekend claims, multi-code claims are only the 25 unbundling claims, and no fraud claim is caught by rapid / upcoding / clustering outside its own pattern. Known exception (the 6 claims on the phantom day): see `../business-rule/fraud-injection.md`.

## Rule derived

- Every accepted natural FP must have a real measurement in the metrics report, not only an estimate.
- The generator must not let the order, format, value shape or provider volume of the data reveal the ground-truth label.

## Related

- `../business-rule/fraud-injection.md`, `../business-rule/upcoding.md`, `../business-rule/metrics.md`
- `../decisions/tech-and-structure.md` (performance B5, timing C4)

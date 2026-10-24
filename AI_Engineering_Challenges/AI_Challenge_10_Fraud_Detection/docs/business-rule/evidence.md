# Evidence (B2)

The brief asks: "Each flag includes specific, actionable evidence (not just 'flagged by rule 3')".

## Principles

- Language: **English** (following the brief's example output).
- Every evidence has 3 parts: the claim's **observed value**, the rule's **comparison value + threshold**, the **related claims** (if any).
- Procedure / diagnosis codes always come with their **English name** (see `catalog.md`, `icd-10.md`) so a claim adjuster can read it without looking codes up.
- Amounts use a thousands separator and the unit VND.
- Numbers in evidence come from the rule's constants and the data, never typed into the text by hand.

## Templates for the 8 rules

| # | Rule | Evidence template |
|---|---|---|
| 1 | Duplicate | `Duplicate of CLM-00456: same member MEM-0042, provider PRV-007, date 2024-03-15, diagnosis K35.8 (Acute appendicitis) - 2 claims share this key` |
| 2 | Rapid re-submission | `Re-submitted 3 days after CLM-00456 (2024-03-12) for the same member MEM-0042 and diagnosis J06.9 (Acute upper respiratory infection) - window: 7 days` |
| 3 | Upcoding | `Submitted amount 900,000 VND for procedure P-4003 (Dental filling) is 8.3 standard deviations above the mean of 410,000 VND (threshold 530,000 VND, based on 95 claims)` |
| 4 | Unbundling | `Procedures P-3001 (Laparoscopic appendectomy) + P-3010 (General anesthesia) billed separately for 21,400,000 VND instead of bundle B-3101 (Appendectomy package) at 19,000,000 VND` |
| 5 | Phantom billing | `Provider PRV-012 submitted 31 claims on 2024-06-18 (threshold: more than 30 per day)` |
| 6 | Weekend anomaly | `Surgical procedure P-3001 (Laparoscopic appendectomy) on Saturday 2024-05-11 at provider PRV-003, whose weekend volume is 3.3% (2 of 60 claims, threshold < 5%)` |
| 7 | Diagnosis-procedure mismatch | `Procedure P-3001 (Laparoscopic appendectomy) is not valid for diagnosis K02.1 (Dental caries); valid procedures: P-4001, P-4002, P-4003` |
| 8 | Amount clustering | `Amount 48,500 VND is 97% of the 50,000 VND auto-approval threshold (band 47,500-49,999)` |

The numbers in the templates are illustrative; real evidence takes its numbers from the dataset.

## Rapid re-submission: wording by time order

A rapid flag is raised on both claims of a pair, so the wording depends on which side the claim is on:

| Case | Evidence template |
|---|---|
| Later claim | `Re-submitted 3 days after CLM-00456 (2024-03-12) ...` (template 2 above) |
| Earlier claim | `Followed 3 days later by CLM-00789 (2024-03-15) for the same member MEM-0042 and diagnosis J06.9 (Acute upper respiratory infection) - window: 7 days` |
| Same day, another provider | `Submitted on the same day as CLM-00456 at another provider PRV-015 for the same member MEM-0042 and diagnosis J06.9 (Acute upper respiratory infection) - window: 7 days` |

A claim related to several claims gets one flag whose evidence lists each related claim (`scoring.md`).

## Edge wording

| Case | Evidence |
|---|---|
| Rapid, several related claims | One clause per related claim (wording above), joined by `; `; the `for the same member ... - window: 7 days` suffix appears once. A 1-day gap reads `1 day`, not `1 days`. |
| Unbundling, several bundles matched | `Billed 4 separate procedures for 520,000 VND: P-1001 (...) + P-1002 (...) + P-1003 (...) instead of bundle B-1001 (...) at X VND; P-1001 (...) + P-1002 (...) + P-1006 (...) instead of bundle B-1002 (...) at Y VND`. One bundle keeps template 4. |
| Percentages near a threshold | Rounded **down** (clustering to a whole percent, weekend ratio to 1 decimal), so a flagged value never displays as the threshold itself: 49,999 VND => `99%`, not `100%`; 10 of 201 => `4.9%`, not `5.0%`. |

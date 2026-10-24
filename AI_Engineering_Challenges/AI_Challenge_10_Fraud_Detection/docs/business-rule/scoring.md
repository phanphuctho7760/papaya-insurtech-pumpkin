# Scoring (B4)

The brief asks: "Composite score = weighted sum of triggered rules, normalized to 0-100" and "Output ranked list of claims by risk score".

## 3 steps per claim

1. **The 8 rules check their conditions** => each rule returns yes / no + evidence (`detection-rules.md`, `evidence.md`). A rule raises **at most 1 flag per claim**; when several claims are related (e.g. a claim re-submitted with 2 others), the single evidence lists all of them. Reason: step 2 sums the weights of the triggered rules, so 2 flags of one rule would count its weight twice.
2. **Weighted scoring**: `total = sum of the weights of the flagged rules` (weights: `scoring-weights.md`).
3. **Scoring scale (0-100)**: `risk_score = round(100 x (1 - e^(-0.25 x total)))`.

Steps 2 and 3 are one formula applied to every claim; case-specific handling lives only in step 1.

## Why a saturating formula (k = 0.25)

| Approach | Formula | Brief's example (4 + 2 = 6) | Duplicate only (5) | Clustering only (2) |
|---|---|---|---|---|
| Divide by total weight | total / 27 x 100 | 22 | 19 | 7 |
| Cap at 10 | min(100, total / 10 x 100) | 60 | 50 | 20 |
| **Saturating** | **100 x (1 - e^(-0.25 x total))** | **78** | **71** | **39** |

- Matches the brief's example output exactly (score 78 for upcoding + clustering): 1 - e^(-1.5) = 0.777.
- Never exceeds 100, however many rules fire.
- A single strong rule still gives a high score (Duplicate => 71), reflecting the real risk.

Reference table: total 2 => 39, 3 => 53, 4 => 63, 5 => 71, 6 => 78, 8 => 86, 10 => 92.

## Ranking and output

- Sorted by `risk_score` descending; on equal scores, more flags first, then by `claim_id`.
- The output covers **all 2,000 claims**; a claim with no flag has `risk_score` = 0 and `flags: []`.
- `output/scored_output.json` is a JSON array in ranked order. Each element has exactly the brief's 3 fields `claim_id`, `risk_score`, `flags`; no extra fields (rank, total weight), so the output matches the brief's example.
- Each flag has `rule`, `severity` (= the rule's weight), `evidence`. Flags inside a claim are sorted by severity descending, then by rule order (`src/rule_names.py`).

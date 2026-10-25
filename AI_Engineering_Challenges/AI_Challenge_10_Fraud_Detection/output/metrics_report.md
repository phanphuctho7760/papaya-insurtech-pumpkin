# Metrics report

- Dataset: 2,000 claims, 200 fraudulent, seed 2024
- Severity weights: duplicate_claim 5, rapid_resubmission 3, upcoding 4, unbundling 3, phantom_billing 4, weekend_anomaly 2, diagnosis_procedure_mismatch 4, amount_clustering 2
- Runtime: Scored 2,000 claims in 0.018 s (load -> rules -> score -> write, measured in-process with time.perf_counter; Python startup excluded)
- Prediction rule: a claim is predicted fraud when risk_score > 0 (at least one flag)

## 1. Overall

| TP | FP | FN | TN | Precision | Recall | FPR |
|---|---|---|---|---|---|---|
| 200 | 46 | 0 | 1,754 | 81.3% | 100.0% | 2.6% |

Recall 100.0% vs target >= 70%: met. FPR 2.6% vs target <= 20%: met. The dataset is synthetic and generated from the same rule definitions the engine applies, so these numbers are an upper bound for real data; see Limitations in README.md.

## 2. By pattern

| Pattern | Fraud claims | Caught (score > 0) | Caught by own rule | Recall |
|---|---|---|---|---|
| duplicate_claim | 30 | 30 | 30 | 100.0% |
| rapid_resubmission | 30 | 30 | 30 | 100.0% |
| upcoding | 30 | 30 | 30 | 100.0% |
| unbundling | 25 | 25 | 25 | 100.0% |
| phantom_billing | 25 | 25 | 25 | 100.0% |
| weekend_anomaly | 20 | 20 | 20 | 100.0% |
| diagnosis_procedure_mismatch | 20 | 20 | 20 | 100.0% |
| amount_clustering | 20 | 20 | 20 | 100.0% |

Every pattern that has fraud claims is fully caught.

## 3. Natural false positives by rule

| Rule | Flags | On fraud claims | On legit claims (FP) |
|---|---|---|---|
| duplicate_claim | 30 | 30 | 0 |
| rapid_resubmission | 54 | 30 | 24 |
| upcoding | 48 | 30 | 18 |
| unbundling | 25 | 25 | 0 |
| phantom_billing | 31 | 31 | 0 |
| weekend_anomaly | 20 | 20 | 0 |
| diagnosis_procedure_mismatch | 20 | 20 | 0 |
| amount_clustering | 24 | 20 | 4 |

46 distinct legit claims were flagged (a claim flagged by 2 rules counts once here and under each rule in the table); legit flags per rule: rapid_resubmission 24, upcoding 18, amount_clustering 4.

## 4. Threshold table

| Predict fraud when score | TP | FP | FN | TN | Recall | FPR |
|---|---|---|---|---|---|---|
| > 0 | 200 | 46 | 0 | 1,754 | 100.0% | 2.6% |
| >= 40 | 160 | 42 | 40 | 1,758 | 80.0% | 2.3% |
| >= 70 | 36 | 0 | 164 | 1,800 | 18.0% | 0.0% |

Raising the threshold from > 0 to >= 70 takes recall from 100.0% to 18.0% and FPR from 2.6% to 0.0%: reviewers who only read high-score claims miss the fraud caught by weaker rules.

## Fraud claims flagged by an extra rule

### Expected (phantom-day exception, see docs/business-rule/fraud-injection.md)

| Claim | Pattern | Extra rules |
|---|---|---|
| CLM-01940 | diagnosis_procedure_mismatch | phantom_billing |
| CLM-01944 | upcoding | phantom_billing |
| CLM-01947 | upcoding | phantom_billing |
| CLM-01949 | diagnosis_procedure_mismatch | phantom_billing |
| CLM-01955 | upcoding | phantom_billing |
| CLM-01956 | diagnosis_procedure_mismatch | phantom_billing |

6 fraud claims carry a rule outside their own pattern.

### Unexpected

None.

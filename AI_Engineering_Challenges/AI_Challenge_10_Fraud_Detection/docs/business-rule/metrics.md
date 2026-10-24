# Metrics (C2)

The brief asks: "Report precision and recall against the known fraudulent claims. Target: >= 70% recall with <= 20% false positive rate".
Definitions of TP / FP / FN / TN, precision, recall, FPR, natural FP: see `glossary.md`, section Evaluation.

## Predicting fraud

- The engine returns a 0-100 score; the ground truth is only fraud / not fraud => a threshold is needed to turn the score into yes / no.
- Main metrics: **predict fraud when `risk_score` > 0** (>= 1 flag).
- Reason: the brief puts recall >= 70% first; a higher threshold (e.g. >= 40) would miss the fraud caught only by weak rules (weekend, clustering = 39 points), about 40 claims = 20% of the fraud.
- FPR = FP / (FP + TN) (the standard definition).

## Extra table by threshold

- Also report recall and FPR at score thresholds 0, 40 and 70 to show the trade-off.
- Practical meaning: if claim adjusters only review high-score claims, how much fraud is missed.

## Metrics report (C3)

The report has 4 parts:

1. **Overall**: TP, FP, FN, TN, precision, recall, FPR; compared with the targets recall >= 70%, FPR <= 20%.
2. **By pattern**: for each pattern, how many fraudulent claims and how many were caught (shows weak rules, e.g. upcoding hit by masking).
3. **Natural FP by rule**: false alarms counted per rule (shows the data has real noise).
4. **Threshold table**: recall / FPR at score thresholds 0, 40, 70.

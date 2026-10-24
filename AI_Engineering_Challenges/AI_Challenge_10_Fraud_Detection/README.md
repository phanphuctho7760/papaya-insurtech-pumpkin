# AI Challenge 10 - Fraud Detection Scoring Engine

Rule-based fraud scoring engine for health insurance claims: it analyzes each claim and assigns a risk score (0-100) with itemized evidence for every rule that fires.

**Status:** work in progress. The dataset generator (part A) is done; the rule engine, tests and metrics report are not built yet.

## Requirements

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)

No runtime dependencies: the code uses the Python standard library only (`pytest` is a dev dependency).

## Generate the dataset

From this folder (`AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/`):

```bash
uv sync                                   # create .venv and install dev dependencies
uv run python src/cli.py generate         # default seed 2024, writes to data/
```

Options:

| Option | Default | Meaning |
|---|---|---|
| `--seed` | `2024` | Random seed. The same seed always produces byte-identical files. |
| `--out` | `data/` | Output directory (created if missing). |

Expected console output:

```text
Wrote 2000 claims (200 fraud) to .../data with seed 2024
  amount_clustering                20
  diagnosis_procedure_mismatch     20
  duplicate_claim                  30
  phantom_billing                  25
  rapid_resubmission               30
  unbundling                       25
  upcoding                         30
  weekend_anomaly                  20
```

### Output files

| File | Content | Read by the engine |
|---|---|---|
| `data/claims.csv` | 2,000 claims with the 10 columns of the brief | Yes |
| `data/ground_truth.csv` | `claim_id`, `is_fraud` (1/0), `fraud_pattern` (empty for legitimate claims) | No, metrics only |
| `data/generation_summary.json` | Seed, claims per pattern, the 10 weekday-only hospitals, the phantom provider-day, claims per code | No, for review only |

`ground_truth.csv` and `generation_summary.json` are answer keys: the engine must detect fraud from `claims.csv` alone.

Format details (CSV dialect, `procedure_codes` joined with `|`, integer VND amounts, `is_weekend` as 1/0): [`docs/decisions/dataset-format.md`](docs/decisions/dataset-format.md).

### Check reproducibility

```bash
uv run python src/cli.py generate --out /tmp/run2
shasum -a 256 data/claims.csv /tmp/run2/claims.csv   # the two hashes must match
```

### What the dataset contains

- 2,000 claims dated 2024-01-01 to 2024-12-31, about 500 members, 50 providers (20 hospitals, 20 clinics, 10 dental clinics).
- 1,800 legitimate claims and 200 fraudulent claims (10%), each fraudulent claim carrying exactly one of the 8 patterns of the brief.
- Claim IDs are assigned after sorting by date, so fraudulent claims are spread over the whole ID range.

How each pattern is injected: [`docs/business-rule/fraud-injection.md`](docs/business-rule/fraud-injection.md). Known natural false positives and other pitfalls, with measured numbers: [`docs/experiences/dataset-generation-pitfalls.md`](docs/experiences/dataset-generation-pitfalls.md).

### Configuration

| File | Content |
|---|---|
| `src/config/catalog.json` | Procedures, bundles, standard prices, ICD-10 diagnoses, valid diagnosis-procedure pairs. Shared by the generator and the engine; validated on load by `src/catalog.py`. |
| `src/config/providers.json` | The 50 providers (ID, name, type). Read by the generator only. |

## Timeline estimate

Total estimate: **5-7 hours** (detailed plan: 6 hours).

| Item | Time | Includes |
|---|---|---|
| Dataset design | 1.5h | Schema, reference data, fraud injection, ground truth |
| Logic | 1.75h | 8 rules, evidence, weights, scoring, output |
| Unit tests | 1.25h | Unit tests for rules and edge cases, metrics (precision / recall / FPR), runtime measurement |
| Buffer and extra work | 1.5h | Estimation buffer, writeup, AI conversation logs |
| **Total** | **6h** | |

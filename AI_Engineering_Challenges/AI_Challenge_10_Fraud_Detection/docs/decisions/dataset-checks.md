# Dataset structural checks (`check` command)

**Purpose:** verify that a generated dataset has the structure the brief and the business rules require, before the engine or the metrics use it.
**Source:** `src/generator/checks.py` (`check_dataset`), called by `src/cli.py check`.
**Why a separate command:** `ADR-001-separate-dataset-check-command.md`.

## Usage

```bash
uv run python src/cli.py check [--data data]
```

| Input | Role |
|---|---|
| `<data>/claims.csv` | The claims, read back from disk (so CSV writing problems are caught too) |
| `<data>/ground_truth.csv` | Labels: `is_fraud`, `fraud_pattern` |
| `<data>/generation_summary.json` | The weekday-only hospitals and the phantom provider-day chosen by the seed |
| `src/config/catalog.json` | Codes, bundles, claim types |
| `src/config/providers.json` | The 50 providers |

Result:

- All checks pass: prints a summary (claims per pattern, members, providers, claims per provider type, weekday-only volume, smallest code volume, duplicate groups, phantom day), exit code 0.
- Any check fails: prints every problem to stderr, exit code 1. The files must not be used.

## Checks

If a shape check (group 1) fails, the remaining checks are skipped: they assume the files line up.

| # | Check | Expected | Why (source) |
|---|---|---|---|
| 1 | Header of `claims.csv` / `ground_truth.csv` | Exactly the columns of `dataset-format.md`, in order | Engine and metrics read columns by name |
| 1 | Row count | 2,000 claims | Brief |
| 1 | `claim_id` | Unique; `ground_truth.csv` has the same IDs in the same order | One label per claim |
| 2 | `is_fraud` vs `fraud_pattern` | `1` exactly when `fraud_pattern` is not empty | Label consistency |
| 2 | Claims per pattern | 30 / 30 / 30 / 25 / 25 / 20 / 20 / 20, total 200 | Brief, `../business-rule/fraud-injection.md` |
| 3 | Distinct members | 480-500 | Brief "~500"; uniform sampling gives ~491 (`../experiences/dataset-generation-pitfalls.md`, item 7) |
| 4 | Providers | Exactly the 50 of `providers.json`; each `provider_id` always with the same `provider_name` | Brief "~50"; one name per provider |
| 5 | `claim_date` | Valid `YYYY-MM-DD` within 2024 | Brief |
| 5 | `is_weekend` | Matches the weekday of `claim_date` | Brief "derived from claim_date" |
| 6 | `procedure_codes` | Every code exists in the catalog | Closed code set (`../business-rule/icd-10.md`) |
| 6 | Number of codes | Unbundling claims: exactly the components of one bundle, in catalog order; every other claim: exactly 1 code | `../business-rule/catalog.md`, `../business-rule/bundling.md` |
| 6 | `claim_type` | Equals the claim type of the (first) code | Claim type follows the code (`../business-rule/diagnosis-procedure-mismatch.md`) |
| 7 | `submitted_amount` | Positive integer, multiple of 100 | Same rounding for every claim, so the format does not leak labels (`../business-rule/fraud-injection.md`) |
| 7 | Clustering amounts | 47,500-49,999 | `../business-rule/amount-clustering.md` |
| 8 | Single-code claims per code | >= 30 for every one of the 21 codes | Upcoding needs history per code (`../business-rule/upcoding.md`) |
| 9 | Weekday-only hospitals | >= 60 claims each | 2 weekend frauds out of >= 60 stays below the 5% weekend-volume threshold (`../business-rule/weekday-only-providers.md`) |
| 9 | Weekend claims at weekday-only hospitals | Only the 20 `weekend_anomaly` claims | Same source |
| 9 | `weekend_anomaly` claims | Each has `is_weekend = 1`, a weekday-only provider and a surgical code; exactly 2 per weekday-only hospital | Same source, `../business-rule/fraud-injection.md` |
| 10 | Groups of the duplicate key `(member_id, provider_id, claim_date, diagnosis_code)` | Exactly 15 groups of 2, every other key unique | `../business-rule/duplicate-and-rapid-resubmission.md` |
| 10 | Claims in duplicate groups | Exactly the claims labelled `duplicate_claim` | Same source |
| 11 | Provider-days with > 30 claims | Only the phantom day of `generation_summary.json`, with exactly 31 claims | `../business-rule/fraud-injection.md` |
| 11 | Labels on the phantom day | Every `phantom_billing` claim is on that day; the day holds exactly 25 `phantom_billing` + 3 `upcoding` + 3 `diagnosis_procedure_mismatch` | Same source |

## Not checked here

- **Each fraud claim triggering its own rule (and only that rule):** needs the rule logic; belongs to the engine's integration test (#03). Copying rule logic here would create a second implementation that can drift from the engine.
- **Natural false positives** (legitimate claims that meet a rule's condition): measured and recorded in `../experiences/dataset-generation-pitfalls.md`, reported in the metrics report. They are allowed by design, so they are not a failure.
- **Claim type of the diagnosis:** reference only; a valid pair may cross claim types (`../business-rule/diagnosis-procedure-mismatch.md`).

## How the checks were verified

Each check was run against copies of the dataset broken on purpose (2026-10-24): duplicated `claim_id`, wrong `is_weekend`, amount off by 50, an extra duplicate group, a legitimate claim with 2 codes, wrong `claim_type`, a pattern count off by one, a renamed provider, a date in 2023, a legitimate weekend claim at a weekday-only hospital, a second provider-day with 31 claims. All 11 were caught; the real dataset (seed 2024) passes. The label-placement rows (added after the #01 review) were verified the same way: moving the `phantom_billing` label to a legitimate claim on another day fails the check.

These manual runs are now automated in `tests/test_dataset_check.py` (`uv run pytest`): each case copies `data/`, breaks exactly one thing (including missing or non-UTF-8 files, a broken `generation_summary.json`, rows with a wrong number of fields) and asserts the message of the check meant to catch it, with no traceback. Mutation run on 2026-10-24: disabling any one of the 34 checks in `src/generator/checks.py` makes at least one test fail.

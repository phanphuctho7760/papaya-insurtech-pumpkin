# AI Challenge 10 - Fraud Detection Scoring Engine

Rule-based fraud scoring engine for health insurance claims: it analyzes each claim and assigns a risk score (0-100) with itemized evidence for every rule that fires.

**Status:** complete. Dataset generator (part A), 8-rule engine with scoring (part B), tests and metrics (part C), writeup and AI conversation logs (part D).

Results on the committed dataset (2,000 claims, seed 2024): precision 81.3%, recall 100.0%, FPR 2.6%, scored in ~0.02 s. Targets of the brief: recall >= 70%, FPR <= 20%, < 30 s. Read the [Limitations](#limitations) before reading these numbers as an achievement.

## Requirements

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)

No runtime dependencies: the code uses the Python standard library only (`pytest` is a dev dependency).

## Generate the dataset

From this folder (`AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/`):

```bash
uv sync                                   # create .venv and install dev dependencies
uv run python src/cli.py generate         # default seed 2024, writes to data/
uv run python src/cli.py check            # structural checks on data/
```

`generate` options:

| Option | Default | Meaning |
|---|---|---|
| `--seed` | `2024` | Random seed. The same seed always produces byte-identical files. |
| `--out` | `data/` | Output directory (created if missing). |

`check` options:

| Option | Default | Meaning |
|---|---|---|
| `--data` | `data/` | Dataset directory to check. |

Generating and checking are two separate steps: `generate` only writes the files, `check` only reads them. `check` can therefore verify any existing dataset directory without regenerating it.

Expected output of `check`:

```text
Structural checks passed for .../data: 2000 claims, 200 fraud
  amount_clustering                20
  diagnosis_procedure_mismatch     20
  duplicate_claim                  30
  phantom_billing                  25
  rapid_resubmission               30
  unbundling                       25
  upcoding                         30
  weekend_anomaly                  20
  members 494, providers 50, claims per provider type {'CLINIC': 111, 'DENTAL': 334, 'HOSPITAL': 1555}
  weekday-only hospitals 70-86 claims, min single-code claims per code 43
  duplicate groups 15, phantom day PRV-049 2024-12-26 (31 claims)
```

`check` reads the files back from disk and verifies counts per pattern, columns and formats, members, providers, codes, weekday-only hospitals, duplicate groups, the single phantom provider-day, and that the weekend, duplicate and phantom labels sit on the claims they were injected into. If any check fails it prints the problems to stderr and exits with code 1; do not use the files in that case. Every check with its threshold and source: [`docs/decisions/dataset-checks.md`](docs/decisions/dataset-checks.md).

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

### Test the dataset check

```bash
uv run pytest tests/test_dataset_check.py -q   # 44 tests, ~3 s
```

`tests/test_dataset_check.py` guards `check` itself, not the dataset content. Each case copies the committed `data/` into a temporary directory, breaks exactly one thing, and asserts that `check` reports the problem of the check meant to catch it, without a traceback:

| Group | Examples of what is broken |
|---|---|
| Files and shape | missing file, BOM header, non-UTF-8 bytes, row with too many / too few fields, duplicate or reordered `claim_id`, 1,999 claims |
| `generation_summary.json` | not JSON, missing key, empty or wrong weekday-only list, `provider_id` of the wrong type |
| Values | wrong `is_weekend`, date in 2023 or invalid, amount not a multiple of 100, unknown code, wrong `claim_type`, clustering amount outside the band |
| Structure and labels | extra duplicate group, second provider-day above 30 claims, too few members / providers / single-code claims, weekday-only hospital below 60 claims, phantom / duplicate / weekend labels moved off the claims they were injected into |

Two more tests: the committed `data/` passes with no problem, and a broken summary plus a broken CSV row are reported in the same run.

The cases pick claims by condition (e.g. a legitimate single-code weekday claim), not by row position, so they keep working after `data/` is regenerated. Disabling any one of the 34 checks in `src/generator/checks.py` makes at least one test fail (mutation run, 2026-10-24). When a new check is added to `checks.py`, add a case that breaks exactly what it checks. The list of checks: [`docs/decisions/dataset-checks.md`](docs/decisions/dataset-checks.md).

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

## Score the claims

```bash
uv run python src/cli.py score            # reads data/claims.csv, writes output/scored_output.json
```

`score` options:

| Option | Default | Meaning |
|---|---|---|
| `--data` | `data/` | Directory holding `claims.csv`. Only that file is read. |
| `--weights` | `src/config/weights.json` | Severity weight (integer 1-5) of each of the 8 rules. |
| `--out` | `output/` | Output directory (created if missing). |

The output is a JSON array of all claims, ranked by `risk_score` (then by number of flags, then `claim_id`). Each element has exactly `claim_id`, `risk_score` and `flags`; each flag has `rule`, `severity` and `evidence`. Scoring formula and ranking: [`docs/business-rule/scoring.md`](docs/business-rule/scoring.md). If `claims.csv` or the weights file is invalid, `score` prints every problem in the first invalid file to stderr and exits with code 1 (it also exits 1 if `--out` cannot be written).

Output on the committed `data/` (seed 2024):

```text
Scored 2000 claims in 0.017 s; wrote .../output/scored_output.json
Claims with at least one flag: 246 of 2000
Claims per rule:
  duplicate_claim                  30
  rapid_resubmission               54
  upcoding                         48
  unbundling                       25
  phantom_billing                  31
  weekend_anomaly                  20
  diagnosis_procedure_mismatch     20
  amount_clustering                24
Top 10 by risk score:
  CLM-01940   86  phantom_billing, diagnosis_procedure_mismatch
  ...
```

## Evaluate against the ground truth

```bash
uv run python src/cli.py metrics          # re-runs score, then compares with data/ground_truth.csv
```

`metrics` takes the same options as `score`. It re-runs the whole score pipeline (rewriting `output/scored_output.json`) so the runtime it reports is measured on the run it evaluates, then writes `output/metrics_report.md`: overall precision / recall / FPR, recall by pattern, natural false positives by rule, a threshold table, and the fraud claims flagged by an extra rule. Why it re-runs scoring: [`docs/decisions/ADR-005-metrics-command-reruns-the-score-pipeline.md`](docs/decisions/ADR-005-metrics-command-reruns-the-score-pipeline.md). An invalid ground truth (bad header, unknown pattern, claim IDs that differ from `claims.csv`) stops it with exit code 1 and the full list of problems.

On the committed `data/`: precision 81.3%, recall 100.0%, FPR 2.6%, 2,000 claims scored in ~0.02 s.

## Run the tests

```bash
uv run pytest -q                          # 154 tests, ~3 s
```

- `tests/test_business_rules.py`: the 19 business test cases of `docs/business-rule/test-cases.md`.
- `tests/test_system_*.py`: input / weights loading, output format, ranking, metrics, engine boundary.
- `tests/test_dataset_check.py`: the `check` command against broken copies of the dataset.
- `tests/test_integration_dataset.py`: the engine on the committed dataset (own-rule hits, phantom-day exception, recall / FPR targets, < 30 s).

## Scoring weights

Each weight (1-5, in `src/config/weights.json`) is set on two criteria: **how certain the signal is** (is there a legitimate reason that produces the same sign?) and **how much the insurer loses** if it is real fraud. The brief's own example fixes two anchors: upcoding = 4, amount clustering = 2.

| Rule | Weight | Why |
|---|---|---|
| `duplicate_claim` | 5 | The data has passed input validation, so a second claim on the same member, provider, date and diagnosis is almost certainly fraud; the insurer pays twice for one visit. |
| `phantom_billing` | 4 | > 30 claims in one provider-day is a very clear anomaly with a large loss; not 5 because the rule flags every claim of that day, legitimate ones included. |
| `upcoding` | 4 | Brief's anchor. Direct financial loss; a statistical threshold, so ~2% of legitimate claims can still exceed mean + 2 SD. |
| `diagnosis_procedure_mismatch` | 4 | A clear medical inconsistency; sometimes a data-entry error. |
| `unbundling` | 3 | Deterministic, it is certainly an unbundled bill; but the overcharge is only ~10% of the bundle price. |
| `rapid_resubmission` | 3 | A follow-up visit for the same diagnosis within 7 days can be legitimate. |
| `weekend_anomaly` | 2 | Indirect signal; a hospital's schedule can change. |
| `amount_clustering` | 2 | Brief's anchor. The weakest signal: legitimate claims fall in the 47,500-49,999 band on their own. |

Score = `100 x (1 - e^(-0.25 x sum of weights))`: one weight-2 rule gives 39, `duplicate_claim` alone gives 71, and the curve saturates instead of capping, so two strong rules still rank above one. Full formula and ranking: [`docs/business-rule/scoring.md`](docs/business-rule/scoring.md). Rule thresholds are constants, only weights are configurable: [`ADR-003`](docs/decisions/ADR-003-only-weights-are-configurable.md).

## Limitations

- **Recall 100% is an upper bound, not a result.** The same person wrote the 8 rules and generated the data to match their definitions, so every injected pattern is caught by construction. Real data would score lower: fraud that does not follow the textbook pattern, noisier legitimate claims, several patterns on one claim.
- **The dataset is hand-placed, not random.** One fixed seed (2024), with constraints that keep each fraud claim inside its own pattern; the tests read that one committed dataset. Next step: a generator that places fraud at random (any seed), so the engine is shown to work on data it was not tuned to.
- **At a high threshold most fraud is missed.** At `score >= 70` recall drops to 18.0% (FPR 0.0%), because weak rules (weekend, clustering) give 39 points. This is why the main metric predicts fraud at `score > 0`; a claims team that only reviews high scores needs different weights or a second queue.
- **One pattern per fraud claim.** Deliberate simplification of the generator; in reality a claim can carry several.
- **Upcoding uses mean and SD over all claims of the code, upcoded ones included** (masking accepted because recall met the target; leave-one-out was the fallback). The `>` vs `>=` boundary of mean + 2 SD has no test, because it needs an amount exactly on a non-integer threshold.
- **Clinics are small.** The 20 clinics get only ~1-15 claims each, a side effect of giving every hospital the same volume: [`ADR-004`](docs/decisions/ADR-004-equal-volume-for-all-hospitals.md).

## Timeline

| Item | Estimate | Includes |
|---|---|---|
| Dataset design | 1.5h | Schema, reference data, fraud injection, ground truth |
| Logic | 1.75h | 8 rules, evidence, weights, scoring, output |
| Unit tests | 1.25h | Unit tests for rules and edge cases, metrics (precision / recall / FPR), runtime measurement |
| Buffer and extra work | 1.5h | Estimation buffer, writeup, AI conversation logs |
| **Total** | **6h** (range 5-7h) | **Real: ~9h** |

Real time was ~9h, about 3h over (not tracked per item). Work that was not in the estimate: the 44-case test suite for the `check` command, the `reviewer` rounds and their fixes, and the decision docs / ADRs written as decisions were made.

## Agent Workflow

Tools: Claude Chat to explore the brief and the insurance domain (log 01); Claude Code for everything else (logs 02-08). Logs: [`conversations/`](conversations/README.md).

How the work was directed:

- The brief was split into 4 parts (A dataset, B engine, C tests and metrics, D writeup), each a backlog ticket with acceptance criteria and an execution plan in phases: [`docs/requirements/challenge-10-requirements.md`](docs/requirements/challenge-10-requirements.md), [`docs/backlog/`](docs/backlog/README.md).
- Business rules were settled in `docs/business-rule/` before any code for them was written; the AI implemented from those docs, not from the brief directly.
- The main Claude Code thread is the orchestrator. Two subagents: `coder` (writes code from an exact spec) and `reviewer` (read-only, checks the diff against the business rules). Every reviewer finding was opened at its `file:line` and confirmed or rejected before fixing; tests were re-run before relaying any "done".

Mistakes caught, and by whom:

| What went wrong | Caught by | Log |
|---|---|---|
| Plan 01 had no step that actually generates the 2,000 claims | me | 03 |
| `generate` ran the dataset check inside itself; split into two commands | me | 03, [`ADR-001`](docs/decisions/ADR-001-separate-dataset-check-command.md) |
| Legitimate amounts rounded to 1,000, clustering fraud to 100: the rounding leaked the label | AI, re-reading the business docs before Phase 2 | 03 |
| Fraud amount factor clamped to +-15% piled amounts on 2 exact values that leaked the label | `reviewer` | 05 |
| ~12 hand-broken datasets used to test `check` were one-off; turned into a 44-case test suite | me | 05 |
| Tests mixed two concerns; split into system tests (does code match the design) and business tests (do the rules give the right result) | me | 04 |
| A ground truth with a misspelled pattern name was silently ignored by `metrics` | `reviewer` | 07 |

Checked by hand: evidence text of flagged claims read by eye against the rule definitions; the metrics report numbers against the brief's targets; the "too good" recall, which led to the Limitations above.

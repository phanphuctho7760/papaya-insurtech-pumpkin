# Challenge 10 - Requirement breakdown

Breaks AI Challenge 10 - Fraud Detection Scoring Engine down into main parts and details.
Source: `docs/requirements/original-brief.md`, Part 1 (R1-R7) and Part 2 (R8).
Paths in this file are relative to the project folder `AI_Challenge_10_Fraud_Detection/`.
Stage: New Task (per Task_Lifecycle). Technology not chosen yet.

## Original requirements (R)

| Code | Requirement | Source |
|---|---|---|
| R1 | Estimate and report the timeline | Brief, section Note |
| R2 | Generate a dataset of 2,000 claims, 10 columns, embedding ~200 fraud cases across 8 patterns, with ground truth | Brief, section Dataset |
| R3 | Reference data: >= 5 bundles, >= 10 valid diagnosis-procedure pairs, a shared code set | Brief, section Detection Rules |
| R4 | 8 detection rules, every flag with specific evidence | Brief, sections Detection Rules + Evaluation Criteria |
| R5 | Configurable weights 1-5, score 0-100, ranked list, JSON per claim, weights explained | Brief, sections Output + Scoring + Evaluation Criteria |
| R6 | Precision, recall against the ground truth; recall >= 70%, FPR <= 20%; metrics report | Brief, sections Metrics + Submission |
| R7 | >= 15 unit tests (each rule + edge cases); 2,000 claims processed in < 30 seconds | Brief, section Evaluation Criteria |
| R8 | GitHub repo, writeup, verbatim AI conversation logs (mandatory, missing = fail), no one-shot | General README |

## Main parts and details

### A. Generate the dataset

- A1. 10-column schema, 2,000 claims, ~500 members, ~50 providers, year 2024; `is_weekend` derived from `claim_date`. (R2)
- A2. Reference data: ICD-10 and procedure codes, >= 5 bundles, >= 10 valid diagnosis-procedure pairs, list of surgical procedures. Shared with part B. (R3)
- A3. Embed ~200 fraud cases across 8 patterns, with the brief's counts. (R2)
- A4. Ground-truth label for every claim. (R2)
- A5. Export the dataset files for submission. (R8)

### B. Rule logic (engine)

- B1. 8 detection rules. (R4)
- B2. Specific evidence with numbers for every flag. (R4)
- B3. Configurable weights 1-5, with the reasons for each choice. (R5)
- B4. Score 0-100, JSON output per claim, list ranked by score. (R5)
- B5. Performance constraint: 2,000 claims in < 30 seconds. (R7)

### C. Verification

- C1. >= 15 unit tests for each rule and edge cases. (R7)
- C2. Precision and recall against the ground truth; targets recall >= 70%, FPR <= 20%. (R6)
- C3. Metrics report. (R6)
- C4. Measure the runtime to prove B5. (R7)

### D. Delivery (not code)

- D1. Timeline estimate sent to Papaya. (R1)
- D2. Writeup in the README: approach, decisions, reasons for the weights. (R5, R8)
- D3. Verbatim AI conversation logs, mandatory. (R8)
- D4. GitHub repo with the dataset, scored output and metrics report. (R8)

## Settled decisions

- Current stage: New Task. Technology chosen later (possibly in Claude Code).
- Target timeline 4-6 hours, not committed until the brief is fully analyzed.
- Timeline 5-7h (plan 6h): dataset 1.5h, logic 1.75h, unit tests 1.25h (including C2, C3, C4), buffer 1.5h. Recorded in the project `README.md`.
- A: write generator code, constrained to produce every fraud pattern of the brief.
- A: legitimate data may trigger rules naturally (natural FP), counted and reported in the metrics.
- A2: diagnoses use real ICD-10 codes; procedures use made-up `P-xxxx` codes. See `docs/business-rule/icd-10.md`.
- A4: input (`claims.csv`, only the brief's 10 columns) is separate from the ground truth (`ground_truth.csv`: claim_id, is_fraud, fraud_pattern). The engine does not read the ground truth.
- A: fixed seed so the dataset is reproducible.
- A3: a fraudulent claim carries only 1 pattern (a deliberate limitation; in reality there can be several).
- A3: there is a group of weekday-only providers. See `docs/business-rule/weekday-only-providers.md`.
- Fraud counting: option C, counted per claim, 200 fraudulent claims in total. Duplicate 15 pairs (30 claims). Phantom: 1 provider-day with 31 claims = 25 claims labeled phantom + 6 claims labeled upcoding / mismatch.
- Providers: 50 providers of 3 types (hospital, clinic, dental clinic); 10 weekday-only hospitals, each receiving 2 weekend fraud claims.
- Currency VND, keeping the brief's numbers; private hospital price level.
- A2 recorded in: `docs/business-rule/` (catalog, icd-10, upcoding, bundling, diagnosis-procedure-mismatch, amount-clustering, weekday-only-providers).
- A legitimate claim has exactly 1 procedure code; amount = standard price x log-normal with 15% variation; upcoded = standard price x 1.6-2.5.
- Unbundling flags when a claim contains all the components of a bundle.
- Amount clustering uses P-1003 (standard price 40,000, 15% variation).
- A3: rapid re-submission 15 pairs (30 claims), both claims labeled fraud, 1-7 days apart. Summary: `docs/business-rule/fraud-injection.md`.
- A5: CSV RFC 4180 (`,` separator), `procedure_codes` separated by `|`, dates `YYYY-MM-DD`, amount as integer VND, `is_weekend` 1/0, ground truth in a separate file. See `docs/decisions/dataset-format.md`.
- Part A: fully settled.
- Technology: A uses Python; B was planned in TypeScript, Python for both A and B under consideration (the brief asks for no API). Structure of `src/` and `conversations/`: `docs/decisions/tech-and-structure.md`.
- The emergency concept is left out of scope entirely.
- B1 upcoding: codes with < 10 claims are not checked; the generator creates >= 30 claims per code.
- B2 evidence: English, with the English name of every code, all 3 parts (observed / threshold / related claims). See `docs/business-rule/evidence.md`.
- B3 weights: Duplicate 5, Phantom 4, Upcoding 4, Mismatch 4, Unbundling 3, Rapid 3, Weekend 2, Clustering 2. See `docs/business-rule/scoring-weights.md`.
- B4 scoring: weighted sum + saturating scale `100 x (1 - e^(-0.25 x total))` (matches the brief's example of 78); ranked descending; output covers every claim. See `docs/business-rule/scoring.md`.
- C2 metrics: predict fraud when score > 0; FPR = FP/(FP+TN); extra table at thresholds 0/40/70. See `docs/business-rule/metrics.md`.
- C1 tests: 19 tests (each rule 1 flag case + 1 no-flag case + boundary cases, plus scoring). See `docs/business-rule/test-cases.md`.
- C3 metrics report: 4 parts (overall, by pattern, natural FP by rule, threshold table). See `docs/business-rule/metrics.md`.
- The project stands on its own: the brief and the general rules are merged in `docs/requirements/original-brief.md`; requirement breakdown and handbook notes live in `docs/`.
- B1 weekend: the rule is computed over all of the provider's claims; every weekday-only hospital has >= 60 claims.
- Business of the 8 rules: `docs/business-rule/detection-rules.md`.
- B1 upcoding: mean/SD computed over every claim with the same code (upcoded claims included), masking accepted; measure recall first, switch to leave-one-out only if the target is missed. See `docs/business-rule/upcoding.md`.
- B1 duplicate: unique key `(member_id, provider_id, claim_date, diagnosis_code)`; a group of >= 2 claims => flag all of them.
- B1 rapid re-submission: only pairs on the same duplicate unique key are skipped; same-day pairs at different providers are still rapid. See `docs/business-rule/duplicate-and-rapid-resubmission.md`.
- Duplicate: the data has passed input validation, there is no double-submit; two matching claims are two independent claims and are fraud. The rule flags both claims of the pair, both labeled fraud.
- Technology (settled 2026-10-24): Python for A, B and C; standard library + pytest only; `src/api/` dropped. See `docs/decisions/tech-and-structure.md`.
- B1 upcoding: only claims with exactly 1 code take part in the mean/SD and are checked; claims with several codes (unbundling) are skipped. Mismatch checks every code. See `docs/business-rule/upcoding.md`.
- A: the generator only runs structural checks after generating; cross-checking rules against labels moved to C (integration test). See `docs/business-rule/fraud-injection.md`.
- A1 providers (2026-10-24): 50 providers fixed in `src/config/providers.json` (id, name without diacritics, type), IDs interleaved across types; the weekday-only list is not in the config, the generator picks it by seed.
- A1 members (2026-10-24): picked uniformly from `MEM-0001..0500`, no pre-allocation; "~500" is checked automatically as >= 480 distinct members (expected ~491).
- A2 claim_type (2026-10-24): a diagnosis's claim_type is for reference only, a claim's claim_type comes from its code. The 2 cross-type pairs `K80.2 - P-1005`, `J18.9 - P-1004` are kept. See `docs/business-rule/diagnosis-procedure-mismatch.md`.
- A amounts (2026-10-24): every amount is rounded to 100 VND, legitimate and fraud alike (an earlier version rounded them differently => the clustering label leaked). See `docs/business-rule/fraud-injection.md`.
- B5 / C4: rapid groups by `(member_id, diagnosis_code)`; runtime measured with `time.perf_counter()` in the CLI, written to the metrics report.
- Risks estimated before coding: `docs/experiences/dataset-generation-pitfalls.md`.
- A2 valid pairs fixed: added `J06.9 - P-1003`, `I10 - P-1003`, `E11.9 - P-1002` (35 pairs) so unbundled B-1001 / B-1002 claims do not trip mismatch. See `docs/business-rule/diagnosis-procedure-mismatch.md`.
- A3 (revised 2026-10-24 after review of #01): amounts of fraud claims outside the amount patterns use a factor re-drawn until inside [0.85, 1.15] (truncated, not clamped: clamping piled amounts on 2 exact values that leaked the label); upcoded claims are spread over codes with >= 60 claims, at most 2 per code. See `fraud-injection.md`, `upcoding.md`.
- Work tracking: tickets in `docs/backlog/`, plans in `.claude/docs/plans/` (repo root).
- Agent workflow (2026-10-24): subagents `coder` (sonnet) and `reviewer` (opus, read-only) in `.claude/agents/`; trigger table in the repo-root `AGENTS.md`; the pre-commit doc sweep stays on the main thread.
- Docs (2026-10-24): business terms have a single source, `docs/business-rule/glossary.md`; other docs link to it instead of defining terms.
- Tests (2026-10-24): two kinds. **System tests** (#02) check that the code implements the technical design discussed (input / weights loading, output format, ranking, engine / ground-truth boundary). **Business tests** (#03, the 19 in `docs/business-rule/test-cases.md`) check that the 8 rules and scoring give correct business results.
- B4 (2026-10-24): a rule raises at most 1 flag per claim; the evidence lists every related claim. Reason: the score sums the weights of the triggered rules, so 2 flags of one rule would count its weight twice. See `docs/business-rule/scoring.md`.
- B1 upcoding (2026-10-24): SD = `statistics.pstdev` (population SD, the data is every claim of the code, not a sample); flag on `>` mean + 2 SD; SD = 0 => no flag. See `docs/business-rule/upcoding.md`.
- B2 rapid evidence (2026-10-24): worded by time order (after / followed by / same day at another provider). See `docs/business-rule/evidence.md`.
- B1 weekend (2026-10-24): "surgical" = at least 1 code in `procedure_codes` is a procedure or bundle with `surgical = true`; weekend taken from the `is_weekend` column. See `docs/business-rule/weekday-only-providers.md`.
- B input (2026-10-24): invalid input stops the engine with the full list of problems; no rows are skipped. See `docs/decisions/ADR-002-invalid-input-stops-the-engine.md`.
- B config (2026-10-24): only the weights are configurable (the brief only asks for weights); rule thresholds are constants at the top of each rule file. See `docs/decisions/ADR-003-only-weights-are-configurable.md`.
- B4 output (2026-10-24): `output/scored_output.json` is a ranked JSON array; each element has exactly the brief's 3 fields; flags inside a claim sorted by severity descending. See `docs/business-rule/scoring.md`.
- A provider volume (2026-10-24, review of #01): 150 legit claims moved from DENTAL to OUTPATIENT codes; all 20 hospitals get the same pre-assigned 58-62 OUTPATIENT / INPATIENT claims, so the weekday-only group is not the 10 largest; fraud providers are drawn weighted by legit volume, so no provider type has an outlier fraud rate. Known limitation, accepted: the 20 clinics get only ~1-15 claims each. Making them larger needs a lower weekday-only floor (< 60) or fewer dental providers; both rejected. See `docs/decisions/ADR-004-equal-volume-for-all-hospitals.md`.
- C2 thresholds (2026-10-25): threshold table rows are `score > 0` (main metric), `score >= 40`, `score >= 70`. With the current weights scores are discrete (39, 53, 63, 71, ...), so `>` or `>=` at 40 / 70 gives the same result; `>=` reads more naturally. See `docs/business-rule/metrics.md`.
- C4 runtime (2026-10-25): the `metrics` command re-runs the whole score pipeline (load -> rules -> score -> write `scored_output.json`), times it with `time.perf_counter()` (one in-process run, Python startup excluded), then compares with the ground truth. Rejected: reading an existing `scored_output.json`, because the output only has the brief's 3 fields and carries no runtime. See `docs/decisions/ADR-005-metrics-command-reruns-the-score-pipeline.md`.
- C2 boundary (2026-10-25): only `src/metrics/` reads `ground_truth.csv`; the engine never imports `metrics`. If the ground-truth `claim_id` set differs from the scored claims, `metrics` stops with exit 1 (same stance as ADR-002).
- C3 natural FP by rule (2026-10-25): an FP claim with 2 rules is counted under both; the table adds a total row of FP claims so the columns are not summed into a wrong total.
- C1 integration test (2026-10-25): the allowed exception (fraud claims on the phantom provider-day may also trigger `phantom_billing`) is derived from `generation_summary.json`, not hard-coded claim IDs; any other extra rule fails the test with claim ID, pattern and extra rules.
- C3 report format (2026-10-25): `output/metrics_report.md` in English; header with dataset, weights in use and runtime, then the 4 parts of `metrics.md` as tables, percentages with 1 decimal, 1-2 sentences reading each table. Deterministic except the runtime line.
- D writeup (2026-10-25): no rewrite of the generator into a random dataset (does not fit the remaining time); the fixed, hand-placed seed-2024 dataset is listed under `## Limitations` in `README.md` as a next step. The submission email is handled by the user, outside ticket #04. See `docs/backlog/done/04-writeup-and-submission.md`.

## Open questions (discussed when each part is detailed)

| Part | Question |
|---|---|

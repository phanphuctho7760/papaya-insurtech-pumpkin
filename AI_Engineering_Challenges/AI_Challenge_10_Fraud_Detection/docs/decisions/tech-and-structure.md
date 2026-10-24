# Technology and project structure

> Intended design; it may change while the work goes on. When it changes: update this file and record the reason.

## Technology (settled 2026-10-24)

| Part | Technology | Notes |
|---|---|---|
| A. Dataset generation | Python | Writes `claims.csv` + `ground_truth.csv`, fixed seed |
| B. Engine (8 rules, scoring) | Python | Same language as A |
| C. Tests, metrics | pytest | |

- Libraries: standard library only (`csv`, `json`, `statistics`, `random`, `datetime`, `math`, `time`) + pytest for tests.

### Options considered

| Option | Why rejected / chosen |
|---|---|
| TypeScript for B, Python for A | Rejected: the config would be read in 2 languages, easy for the generator and the engine to drift apart. The only gain is matching Papaya's backend stack. |
| **Python for A, B and C** | Chosen: the brief asks for no API; 1 place reads the config, 1 test runner; Python is the team's AI/ML stack (Handbook `Tech_Stack.md`). |
| pandas | Rejected: 2,000 rows is tiny; plain code is easier to explain line by line in the interview. |

## Technical notes

- `config/` holds shared JSON files (bundle map, valid pairs, standard prices, weights) so the generator and the engine cannot drift apart. Weights 1-5 are validated on load.
- No API (the brief does not ask for one). Batch runs through the CLI, writing files.
- Every rule has the same signature: it takes the full list of claims and returns flags by `claim_id`. Reason: 5 of the 8 rules need to look at several claims (duplicate, rapid, upcoding, phantom, weekend).
- Rules return evidence only (`claim_id -> evidence`); the engine attaches the severity from the weights, so a rule never knows its weight.
- The engine never imports from `generator/` (the generator knows the labels). Input loading lives in `src/claims.py`, next to `catalog.py`.
- Invalid input stops the engine with the full list of problems; no rows are skipped (`ADR-002-invalid-input-stops-the-engine.md`).
- Only the weights are configurable (`src/config/weights.json`); rule thresholds are constants at the top of each rule file (`ADR-003-only-weights-are-configurable.md`).
- Performance (B5): the rapid rule only compares pairs inside a `(member_id, diagnosis_code)` group of a few claims => no O(n^2) over the whole dataset.
- Timing (C4): `time.perf_counter()` around the whole load -> rules -> score -> write flow in the CLI; the result goes into the metrics report.
- The generator assigns `claim_id` after sorting all claims by date, so fraudulent claims do not cluster at the end of the ID range.
- Generating and checking the dataset are separate CLI commands (`ADR-001-separate-dataset-check-command.md`); the checks are listed in `dataset-checks.md`.

## Structure of `src/`

```
src/
|-- config/      # weights.json, catalog.json (procedures, bundles, prices, valid pairs), providers.json (50 providers, read by the generator only)
|-- generator/   # dataset generation + ground-truth labels + structural checks
|-- rules/       # 8 rules, one file each, pure functions
|-- scoring/     # weighted sum, 0-100 normalization, ranking
|-- metrics/     # precision, recall, FPR, 4-part report
`-- cli.py       # generate | check | score | metrics
tests/           # pytest
data/            # claims.csv, ground_truth.csv
output/          # scored_output.json, metrics_report.md
```

## Structure of `conversations/`

```
conversations/
|-- README.md                      # index
|-- 01-chat-research-domain.md     # Claude Chat
|-- 02-code-setup-project.txt      # Claude Code: tech decisions, backlog, plan 01
|-- 03-code-phase1-generator.txt   # Claude Code (planned)
`-- 04-code-phase2-rules.txt       # Claude Code (planned)
```

- Claude Chat: saved with the `/noteconversaion-clacowo-bunhy` skill (under consideration).
- Claude Code: saved with `/export`, kept as the original `.txt` (not converted to `.md`, to stay verbatim).
- Naming `NN-<tool>-<topic>`, `NN` in chronological order; `README.md` lists every file.
- Logs are kept verbatim, never edited.

## Data formats

See `dataset-format.md`.

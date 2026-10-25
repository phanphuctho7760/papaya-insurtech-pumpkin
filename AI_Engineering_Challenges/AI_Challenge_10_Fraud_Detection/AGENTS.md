# AGENTS.md - AI Engineering Challenges

This folder holds **AI Challenge 10 - Fraud Detection Scoring Engine** (Advanced, 3 points, the brief estimates 4-6 hours).
Code lives in this folder (`AI_Challenge_10_Fraud_Detection/`).

## Planned layout of `AI_Challenge_10_Fraud_Detection/`

```
AI_Challenge_10_Fraud_Detection/
|-- README.md          # submission writeup: approach, decisions, weights, metrics, agent workflow
|-- AGENTS.md          # project-level agent instructions
|-- docs/
|   |-- business-rule/  # business meaning of the 8 rules, catalog
|   |-- requirements/   # original-brief.md (verbatim brief), requirement breakdown + settled decisions
|   |-- handbook-notes.md
|   |-- backlog/        # A/B/C/D tickets: what, why, done criteria
|   |-- experiences/    # pitfalls / risks met while implementing
|   `-- decisions/      # technical design: technology, structure, data formats
|-- src/               # source code, details: docs/decisions/tech-and-structure.md
|-- tests/             # pytest
|-- data/              # claims.csv, ground_truth.csv
|-- output/            # scored_output.json, metrics_report.md
`-- conversations/     # verbatim AI conversation logs (mandatory for submission)
    `-- README.md      # log index: which session, which tool, main content
```

## Saving AI conversation logs

- Claude Chat: considering the `/noteconversaion-clacowo-bunhy` skill.
- Claude Code: use the export feature.
- Every log goes in `conversations/`, kept verbatim, never edited. `conversations/README.md` lists each log file.
- The agent reminds the user to save the log at the end of every important working session.

## Required reading

- Original brief (Challenge 10 + general rules, verbatim): `docs/requirements/original-brief.md`
- Handbook notes for Challenge 10: `docs/handbook-notes.md`. Remind the user per its "When to remind" table when they analyze the brief, choose a solution, estimate the timeline, write the README, review AI output, or name things / write evidence in insurance-domain terms.
- Business terms (single source; other docs link here instead of redefining terms): `docs/business-rule/glossary.md`.
- A/B/C/D requirement breakdown, settled decisions, open questions: `docs/requirements/challenge-10-requirements.md`. Update it whenever a new decision is made.

## What Papaya grades (from the general README)

- Software design: how the problem is broken down and the solution structured.
- Attention to detail: edge cases, things the brief leaves unsaid.
- Polish: a result that "feels right", not just one that runs.
- Learning velocity: picking up the insurance domain quickly.
- **One-shot = fail.** The process of directing the AI, catching its mistakes and making trade-offs must be visible.
- **Verbatim AI conversation logs are mandatory** (export / transcript); missing them is an automatic fail.
- Any decision may be questioned in the interview: everything in the submission must be understood and explainable.

## Core requirements of the brief (checklist)

- [x] Dataset of 2,000 claims, ~500 members, ~50 providers, year 2024, with `is_weekend`.
- [x] ~200 fraudulent claims (~10%) embedded across 8 patterns with the brief's counts, with ground-truth labels.
- [x] 8 rules: duplicate, rapid re-submission, upcoding, unbundling (>= 5 bundles), phantom billing, weekend anomaly, diagnosis-procedure mismatch (>= 10 valid pairs), amount clustering.
- [x] Output per claim: `claim_id`, `risk_score` 0-100, `flags[]` with `rule`, `severity`, specific `evidence` (with numbers).
- [x] Configurable severity weight 1-5; score = weighted sum normalized to 0-100; list ranked by score.
- [ ] Explain the weight choices.
- [x] Metrics: precision, recall; target recall >= 70%, FPR <= 20%.
- [x] >= 15 unit tests (each rule + edge cases).
- [x] Processing 2,000 claims takes < 30 seconds.
- [ ] Estimate and report the timeline.
- [ ] Submit: dataset, scored output, metrics report, writeup (`README.md`), AI conversation logs (`conversations/`).

## Decisions

Settled decisions and open questions: `docs/requirements/challenge-10-requirements.md` (single source, not copied here).

## Agent conventions

- Work in phases: analyze the brief -> compare >= 2 solutions -> plan -> code -> test -> review -> writeup. Never jump straight into code.
- The user reviews 100% of plans / assumptions before code is written.
- No one-shot: split work into small steps, each with its own verification.
- Record every assumption about ambiguous parts of the brief in `docs/requirements/challenge-10-requirements.md` and in the writeup.
- Code favors readability over abstraction; no features beyond the brief.

## Documentation conventions (per the `pjdoc-mgmt-claco-bunhy` skill)

- Work items: tickets in `docs/backlog/{idea,todo,done}/NN-<slug>.md`; the execution plan with the same number in `.claude/docs/plans/{todo,done}/NN-<slug>.md` (repo root). Status lives in the ticket, execution detail in the plan.
- **New** technical decisions use the skill's ADR format: `docs/decisions/ADR-NNN-<title>.md`. Existing files in `docs/decisions/` keep their current format.
- Pitfalls / risks met or estimated: `docs/experiences/`.
- No changelog: commit history and conversation logs are enough.
- Language: every doc in this folder (`docs/`, `README.md`, `AGENTS.md`) is written in English; code, comments and commit messages are English too. Docs still in Vietnamese are converted to English when they are next edited (whole file at once, never two languages in one file), not in a bulk pass. The execution plans in `.claude/docs/` at the repo root stay in Vietnamese.
- Before every commit run `/pjdoc-mgmt-claco-bunhy pre-commit`. When writing Python apply `/pyfriend-claco-bunhy`.

# 04 - D: Writeup and submission

**Status:** done
**Type:** chore
**Priority:** 4
**Effort:** S
**Plan:** none yet
**Related:** #01, #02, #03

## What

Submission `README.md` (approach, decisions, weights, metrics, real timeline, agent workflow, limitations), a repo-root `README.md`, complete conversation logs in `conversations/`, push the repo.

## Why / value

Missing conversation logs is an automatic fail; the writeup is where Papaya reads the reason behind every decision, and the "Agent Workflow" section is where they see how the AI was directed (the brief grades "direct the AI tool effectively").

## Acceptance criteria

- `README.md` (Challenge 10) has:
  - the run commands, with numbers matching a final `uv run python src/cli.py metrics` run on the committed `data/`;
  - the weight explanation: the business reason for each rule's weight, not only the numbers;
  - the real metrics (from the final `output/metrics_report.md`);
  - a **`## Limitations`** section (exact heading, `output/metrics_report.md` links to it) covering at least: the dataset is generated from the same rule definitions the engine applies (recall 100% is an upper bound), recall drops to 18% at threshold >= 70, and the dataset is hand-placed with a fixed seed 2024 (not random);
  - an **Agent Workflow** section: tools and agents used (main thread + `coder` / `reviewer`), the key instructions given, the AI mistakes caught and how, what was verified by hand; each point links to the log file where it happened;
  - the timeline: estimate vs real time per item;
  - the status line no longer says "work in progress".
- Repo root has a short `README.md` pointing to `Logical_Questions/` and `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/`.
- `conversations/README.md` lists every log file, including the log of this writeup session (exported last); the `01-chat-research-domain.md` row is either backed by a real file or removed (no "planned" left).
- Every log file in `conversations/` is committed.
- The repo holds the dataset, the scored output and the metrics report.
- Everything is pushed to `origin/main`.

Out of scope: the submission email (the user handles it).

## Notes

From #03 (2026-10-25, rough measurement on seed 2024; use the final numbers in `output/metrics_report.md`):

- **Recall 100% / FPR 2.6% is "too good".** The same person wrote the rules and generated the data to fit the rule definitions, so the engine catches every injected pattern by construction. The writeup must state this limitation (real data would score lower: fraud that does not match the textbook pattern, noisier legit data) instead of presenting the numbers as an achievement.
- **At threshold >= 70 recall drops to 18%.** If claim adjusters only review high-score claims, they miss most of the fraud (weak rules such as weekend and clustering give 39 points). This is the reason the main metric predicts fraud at `score > 0`.

Decided 2026-10-25: **no random dataset rewrite.** Today the generator places fraud on purpose (fixed seed 2024, constraints that keep each fraud claim inside its own pattern) and the tests read that one committed dataset. Rewriting generation to be random would show the engine works on data it was not tuned to, but it does not fit an S ticket this close to the deadline. The writeup lists it under Limitations next to the "too good" recall note, as a next step.

From #03 Phase 2 review (2026-10-25):

- `output/metrics_report.md` (Overall section) says "see Limitations in README.md". The README must get a **Limitations** section with that exact heading.

From the ticket review (2026-10-25):

- `conversations/README.md` updated with logs 03-07; `07-code-and-metric.txt` still needs committing.
- No secrets found in the logs (quick scan for keys / passwords).
- Logical_Questions has 5 answers (Q1, Q4, Q5, Q8, Q10), both mandatory ones included; check again before submitting.

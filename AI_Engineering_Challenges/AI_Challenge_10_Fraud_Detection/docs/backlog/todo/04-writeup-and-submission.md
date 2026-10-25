# 04 - D: Writeup and submission

**Status:** todo
**Type:** chore
**Priority:** 4
**Effort:** S
**Plan:** none yet
**Related:** #01, #02, #03

## What

Submission `README.md` (approach, decisions, weights, metrics, real timeline, agent workflow), complete conversation logs in `conversations/`, push the repo.

## Why / value

Missing conversation logs is an automatic fail; the writeup is where Papaya reads the reason behind every decision.

## Acceptance criteria

- `README.md` has the run commands, the weight explanation, the real metrics and the remaining limitations.
- `conversations/README.md` lists every log file.
- The repo holds the dataset, the scored output and the metrics report.

## Notes

From #03 (2026-10-25, rough measurement on seed 2024; use the final numbers in `output/metrics_report.md`):

- **Recall 100% / FPR 2.6% is "too good".** The same person wrote the rules and generated the data to fit the rule definitions, so the engine catches every injected pattern by construction. The writeup must state this limitation (real data would score lower: fraud that does not match the textbook pattern, noisier legit data) instead of presenting the numbers as an achievement.
- **At threshold >= 70 recall drops to 18%.** If claim adjusters only review high-score claims, they miss most of the fraud (weak rules such as weekend and clustering give 39 points). This is the reason the main metric predicts fraud at `score > 0`.

Optional, only if time remains (noted 2026-10-25, not committed to):

- **Random dataset instead of a hard-coded one.** Today the generator places fraud on purpose (fixed seed 2024, constraints that keep each fraud claim inside its own pattern) and the tests read that one committed dataset. Rewriting generation to be random (any seed, fraud not hand-placed) would make the tests more transparent: the engine would be shown to work on data it was not tuned to. If done, the writeup explains the change; if not, the writeup lists it as a known limitation next to the "too good" recall note above.

From #03 Phase 2 review (2026-10-25):

- `output/metrics_report.md` (Overall section) says "see Limitations in README.md". The README must get a **Limitations** section with that exact heading, or the report sentence must change.

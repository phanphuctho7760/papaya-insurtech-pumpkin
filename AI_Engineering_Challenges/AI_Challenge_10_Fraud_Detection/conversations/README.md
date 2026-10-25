# AI conversation logs

Verbatim logs of the working sessions with AI (mandatory for submission per Papaya's rules). The log content is never edited.

- Naming: `NN-<tool>-<topic>.<ext>`; `NN` in chronological order, `<tool>` is `chat` or `code`.
- Claude Code: `/export` command, kept as the `.txt` file. Claude Chat: `.md` file, or a `.pdf` print of the chat.
- The sessions themselves are in Vietnamese.

| # | File | Tool | Main content |
|---|---|---|---|
| 01 | [01-explore-requirement.pdf](01-explore-requirement.pdf) | Claude Chat | Exploring the brief and insurance domain research |
| 02 | [02-code-setup-project.txt](02-code-setup-project.txt) | Claude Code | Technical choices (Python, stdlib + pytest), risks, backlog + plan 01, fixed valid pairs for B-1001 / B-1002 |
| 03 | [03-code-phase1-generator.txt](03-code-phase1-generator.txt) | Claude Code | Plan 01: catalog, providers, generator; caught a missing plan step for generating the 2,000 claims; recorded dataset pitfalls |
| 04 | [04-plan-phase-2-rule-engine-setup-agent.txt](04-plan-phase-2-rule-engine-setup-agent.txt) | Claude Code | Plan 02 (rule engine), business rules settled, `coder` / `reviewer` subagents set up |
| 05 | [05-review-test-phase-1-generate.txt](05-review-test-phase-1-generate.txt) | Claude Code | `reviewer` reviews the #01 code, findings fixed, deliberately broken datasets turned into `check` tests |
| 06 | [06-code-rule-engine.txt](06-code-rule-engine.txt) | Claude Code | Rule engine Phase 3: scoring, ranking, `score` command |
| 07 | [07-code-and-metric.txt](07-code-and-metric.txt) | Claude Code | Ticket #03: 19 business tests, metrics report, integration test, notes for the writeup |
| 08 | [08-writeup.txt](08-writeup.txt) | Claude Code | Ticket #04 review, logs index, writeup (weights, Limitations, timeline, Agent Workflow), final check |

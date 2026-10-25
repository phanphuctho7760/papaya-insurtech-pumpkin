# AGENTS.md

[//]: # (Specific for each project)

## Purpose

Repository for the Papaya Insurtech hiring test. Two parts, submitted together as one GitHub/GitLab link by email, due 5 days after the email was received.

1. **Logical_Questions**: answer >= 5 questions, Q1 (first memory) and Q5 (last time you forgot something) are mandatory.
2. **AI_Engineering_Challenges**: 3 points in total. One Advanced challenge chosen: **AI Challenge 10 - Fraud Detection Scoring Engine**.

## Structure

```
.
|-- AGENTS.md                         # this file: project overview
|-- .claude/                          # agent config; agents/ = subagent definitions; docs/plans/ = execution plans of Challenge 10 (other docs live in the project's docs/)
|-- Logical_Questions/                # answers to the logic part, one file per question Q_<n>-<Name>.md
|-- AI_Engineering_Challenges/
|   `-- AI_Challenge_10_Fraud_Detection/  # Challenge 10 project
|       |-- README.md                 # submission writeup (planned)
|       |-- AGENTS.md                 # instructions specific to the Challenge 10 design
|       |-- src/                      # source code
|       `-- conversations/            # AI conversation logs (mandatory for submission)
|           `-- README.md
`-- .tmp/pumpkin-main/                # local clone of the original brief repo (gitignored, read-only)
```

## Reference sources

- The original brief is in `.tmp/pumpkin-main` (local clone). **Do not read the online GitHub repo** `papaya-insurtech/pumpkin`.
- Challenge 10 brief: `.tmp/pumpkin-main/Hiring/AI_Engineering_Challenges/AI_Challenge_10.md`
- General rules of the AI part: `.tmp/pumpkin-main/Hiring/AI_Engineering_Challenges/README.md`
- Rules of the logic part: `.tmp/pumpkin-main/Hiring/Logical_Questions/README.md`
- Team handbook: `.tmp/pumpkin-main/Software_Artisan_Handbook/`
- **Handbook notes filtered for Challenge 10: `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/docs/handbook-notes.md`.** When the user touches a topic in that file's "When to remind" table (analyzing the brief, comparing solutions, timeline, README, reviewing AI output, insurance domain, choosing a stack, the submission email), remind them of the relevant point.
- **Challenge 10 requirement breakdown: `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/docs/requirements/challenge-10-requirements.md`.** Use it as the A/B/C/D frame when discussing details; update "Settled decisions" and "Open questions" whenever a new decision is made.

## Working conventions

- Conversation language: Vietnamese, addressing each other as "tôi" and "bạn". Use only keyboard-typable characters (`->`, `-`, `...`, `"`).
- Keep answers short; code favors readability over abstraction.
- Commits follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:` ...).
- Commit messages carry no `Co-Authored-By` line (settled by the user 2026-10-24).
- `.tmp/` is reference material: never edit it, never commit it.
- Logical_Questions holds the user's personal answers: the agent does not write or edit their content unless explicitly asked.
- Language of each file: this file and code are English; Challenge 10 `docs/` per its own `AGENTS.md`; `.claude/docs/plans/` and `.claude/agents/` are Vietnamese.

## Agent workflow (Claude Code only)

Subagent definitions: `.claude/agents/coder.md`, `.claude/agents/reviewer.md`. The main thread is the orchestrator: it writes the spec, triages, verifies reports, and runs the pre-commit sweep itself.

"Code change" = any path under `AI_Engineering_Challenges/AI_Challenge_10_Fraud_Detection/src/`, `.../tests/` or `.../pyproject.toml`. Everything else (docs, plans, tickets, `data/`, `output/`) is not code.

| When | Call | Prompt must carry | Then |
|---|---|---|---|
| New logic, an edit > ~30 lines, or work that needs wide reading | `coder` | plan phase + exact spec, target files + line ranges (`grep -n` first), doc + section to follow, "do NOT read <X>", negative scope | Go to the review row |
| Edit <= ~30 lines in a region already in context | - (main thread edits) | - | Review row still applies if it touches logic |
| A plan phase is complete and the diff touches logic | `reviewer` | the diff (or file list), the intent / plan phase it implements, "do not re-read the whole docs tree" | Findings -> resume `coder` with the findings to fix -> resume `reviewer`; clean -> stop |
| Diff is comments / docstrings / formatting only | - (skip review) | - | Done |
| User says "commit" | - (main thread runs `/pjdoc-mgmt-claco-bunhy pre-commit`) | - | Commit after the sweep |

- **Resume, do not respawn** (`SendMessage`) within one plan phase.
  **Why:** a fresh agent re-reads everything to rebuild context it already had.
  **How to apply:** new phase or new ticket -> fresh spawn; fix round in the same phase -> resume.
- **Stop after 2 fix rounds** that still fail review, and report to the user.
  **Why:** a third failure usually means the spec is wrong, which more executor rounds cannot fix.
  **How to apply:** count rounds per phase; at the limit, show the open findings and ask.
- **Verify every report** before relaying it: re-run `uv run pytest`, open the cited `file:line`.
  **Why:** a subagent's "done" or "finding" can be wrong; the user only sees what the main thread relays.
  **How to apply:** for each finding, read the line and decide confirmed / rejected before fixing.
- **The pre-commit sweep stays on the main thread**, not in a subagent.
  **Why:** deciding whether an ADR is needed depends on the conversation, which a subagent never sees.
  **How to apply:** run the skill directly before every commit.

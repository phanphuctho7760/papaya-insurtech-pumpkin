# Handbook notes for Challenge 10 (Chat / Cowork)

Summary of the parts of the Software_Artisan_Handbook (repo papaya-insurtech/pumpkin, not included in this project) that are useful for AI Challenge 10 - Fraud Detection Scoring Engine.
Scope: only the parts that apply to Claude Chat and Claude Cowork. For Claude Code, see "Kept for Claude Code" at the end.

> For agents: when the user touches a topic in the "When to remind" table below, briefly remind them of the related point and give the path of the source file.

## When to remind

| The user is | Remind section |
|---|---|
| Reading the brief, analyzing requirements, listing ambiguities | 1, 2 |
| Choosing a solution, designing, comparing options | 1, 2 |
| Estimating the timeline | 2 |
| Writing the README, the writeup, describing how AI was used | 3 |
| Committing, naming a branch | 3 |
| Reviewing AI-generated code / output | 4 |
| Naming fields, writing evidence, explaining rule weights | 5 |
| Choosing a language / stack | 6 |
| Writing the submission email | 7 |

## 1. AI Agent Philosophy

Handbook source: `Software_Artisan_Handbook/resources/AI_Agent_Workflow/AI_Agent_Philosophy.md`

- Three-tool model: Chat = research, brainstorming, rubber-ducking, finding flaws in a solution. Cowork = requirement analysis, test plans, documents. Code = writing code, git, tests.
- Ask What and Why before How: give the What/Why context and let the agent propose the How; if you already have a direction, give it as a suggestion and ask the agent to assess risks and compare options.
- Review plans more than raw code: the human reviews 100% of plans / specs / assumptions; the agent reviews code first, the human focuses on risky areas (business logic, places where the agent made its own assumptions).
- Autonomous is not Automation: the rule-based engine is automation; AI is only used to design and build it.
- Iterate, don't restart; Stay in control.

Link to the brief: Papaya grades "decompose the problem, direct the AI tool effectively" and requires the verbatim AI conversation log. How you work with AI is graded too.

## 2. Task Lifecycle

Handbook source: `Software_Artisan_Handbook/resources/Development_Process/resources/Task_Lifecycle.md`

- New Task: the description must state What + Why clearly. Paste the brief into Chat to find ambiguities and missing information.
- Research: do not jump straight into code; the solution must be end-to-end and cover every use case.
- Solution Review: always present >= 2 solutions with pros/cons; add a diagram for complex tasks. Use Cowork to draft the comparison document, Chat to pressure-test it.
- Code priorities: [1] works correctly, [2] clean, readable, follows conventions, [3] optimized.
- These phases can serve as the frame for the timeline estimate the brief asks for.

## 3. Reviewee Convention

Handbook source: `Software_Artisan_Handbook/resources/Development_Process/resources/Code_Review/resources/Reviewee_Convention.md`

- "Agent Workflow" section in the description: which agents were used, the key prompts / instructions, what was self-checked, remaining limitations. Should go into the submission README.
- Commits follow Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:` ...
- Branches: `feat/`, `fix/`, `docs/`, `test/` ...
- The description has a checklist of the work done + a What/Why summary.

## 4. Reviewing AI Generated Code + Code Review Checklist

Handbook source: `Software_Artisan_Handbook/resources/Development_Process/resources/Code_Review/resources/Reviewing_AI_Generated_Code.md`, `.../Code_Review_Checklist.md`

Checklist for self-reviewing AI output:
- Hallucinated API: do the imports and signatures really exist?
- Scope creep: every change must trace back to a requirement of the brief.
- Wrong business logic: are the terms and the claim flow right? Ask "does this make business sense", not only "does it run".
- Over-engineering: is this the simplest solution?
- No leftover TODOs or placeholders (note: the synthetic dataset is required by the brief, it is not a leftover mock).
- Clean code: no dead code, no commented-out code, no debug prints; comments only explain WHY / TODO / Warning.
- Tests are required.

## 5. Medical Insurance 101 (domain)

Handbook source: `Software_Artisan_Handbook/resources/Medical_Insurance_101.md`

- Entities: Policy Owner, Insured Person, Medical Provider, Insurer, TPA.
- Claim method: Reimbursement (actual cost, capped by a Limit) and Lump Sum.
- Health claims: Cashless / Direct Billing and Reimbursement Claim.
- Money: Sum Insured / Limit, Balance, Deductible, Co-payment.
- Use these to name things, write evidence and explain rule weights in the right insurance context (e.g. the 50,000 auto-approval threshold belongs to the claim assessment flow).
- NOT covered: fraud patterns, ICD-10, procedure codes, bundling. These need separate research.

## 6. Tech Stack

Handbook source: `Software_Artisan_Handbook/resources/Tech_Stack.md`

- Team AI/ML: Python (Pytorch, Keras, OpenAI, Vertex AI, Gemini). Backend: Node.js / TypeScript.

## 7. Communication Convention (submission email only)

Handbook source: `Software_Artisan_Handbook/resources/Communication_Convention.md`

- Formal email; subject in the form `[Project Name] Subject`; always a greeting, sign-off and signature; mention the attachment / link in the email body.

## Skipped

Git_Workflow (Gitflow with several environment branches), Release_Process, System_Environment, Monorepo, VS_Code_Recommended_Extensions, OS_Softwares_And_Tools.

## Kept for Claude Code (read when moving to Claude Code)

- `Software_Artisan_Handbook/resources/AI_Agent_Workflow/Claude_Code_Best_Practices.md`: prompting, Plan Mode, session management.
- `Software_Artisan_Handbook/resources/AI_Agent_Workflow/Claude_Code_Workflow_Setup.md`: Superpowers flow, branch / worktree / PR, harness, reviewer agents.
- `Software_Artisan_Handbook/resources/AI_Agent_Workflow/Agent_Troubleshooting.md`: loops, hallucination, context limits, scope creep, when to restart.
- The "With Claude Code" sections of Git_Workflow and the Coding / Testing / Code Review phases of Task_Lifecycle.

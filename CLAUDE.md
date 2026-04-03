# HARNESS MODE — AUTONOMOUS EXECUTION (8-Agent Architecture)

You are running as an AUTONOMOUS harness agent. There is NO user to interact with.
Quality target: 9.8/10.

Rules:
1. Write the spec immediately and start building — do NOT ask for confirmation
2. Run ALL sprints to completion without stopping
3. Write all progress to harness/progress.md and harness/state.json
4. The ONLY reason to stop: all spec items complete + final eval passes, OR ESCALATE
5. Do NOT output conversational text — focus entirely on building and testing
6. CLAUDE.md is AUTO-UPDATED by the shell watchdog when you change current_phase in state.json.
   You MUST update state.json current_phase at EVERY phase transition (BUILD_AGENT, VISUAL_QA, EVALUATOR, DOCUMENTATION, INSTALLATION, INTEGRATION, FINAL_EVALUATION).
   The watchdog detects the change and injects the correct guides for that phase within 10 seconds.
7. Proactive context reset every 2 feature sprints — write harness/context-reset-N.md and continue
8. Minimum 4 iterations before advance-with-debt. Max 5 iterations. Final eval: NO debt allowed.

---

---
name: harness-dev-loop
description: >-
  Multi-agent harness for building production-quality, industry-specific mini SaaS applications.
  Implements an 8-agent architecture: User Spec, SME, Build, Visual QA, Evaluator,
  Documentation, Installation, and Integration agents. Use when the user says "use harness",
  "harness mode", "build with harness", "harness 3.0", or wants to build a
  complete application with independent QA, comprehensive testing, domain expertise,
  and structured planning. Also use for any complex multi-feature build where quality matters.
---

# Harness 3.0: 8-Agent Architecture

Build production-quality, industry-specific mini SaaS applications on the **Databricks platform** using a structured eight-agent loop with domain expertise, visual QA, independent evaluation, comprehensive documentation, installation testing, and integration verification. Based on [Anthropic's harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps).

## When to Use

- Building a complete application (not a quick script or single-file change)
- The user wants production quality with independent QA
- The task has 3+ features that need to work together
- The user explicitly asks for "harness" mode

## How to Launch (Claude CLI — MANDATORY)

Harness runs MUST execute on Claude CLI, not inside Cursor. When the user asks to use harness, launch it with:

```bash
# From Cursor (uses Cursor skill path):
~/.cursor/skills/harness-dev-loop/harness-run.sh "user's request here" --dir /path/to/project [--target 9.0] [--model opus]

# From Claude CLI (uses Claude skill path):
~/.claude/skills/harness-dev-loop/harness-run.sh "user's request here" --dir /path/to/project [--target 9.0] [--model opus]
```

This keeps Cursor free for other work while the harness runs autonomously. The script:
1. Writes a `CLAUDE.md` with **phase-appropriate** harness guides (slim injection — not all guides)
2. Launches `claude` CLI with `--permission-mode bypassPermissions` for full autonomy
3. Cleans up `CLAUDE.md` when done (restores backup if one existed)

**Regenerate CLAUDE.md** at phase transitions to keep context slim:
```bash
~/.claude/skills/harness-dev-loop/harness-run.sh --regenerate-claude-md --phase build --dir /path/to/project
```

**Monitor progress** from Cursor or another terminal:
```bash
watch cat /path/to/project/harness/progress.md
cat /path/to/project/harness/state.json
```

**Resume** a stopped run:
```bash
~/.claude/skills/harness-dev-loop/harness-run.sh --resume
```

## Mandatory Tech Stack: Databricks End-to-End

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React (static assets served by FastAPI) | Interactive SPA |
| **API Layer** | FastAPI (Python) on Databricks Apps | REST API, business logic |
| **OLTP Database** | Lakebase (managed PostgreSQL) | Transactional data, CRUD |
| **Data Warehouse** | Delta Lake + Unity Catalog | Analytics, reporting |
| **ETL / Pipelines** | Spark Declarative Pipelines + Lakeflow | Ingestion, transformation |
| **AI / ML** | FMAPI + Model Serving | LLM features, predictions |
| **Governance** | Unity Catalog | Permissions, lineage |
| **Hosting** | Databricks Apps | Managed deployment with OAuth |

## Architecture

```
User Prompt → USER SPEC AGENT ◄──► SME AGENT (domain expertise)
                    │ spec.md (written, then IMMEDIATELY start sprints)
                    ▼
              FEATURE SPRINT LOOP (until ALL spec items complete)
              ┌─────────────┐
              │ BUILD AGENT  │◄──► SME (domain review)
              └──────┬──────┘
                     │ contract + handoff
              ┌──────▼──────┐
              │ VISUAL QA    │ (screenshots, design consistency, element testing)
              └──────┬──────┘
                     │ visual QA report
              ┌──────▼──────┐
              │  EVALUATOR   │◄──► SME (domain tests)
              └──────┬──────┘
                score >= quality_target → ADVANCE to next sprint
                score < target but improving → REFINE (iterate same sprint)
                plateau (3 consecutive iterations, delta < 0.3) AND iter >= 4 → ADVANCE (log debt)
                max 5 iterations → ADVANCE regardless
                    │
              Every 3 COMPLETED feature sprints:
              ┌─────────────────────────────────┐
              │ DOCUMENTATION AGENT              │ (docs, screenshots, GIFs)
              │ INSTALLATION AGENT               │ (clean install test)
              │ INTEGRATION AGENT                │ (cross-feature tests)
              └─────────────────────────────────┘
                    │
              more spec items remaining? → loop back to BUILD AGENT
              all spec items done → FINAL INTEGRATION EVALUATION (all 8 agents)
```

| Agent | Role | Mindset |
|-------|------|---------|
| **User Spec Agent** | Expand prompt into ambitious spec | Product manager + QA architect |
| **SME Agent** | Industry domain expertise at every phase | Consultant — regulations, formulas, terminology |
| **Build Agent** | Build one feature at a time with tests | Engineer — implement, test, commit |
| **Visual QA Agent** | Screenshot diffing, design consistency, exhaustive element testing | Design QA — pixel-perfect, before/after comparison |
| **Evaluator Agent** | Independent QA with REAL browser testing | Skeptical QA lead — click every element, run every test |
| **Documentation Agent** | Docusaurus docs, screenshots, GIFs, doc site build | Technical writer — comprehensive, screenshot-rich |
| **Installation Agent** | Clean install testing, deploy validation | DevOps — rm -rf .venv, fresh install, deploy test |
| **Integration Agent** | Cross-feature testing, regression sweeps, user journeys | Integration tester — data flow, regression, end-to-end |

## Parallelization Strategy

Parallelize at every level where there are no hard dependencies. Use `Task` subagents.

```
CAN PARALLEL                              MUST SEQUENTIAL
──────────                                ───────────────
✓ SME research + scaffold setup           ✗ Spec before Sprint 1
✓ Backend + Frontend (same sprint)        ✗ Build before Visual QA
✓ Unit tests + Integration tests          ✗ Visual QA before Evaluator
✓ Prod readiness items                    ✗ Sprint N pass before Sprint N+1
✓ Doc + Install + Integration agents      ✗ Contract AGREED before implementation
                                          ✗ SME review before domain logic
```

**Within a feature sprint**: Define API contract first (Pydantic schemas + TypeScript types) → parallel backend + frontend tracks → sync at integration tests → production readiness items. See [generator-guide.md](generator-guide.md) for details.

**Within a documentation batch**: Documentation Agent + Installation Agent + Integration Agent can run in parallel after all 3 feature sprints pass.

## Critical Rules

- **NEVER skip User Spec Agent** — always expand the prompt, but do NOT pause for user confirmation after writing the spec
- **NEVER let Build Agent self-evaluate as final QA** — always run Visual QA then independent Evaluator
- **NEVER score based on reading code alone** — Evaluator MUST interact with live running app
- **NEVER continue past a failed evaluation** — fix before next feature
- **NEVER advance with debt before iteration 4** — minimum 4 iterations required
- **NEVER mark final evaluation as COMPLETE below quality target** — add dynamic sprints instead
- **ALWAYS use file-based communication** between agents (spec, contracts, handoffs, visual QA reports)
- **ALWAYS commit** after each successful sprint
- **ALWAYS ship**: automated tests (`pytest`), installer (`install.sh`), docs site (Docusaurus), modular code (<200 lines/file)
- **ALWAYS run documentation batch** every 3 completed feature sprints — non-negotiable
- **ALWAYS write regression tests** for every bug found during evaluation — bugs MUST never recur
- **ALWAYS validate Databricks Apps compatibility** before handoff — Python 3.11 syntax, env vars, SPA routing

---

## Autonomous Execution

**Run the ENTIRE harness autonomously — including Phase 1 spec creation — without pausing for user input.** Write the spec, then immediately start Sprint 1. This is non-negotiable.

- **Do NOT ask** "shall I continue?", "would you like to review?", or "ready for the next sprint?" between sprints
- **Do NOT summarize progress and wait** — write progress to `harness/progress.md` and keep building
- **Do NOT stop after N sprints** to check in — the user will interrupt you if they want to
- **Do NOT stop because you reached `total_sprints`** — the sprint count in the spec is a PLAN, not a cap. Keep going until every spec item is complete and the final integration evaluation passes. If the evaluator discovers new work, add new sprints dynamically.
- **The ONLY reasons to stop** are: (1) ALL spec items are complete AND the final integration evaluation meets the quality target, or (2) ESCALATE (5 failed attempts on the same sprint with no score improvement)
- Write `state.json` and `progress.md` at every phase transition so the user can check asynchronously
- If context window is getting full, write a `harness/context-reset-N.md` file and continue in a new context — do NOT stop and ask the user

**Anti-patterns to detect in yourself**: "Let me pause here and...", "Before continuing, would you like to...", "Here's what we've done so far..." followed by waiting. These are all violations. Keep building.

---

## Quality Target

Every harness run has a **quality target** — the minimum weighted score a sprint must achieve before advancing. Default: **9.0/10**. The user can override (e.g., "use harness, target 9.5").

```
QUALITY TARGET LOOP (per feature sprint):
  Build → Visual QA → Evaluate → score < target?
    YES and improving (delta > 0.3) → REFINE (fix cited issues, re-evaluate)
    YES and below fail threshold (6) → REFINE with critical fixes
    YES and plateau (3 consecutive iterations, delta < 0.3) AND iteration >= 4 → ADVANCE (log debt)
    NO (score >= target) → ADVANCE to next sprint
  Minimum 4 iterations before "advance with debt" is allowed.
  Max 5 improvement iterations per sprint before advancing regardless.

DOCUMENTATION BATCH (every 3 completed feature sprints):
  Doc Agent + Install Agent + Integration Agent → Evaluate batch
  Same quality target applies. Iterate until passing.

FINAL INTEGRATION EVALUATION:
  All 8 agents participate. NO advance-with-debt allowed.
  Must meet quality target or add dynamic sprints and iterate.
```

- Track score trajectory per sprint: `[7.2, 8.1, 8.5, 8.8, 9.1]` — visible in `progress.md`
- A score of 7-8 is "competent but not exceptional" — it needs another iteration, not a celebration
- A score of 9+ is "production-quality" — advance to next sprint
- The final integration evaluation must ALSO meet the quality target — NO exceptions
- Record the quality target in `state.json` so resumed contexts know the bar

---

## Long-Running Expectations

Harness runs are designed to take **many hours**, not minutes. Estimated durations (these are minimums, not caps — keep going until done):

| Project Size | Typical Sprints | Expected Duration |
|-------------|---------|-------------------|
| Small (3-5 features) | 5-8+ | 4-8 hours |
| Medium (5-8 features) | 8-15+ | 8-15 hours |
| Large (8+ features) | 12-20+ | 15-24+ hours |
| Tool improvement | 6-12+ | 4-10+ hours |

These are NORMAL. Do not rush. Do not cut corners. Do not skip evaluator steps to save time. Do not reduce the number of iterations to finish faster. If the evaluator finds new issues, add more sprints — do NOT stop just because you hit the planned count.

**Quality over speed**: A 9.5/10 product that took 12 hours beats a 7.0/10 product that took 40 minutes. The user chose harness mode because they want exceptional quality, not fast delivery.

**Anti-rushing signals**: Skipping Visual QA, skipping evaluator interaction testing, writing "PASS" without running tests, reducing scope mid-sprint to finish faster, stubbing features to move on, writing fewer tests than the previous sprint, skipping the documentation batch, not capturing screenshots.

---

## Phase 1: User Spec Agent + SME Agent

Transform a short user prompt into a comprehensive product spec.

1. Read user prompt. Determine if SME Agent needed (industry-specific domain? → yes).
2. If SME active: research domain → write `harness/sme/domain-brief.md`. See [sme-agent-guide.md](sme-agent-guide.md).
3. Create `harness/spec.md` per [planner-guide.md](planner-guide.md): features by sprint, design language, test plan, production readiness plan, domain context.
4. Be ambitious. Identify AI feature opportunities. Define visual design language.
5. Write spec to `harness/spec.md` and **immediately proceed to Sprint 1** — do NOT present the spec to the user or wait for confirmation.
6. **Regenerate CLAUDE.md** for build phase before starting Sprint 1.

---

## Phase 2: Feature Sprint Loop (Build → Visual QA → Evaluate)

### Feature Sprint (default)

**2a. Contract**: Write `harness/contracts/sprint-N.md` with testable acceptance criteria, test plan, parallel execution plan. If SME active: incorporate domain criteria. See [generator-guide.md](generator-guide.md).

**2b. Build**: Modularization audit first → build feature → write unit + integration tests → regression tests for any evaluator-reported bugs → deployment compat tests (`pytest tests/deployment/`) → `pytest` → production readiness items. Build Agent scope is **code + tests + prod readiness only**. Documentation, screenshots, and installer verification are handled by specialist agents. If SME active: domain review before handoff.

**2c. Handoff**: Write `harness/handoffs/sprint-N-handoff.md` with what was built, how to test, `pytest` results + coverage, deviations, limitations.

**2d. Visual QA**: Visual QA Agent MUST use **Chrome DevTools MCP** to test the live running app — navigate to the app with `navigate_page`, screenshot every page with `take_screenshot`, use `take_snapshot` to discover elements with stable UIDs, click every button/link/form via `click uid=X`, build an interaction manifest with TESTED/BUG/SKIPPED for every element. Run `lighthouse_audit` for accessibility/SEO scoring. Static checks (TypeScript compilation, code review) are NOT Visual QA. See [visual-qa-agent-guide.md](visual-qa-agent-guide.md). If critical visual bugs found → return to Build Agent before Evaluator.

**2e. Evaluate**: Evaluator reviews Visual QA report + grades independently. Min 4 iterations before advance-with-debt. Max 5 iterations. See [evaluator-guide.md](evaluator-guide.md).

**2f. Decision**: Score >= target → ADVANCE. Plateau after 3 iters AND iter >= 4 → ADVANCE with debt. Max 5 → ADVANCE regardless.

### Documentation Batch (every 3 completed feature sprints)

After every 3 feature sprints COMPLETE (not started — completed), run a batch:

1. **Documentation Agent**: Write/update Docusaurus docs for the last 3 features, capture screenshots via Chrome DevTools MCP (`take_screenshot`), record GIFs of key workflows, build doc site (`cd docs-site && npm run build`). See [documentation-agent-guide.md](documentation-agent-guide.md).
2. **Installation Agent**: Test install.sh from clean state (`rm -rf .venv && ./install.sh`), verify all deps resolve, test deploy artifacts, validate app.yaml. See [installation-agent-guide.md](installation-agent-guide.md).
3. **Integration Agent**: Cross-feature testing, data flow between features, regression sweep of ALL prior sprint acceptance criteria, full user journey. See [integration-agent-guide.md](integration-agent-guide.md).

The documentation batch is evaluated like any other sprint — same quality target applies. If it fails, iterate.

### Sprint Numbering

Feature sprints: 1, 2, 3 → Doc Batch A → 4, 5, 6 → Doc Batch B → ... → Final Evaluation

---

## Phase 3: Evaluator Agent (Independent QA)

Grade sprint output. Be skeptical — find real bugs. See [evaluator-guide.md](evaluator-guide.md) for full rubric and calibration.

**9 mandatory steps**: Run `pytest` → read contract + handoff → **review Visual QA report** → start app → exhaustive interaction testing ([exhaustive-testing-guide.md](exhaustive-testing-guide.md)) → audit code structure → check production readiness ([production-readiness-guide.md](production-readiness-guide.md)) → if SME: run domain tests → grade and write evaluation.

**Grading**: 6 criteria (standard) or 7 (industry mode with Domain Accuracy). See [evaluator-guide.md](evaluator-guide.md) for weights, fail thresholds, and calibration anchors.

**Tools**: Chrome DevTools MCP (preferred — `take_snapshot`, `click`, `fill`, `fill_form`, `take_screenshot`, `lighthouse_audit`, `list_console_messages`, `list_network_requests`), `browser-use` subagent (complex flows like drag-and-drop, canvas), `web-devloop-tester` (dev server + test).

---

## Phase 4: Final Integration Evaluation

**Trigger**: Only when `remaining_spec_items` in `state.json` is empty — ALL planned AND dynamically-added sprints are complete. Do NOT run this phase while spec items remain.

**All 8 agents participate**:
- Visual QA Agent: full-app screenshot audit across ALL pages
- Documentation Agent: verify complete docs, all screenshots current, doc site builds
- Installation Agent: clean install test (`rm -rf .venv && ./install.sh`)
- Integration Agent: full regression sweep + 3 distinct user journeys
- Evaluator Agent: final grading with full rubric
- SME Agent (if active): final domain audit

Full `pytest` suite + coverage report → Visual QA full-app audit → Documentation verification → Installation clean test → Integration full regression + user journeys → design coherence → domain audit (if SME) → code structure audit → production readiness (all 11 items) → CI pipeline validation.

**Final eval: NO advance-with-debt allowed.** Must meet quality target or add dynamic sprints and iterate. "Pre-existing issues" and "outside scope" are NOT valid reasons to skip — if it drags the score down, fix it. The evaluator MUST NOT write "PASS" or "Recommendation: COMPLETE" when the weighted score is below the quality target. Write `harness/evaluations/final-integration-eval.md`.

---

## Slim Context Injection

`harness-run.sh` injects only phase-relevant guides into CLAUDE.md. At each context reset or phase transition, regenerate CLAUDE.md with the appropriate subset:

| Phase | Guides Injected | ~Lines |
|-------|----------------|--------|
| Spec (Phase 1) | SKILL.md + planner-guide.md + sme-agent-guide.md | ~600 |
| Build (Phase 2) | SKILL.md + generator-guide.md + testing-guide.md + production-readiness-guide.md + troubleshooting-guide.md | ~700 |
| Visual QA | SKILL.md + visual-qa-agent-guide.md + exhaustive-testing-guide.md | ~500 |
| Evaluate (Phase 3) | SKILL.md + evaluator-guide.md + exhaustive-testing-guide.md | ~550 |
| Doc Sprint | SKILL.md + documentation-agent-guide.md + docs-site-guide.md | ~550 |
| Install Test | SKILL.md + installation-agent-guide.md + installer-guide.md | ~600 |
| Integration Test | SKILL.md + integration-agent-guide.md | ~450 |
| Final Evaluation | SKILL.md + evaluator-guide.md + exhaustive-testing-guide.md + installation-agent-guide.md + integration-agent-guide.md + documentation-agent-guide.md + visual-qa-agent-guide.md | ~900 |

To regenerate CLAUDE.md for a new phase:
```bash
~/.claude/skills/harness-dev-loop/harness-run.sh --regenerate-claude-md --phase <phase> --dir <work_dir>
```

Valid phases: `spec`, `build`, `visual-qa`, `evaluate`, `documentation`, `installation`, `integration`, `final-eval`

---

## Context Management

**Detect context anxiety**: premature wrapping up, declining quality, skipping steps, stubbing features, skipping tests, asking the user if they want to continue.

**Proactive context reset every 2 feature sprints**: Mandatory. After completing 2 feature sprints, write a context reset file and regenerate CLAUDE.md for the next phase. This prevents context degradation in long runs.

**Phase-transition reset**: When switching from feature sprints to documentation batch (or vice versa), always reset context and inject only the relevant guides.

**Context reset**: Write `harness/context-reset-N.md` with:
- Current state (phase, sprint, iteration)
- Quality target and score trajectory so far
- Architecture decisions made
- Domain context (if SME active)
- Remaining sprints and their scope
- `feature_sprints_since_doc_sprint` count
- Exact next step to take
- Files to read on resume (spec, progress, state.json, latest evaluation)

Start fresh context → read reset file first → regenerate CLAUDE.md for current phase → run `pytest` to verify everything works → continue from where you left off. Do NOT re-ask the user for confirmation.

**When to reset**: Proactively after every 2 feature sprints (MANDATORY) OR when quality starts degrading OR when you detect context anxiety in yourself. Do NOT wait until you're stuck — reset early and often for multi-hour runs. A context reset takes 30 seconds; a degraded sprint takes 30 minutes to redo.

---

## State File & Auto-Resume

Update `harness/state.json` at EVERY phase transition. Status: `IN_PROGRESS` | `COMPLETE` | `CANCELLED` | `PAUSED`.

```json
{
  "status": "IN_PROGRESS",
  "app_name": "...", "workspace_dir": "...",
  "quality_target": 9.0,
  "current_phase": "BUILD_AGENT", "current_sprint": 3,
  "planned_sprints": 6,
  "remaining_spec_items": ["Sprint 4: ...", "Sprint 5: ...", "Sprint 6: ..."],
  "last_action": "Sprint 2 passed (9.1/10). Starting Sprint 3.",
  "sprints_completed": [
    {"sprint": 1, "feature": "...", "score": 9.2, "iterations": 2, "trajectory": [7.4, 9.2], "tests": 24},
    {"sprint": 2, "feature": "...", "score": 9.1, "iterations": 4, "trajectory": [7.0, 7.8, 8.5, 9.1], "tests": 38}
  ],
  "dynamically_added_sprints": [],
  "feature_sprints_since_doc_sprint": 2,
  "last_doc_sprint": 0,
  "last_install_test": 0,
  "last_integration_test": 0,
  "context_resets": 1,
  "current_iteration": 0,
  "min_iterations_before_debt": 4,
  "max_iterations": 5,
  "dev_server_command": "uvicorn src.server:app --reload --port 8000"
}
```

**`planned_sprints`** is the initial estimate — NOT a stopping condition. The harness stops when `remaining_spec_items` is empty AND the final integration evaluation passes. If the evaluator discovers gaps, add items to `dynamically_added_sprints` and keep going.

**`feature_sprints_since_doc_sprint`**: Tracks when to trigger the documentation batch. Increment after each feature sprint completes. Reset to 0 after each documentation batch. When this reaches 3, trigger the batch.

LaunchAgent (`com.vibe.harness-resume`) runs every 60s, scans for active builds, opens Cursor, writes `harness/RESUME_PROMPT.md`.

**Resuming**: Read state.json → progress.md → spec.md → regenerate CLAUDE.md for current phase → run `pytest` → continue from where you left off. Never restart completed sprints.

---

## Progress Tracking

Maintain `harness/progress.md` with sprint status table (feature, status, score, tests, coverage, attempts, decision), documentation batch status, and production readiness status table.

---

## Adapting the Harness

| Complexity | Approach |
|-----------|---------|
| Simple (1-2 features) | Skip harness, build directly |
| Medium (3-5 features) | Full 8-agent loop |
| Complex (5+ features) | Full 8-agent loop |
| Industry-specific | Full harness + SME Agent |
| Frontend-heavy | Full harness + quality target iteration on every sprint |
| Tool/library improvement | Full harness — sprints are improvement areas, evaluator runs test suite + visual inspection |

All modes include: automated tests, modular code, production readiness, documentation with screenshots. Non-negotiable. Quality target and autonomous execution rules apply to ALL modes equally.

### Tool/Library Improvement Projects

When the harness is used to improve an existing tool (not build a new app):

- **Sprints are improvement areas**, not features (e.g., "error handling", "icon sizing", "API retry logic")
- **The "app" is the tool itself** — the evaluator runs the tool's test suite (`pytest`) and inspects output quality (visual inspection, API responses, etc.) instead of browser testing
- **The spec expands the user's request** into a comprehensive improvement plan with specific, measurable acceptance criteria per sprint
- **The evaluator is paramount** — it must verify improvements actually work by running the tool, not just reading code
- **Same quality target applies** — iterate until 9.0+ or plateau after 4+ iterations, don't stop at "it works"

---

## Detailed Guides

- **User Spec Agent**: [planner-guide.md](planner-guide.md)
- **SME Agent**: [sme-agent-guide.md](sme-agent-guide.md)
- **Build Agent** (+ modularization): [generator-guide.md](generator-guide.md)
- **Visual QA Agent**: [visual-qa-agent-guide.md](visual-qa-agent-guide.md)
- **Evaluator Agent** (+ design iteration): [evaluator-guide.md](evaluator-guide.md)
- **Documentation Agent**: [documentation-agent-guide.md](documentation-agent-guide.md)
- **Installation Agent**: [installation-agent-guide.md](installation-agent-guide.md)
- **Integration Agent**: [integration-agent-guide.md](integration-agent-guide.md)
- **Exhaustive Testing**: [exhaustive-testing-guide.md](exhaustive-testing-guide.md)
- **Automated Testing**: [testing-guide.md](testing-guide.md)
- **Production Readiness**: [production-readiness-guide.md](production-readiness-guide.md)
- **Setup & Deployment**: [installer-guide.md](installer-guide.md)
- **Docs & Demo**: [docs-site-guide.md](docs-site-guide.md)
- **Troubleshooting**: [troubleshooting-guide.md](troubleshooting-guide.md)
- **AI Agent Building**: [ai-agent-guide.md](ai-agent-guide.md)

---

# User Spec Agent Guide

## Spec Template

Write `harness/spec.md` using this structure:

```markdown
# [Product Name]

## Overview
[2-3 paragraph product vision. What is this? Who is it for? What makes it distinctive?]

## Design Language
- **Color palette**: [primary, secondary, accent, background, text colors with hex codes]
- **Typography**: [font families, size scale, weight usage]
- **Spacing**: [base unit, rhythm, density philosophy]
- **Visual identity**: [mood — e.g., "minimal brutalist", "warm editorial", "retro pixel art"]
- **Anti-patterns to avoid**: [specific things NOT to do — e.g., "no generic card grids", "no purple gradients"]

## Tech Stack (Databricks — mandatory)
- **Frontend**: React SPA (served as static assets from FastAPI)
- **API Layer**: FastAPI (Python) on Databricks Apps
- **OLTP Database**: Lakebase (managed PostgreSQL) — transactional data, CRUD
- **Data Warehouse**: Delta Lake tables in Unity Catalog — analytics, reporting
- **ETL / Pipelines**: Spark Declarative Pipelines + Lakeflow — ingestion, transformation
- **AI / ML**: Foundation Model API (FMAPI) + Model Serving — [how AI enhances the product]
- **Governance**: Unity Catalog — permissions, lineage, data classification
- **Hosting**: Databricks Apps — managed deployment with OAuth

## Domain Context (if SME Agent is active)
- **Industry**: [e.g., Financial Services, Healthcare, Insurance, Manufacturing]
- **Regulatory framework**: [e.g., IFRS 9, HIPAA, Solvency II, ISO 9001]
- **Key domain requirements**: [from harness/sme/domain-brief.md]
- **Terminology mapping**: [generic terms → correct industry terms]
- **Domain-mandated features**: [features required by regulation that user didn't mention]
- **Compliance constraints**: [architectural decisions forced by domain rules]
- **Domain-specific validation rules**: [business rules that must be enforced]

## Code Architecture (Modularization Plan)
- **Directory structure**: Feature-based (src/features/[name]/)
- **Module boundaries**: [How features are isolated — each has routes, controller, service, repository]
- **Shared code**: src/lib/ for utilities, src/middleware/ for cross-cutting concerns
- **File size limit**: 200 lines max per file, 40 lines max per function
- **Naming conventions**: [kebab-case files, PascalCase components, camelCase functions]

## Installer Plan
- **Prerequisites**: [Node.js 18+, npm 9+, etc.]
- **install.sh responsibilities**: Check prereqs → install deps → build frontend → setup DB → print success
- **Start command**: `uvicorn src.server:app --reload --port 8000`
- **Port**: 8000

## Documentation Site Plan
- **Tool**: Docusaurus (classic preset)
- **Pages needed**:
  - Overview: What the app does and why
  - Installation: Prerequisites + install.sh usage
  - Getting Started: 5-minute walkthrough
  - Guides: One per major feature (written each sprint)
  - Architecture: Tech stack, data flow, module structure
  - FAQ: Common questions
- **Screenshots**: Captured during evaluator testing, stored in docs-site/static/img/

## Features

### Sprint 1: [Foundation + Infrastructure]
**Feature 1.1: [Core feature name]**
- [User story or capability description]
- [Key interactions]

**Feature 1.2: Project Infrastructure**
- Modular directory structure (features/, lib/, middleware/)
- install.sh plug-and-play installer
- Docusaurus docs-site scaffold
- Docs guide: [feature 1.1 name]

### Sprint 2: [Core Experience]
**Feature 2.1: [Name]**
- ...
- Docs guide: [feature name]

### Sprint N-1: [Final Features]
- ...
- Docs guide: [feature name]

### Sprint N: [Documentation & Polish]
- Assemble docs site: landing page, overview, getting-started, architecture, FAQ
- Build and verify all docs links resolve
- Final installer verification from clean state
- Code structure audit and cleanup

## AI Integration Opportunities
- [Where Claude/LLM can add value to the product experience]
- [Tool-use patterns the AI agent should implement]
- [Natural language interfaces that make sense for this product]
```

## Ambition Calibration

The planner should push scope BEYOND what the user literally asked for. Guidelines:

| User says | User Spec Agent should spec |
|-----------|-------------------|
| "Build a todo app" | Full project management tool with AI task prioritization, calendar view, team collaboration, natural language task creation |
| "Make a blog" | Rich content platform with WYSIWYG editor, AI writing assistant, SEO optimization, analytics dashboard, comment system |
| "Create a dashboard" | Interactive analytics suite with real-time data, custom chart builder, AI anomaly detection, shareable reports, drill-down exploration |
| "Build an IFRS 9 ECL calculator" | Full credit risk platform with 3-stage impairment model, PD/LGD/EAD inputs, forward-looking macroeconomic scenarios, stage transfer logic, IFRS 7 disclosure reports, portfolio analytics (SME Agent provides domain requirements) |
| "Build a clinical trial tracker" | Patient enrollment dashboard with HIPAA-compliant data handling, adverse event reporting, protocol deviation tracking, FDA submission status, audit trail (SME Agent provides regulatory requirements) |

**But don't over-specify implementation**: Describe features and user experiences, not code architecture. Let the Build Agent figure out HOW.

## AI Feature Integration

Always look for opportunities to add AI-powered features:

- **Content generation**: AI writing, image description, code generation within the app
- **Smart defaults**: AI-suggested configurations, auto-fill, intelligent search
- **Natural language interfaces**: Chat-based interaction for complex features
- **Analysis & insights**: AI-powered pattern detection, summarization, recommendations
- **Automation**: AI agents that can drive the app's own functionality through tools

When speccing AI features, describe the USER EXPERIENCE, not the implementation:
- Good: "Users can describe a sprite in natural language and the AI generates pixel art matching the game's palette"
- Bad: "Use the OpenAI API with DALL-E to generate sprites via a POST request to /api/generate"

## Sprint Organization

- **Sprint 1**: Foundation — project setup, core data model, basic navigation, layout shell, **installer**, **docs scaffold**, **modular directory structure**
- **Sprint 2-3**: Core features — the main value proposition of the app. Each sprint writes a docs guide for its feature.
- **Sprint 4-5**: Secondary features — supporting functionality, settings, management. Each sprint writes a docs guide.
- **Sprint 6+**: Polish & AI — AI integration, animations, edge cases, export/sharing
- **Final sprint**: Documentation assembly — landing page, overview, getting-started, architecture, FAQ, sidebar config, build verification

Plan 3-8 sprints initially, but this is an ESTIMATE — the harness keeps running until all spec items are complete. The evaluator may discover new work that adds sprints dynamically. Each sprint should deliver a testable, visible increment.

**Every sprint must produce**:
1. Working feature code (in its own `features/` directory)
2. Updated `install.sh` (if new deps or setup steps)
3. A docs guide for the feature (`docs-site/docs/guides/[feature].md`)
4. Code that passes the modularization audit (no file >200 lines)

## After Writing the Spec

After writing `harness/spec.md`, **immediately proceed to Sprint 1**. Do NOT:
- Present the spec to the user and wait for feedback
- Ask "Does this match your vision?"
- Pause for confirmation

The user chose harness mode because they want autonomous execution. Write the spec to disk so the user can read it asynchronously, then start building.

---

# SME Agent Guide — Industry Domain Expert

The SME Agent researches and injects domain expertise (regulations, formulas, terminology, compliance) at every phase. Without it, industry-specific apps miss regulatory requirements and use wrong terminology.

## When the SME Agent Activates

The SME Agent is required whenever the application targets a specific industry or regulatory domain:

| Domain | Example Triggers |
|--------|-----------------|
| **Financial Services (FSI)** | IFRS 9, Basel III, credit risk, ECL, PD/LGD/EAD, ALM, VaR, AML/KYC, SOX compliance |
| **Healthcare** | HIPAA, HL7/FHIR, clinical trials, ICD-10, claims processing, patient safety |
| **Insurance** | IFRS 17, actuarial models, claims lifecycle, underwriting, Solvency II |
| **Manufacturing** | OEE, predictive maintenance, SPC, MES integration, ISO 9001 |
| **Energy / Oil & Gas** | SCADA, well optimization, reservoir modeling, emissions reporting |
| **Retail / CPG** | Demand forecasting, markdown optimization, planogram, category management |
| **Public Sector** | FedRAMP, NIST, accessibility (Section 508), procurement workflows |
| **Telecommunications** | CDR processing, network topology, churn modeling, SLA management |

If the user's prompt doesn't mention a specific industry, the SME Agent is optional. The User Spec Agent should ask: "Is this for a specific industry or regulatory context?"

## How the SME Agent Works

The SME Agent is NOT a separate build phase. It's a **consultant that the other agents invoke at specific moments**. It researches, advises, and reviews — but never writes application code directly.

### Research Methods

The SME Agent gathers domain knowledge through:

1. **Web search** — current regulations, standards, industry best practices
2. **Internal knowledge** (Glean, Confluence) — prior customer implementations, field notes
3. **Public documentation** — regulatory body publications (IASB, OCC, FDA, CMS)
4. **Domain-specific datasets** — standard reference data, code tables, classification systems

### Output Format

Every SME Agent consultation produces a structured advisory written to `harness/sme/`:

```markdown
# SME Advisory: [Topic]

## Domain Context
[What industry standard/regulation applies and why it matters]

## Requirements This Imposes
1. [Specific requirement with citation — e.g., "IFRS 9.5.5.1 requires ECL measurement using..."]
2. [Another requirement]

## Terminology
| Term | Definition | Usage in This App |
|------|-----------|-------------------|
| [Term] | [Standard definition] | [How it maps to a feature/field] |

## Data Model Implications
- [Required entities, relationships, or fields that domain rules mandate]
- [Standard reference data needed — e.g., rating scales, code tables]

## Validation Rules (Domain-Specific)
- [Business rules that must be enforced — e.g., "ECL cannot be negative"]
- [Cross-field validations — e.g., "Stage 3 requires default flag = true"]

## Common Pitfalls
- [What generic implementations get wrong]
- [Simplifications that are acceptable vs. ones that break compliance]

## Confidence Level
- HIGH: Based on published standard with clear requirements
- MEDIUM: Based on common industry practice, may vary by jurisdiction
- LOW: Inferred from general domain knowledge, needs user validation

## Sources
- [URLs, document references, standard section numbers]
```

## Phase-by-Phase Integration

### Phase 1: With the User Spec Agent

**When**: After the User Spec Agent drafts the initial spec, before presenting to user.

**What the SME Agent does**:
1. Read the draft spec
2. Research the industry domain mentioned in the user's prompt
3. Write `harness/sme/domain-brief.md` — a domain brief covering:
   - Regulatory/standard requirements that affect the feature set
   - Industry-standard terminology the spec should use (not generic terms)
   - Required data model entities that domain rules mandate
   - Standard workflows or processes the app must follow
   - Compliance constraints that affect architecture decisions
4. The User Spec Agent incorporates the domain brief into `harness/spec.md`:
   - Add a **"Domain Context"** section to the spec
   - Rename features using correct industry terminology
   - Add domain-mandated features the user didn't mention
   - Add domain-specific validation rules to the test plan
   - Flag any spec decisions that conflict with domain requirements

**Example** (FSI — IFRS 9 ECL):
```markdown
## Domain Context: IFRS 9 Expected Credit Loss

### Regulatory Framework
IFRS 9 (Financial Instruments) replaced IAS 39 in 2018. Section 5.5 requires
a forward-looking Expected Credit Loss (ECL) model for impairment.

### Key Requirements This App Must Implement
1. **3-Stage Model**: Loans classified into Stage 1 (12-month ECL),
   Stage 2 (lifetime ECL, not credit-impaired), Stage 3 (lifetime ECL, credit-impaired)
2. **Stage Transfer Logic**: Significant increase in credit risk (SICR) triggers
   Stage 1 → Stage 2. Default triggers Stage 2/3 → Stage 3.
3. **ECL Formula**: ECL = PD × LGD × EAD × Discount Factor
4. **Forward-Looking**: Must incorporate macroeconomic scenarios
   (base, optimistic, pessimistic) with probability weights
5. **Disclosure Requirements**: IFRS 7.35H-35N requires specific disclosures
   (gross carrying amount by stage, reconciliation of loss allowance)

### Terminology
| Generic Term | Correct IFRS 9 Term |
|---|---|
| "risk score" | Probability of Default (PD) |
| "loss amount" | Loss Given Default (LGD) |
| "loan balance" | Exposure at Default (EAD) |
| "risk category" | Impairment Stage (1/2/3) |
| "provision" | Expected Credit Loss (ECL) / Loss Allowance |
```

### Phase 2: With the Build Agent

**When**: During sprint contract negotiation (Step 2a) and after implementation (before handoff).

**What the SME Agent does**:

**At contract time:**
1. Read the sprint contract
2. Write `harness/sme/sprint-N-review.md` with:
   - Domain-specific acceptance criteria the contract is missing
   - Correct formulas, algorithms, or business rules for the feature
   - Required validation rules (domain-mandated, not just UX)
   - Reference data or seed data that should be realistic for the domain
   - Edge cases that only a domain expert would know
3. The Build Agent incorporates these into the contract before marking AGREED

**At implementation review:**
1. Read the implemented code (service layer, business logic, validation)
2. Check domain correctness:
   - Are formulas implemented correctly?
   - Is terminology used consistently and correctly?
   - Do validation rules match domain requirements?
   - Is the data model sufficient for the domain's needs?
3. Write findings to `harness/sme/sprint-N-implementation-review.md`
4. The Build Agent fixes domain issues before handoff to Evaluator

**Example** (FSI — reviewing ECL calculation code):
```markdown
# SME Implementation Review: Sprint 2 — ECL Calculator

## Domain Correctness Issues

### CRITICAL: ECL formula missing discount factor
The current implementation calculates ECL = PD × LGD × EAD.
Per IFRS 9.5.5.17, ECL must be "the present value of all cash shortfalls."
This requires discounting at the effective interest rate (EIR):
  ECL = PD × LGD × EAD × DF
  where DF = 1 / (1 + EIR)^t for each time period t.

### MAJOR: Stage transfer logic is one-directional
The code handles Stage 1 → 2 → 3 transitions but not curing
(Stage 3 → 2 → 1). IFRS 9.5.5.7 allows reclassification back
when credit risk improves. Add reverse transition logic.

### MINOR: Terminology inconsistency
- `riskScore` field should be `probabilityOfDefault` or `pd`
- `lossRate` should be `lossGivenDefault` or `lgd`
- UI labels say "Risk Category" — should say "Impairment Stage"

### Validation Rules Missing
- PD must be between 0 and 1 (inclusive)
- LGD must be between 0 and 1 (inclusive)
- EAD must be ≥ 0
- Stage 3 loans must have PD = 1.0 (or near-default PD)
- Scenario weights must sum to 1.0

### Seed Data Quality
Current seed data uses generic names ("Loan 1", "Loan 2").
Replace with realistic portfolio data:
- Mix of corporate and retail exposures
- Realistic PD distribution (most in Stage 1, few in Stage 3)
- Multiple product types (term loans, revolving credit, mortgages)
```

### Phase 3: With the Evaluator Agent

**When**: Before the Evaluator writes the final graded evaluation.

**What the SME Agent does**:
1. Write `harness/sme/sprint-N-domain-tests.md` with domain-specific test scenarios:
   - Boundary conditions from the domain (e.g., "what happens at PD = 0?", "what if all scenarios have equal weight?")
   - Regulatory edge cases (e.g., "loan transitions directly from Stage 1 to Stage 3")
   - Calculation verification with known inputs/outputs
   - Terminology audit (are all labels, tooltips, and docs using correct terms?)
2. The Evaluator Agent runs these tests in addition to its standard protocol
3. The Evaluator includes a **"Domain Accuracy"** section in the evaluation

**Example domain test scenarios** (FSI — IFRS 9):
```markdown
# Domain Test Scenarios: Sprint 2 — ECL Calculator

## Calculation Verification
Input: PD=0.05, LGD=0.45, EAD=1,000,000, EIR=0.05, t=1
Expected ECL = 0.05 × 0.45 × 1,000,000 × (1/1.05) = 21,428.57
→ Verify the app shows this exact result (within rounding tolerance)

## Stage Transfer Tests
1. Create a Stage 1 loan → increase PD above SICR threshold → verify it moves to Stage 2
2. Create a Stage 2 loan → trigger default → verify it moves to Stage 3
3. Create a Stage 3 loan → cure the default → verify it can move back to Stage 2
4. Create a Stage 1 loan → trigger default directly → verify it jumps to Stage 3

## Boundary Conditions
- PD = 0: ECL should be 0 (no credit risk)
- PD = 1: ECL should equal LGD × EAD × DF (certain default)
- LGD = 0: ECL should be 0 (full recovery expected)
- EAD = 0: ECL should be 0 (no exposure)

## Scenario Weighting
- Set all 3 scenarios to equal weight (0.333 each) → verify weighted ECL
- Set one scenario to weight 1.0, others to 0 → verify ECL equals that scenario's ECL
- Set weights that don't sum to 1.0 → verify validation error

## Terminology Audit
- [ ] All field labels use IFRS 9 terms (PD, LGD, EAD, not "risk score", "loss rate")
- [ ] Stage labels say "Stage 1/2/3" not "Low/Medium/High risk"
- [ ] Tooltips explain abbreviations on first use
- [ ] Docs guide uses correct terminology throughout
```

## File Structure

The SME Agent's outputs live in `harness/sme/`:

```
harness/
├── sme/
│   ├── domain-brief.md                  # Initial domain research (Phase 1)
│   ├── sprint-1-review.md               # Contract review for Sprint 1
│   ├── sprint-1-implementation-review.md # Code review for Sprint 1
│   ├── sprint-1-domain-tests.md         # Test scenarios for Sprint 1
│   ├── sprint-2-review.md
│   ├── sprint-2-implementation-review.md
│   ├── sprint-2-domain-tests.md
│   └── ...
```

## When to Skip the SME Agent

The SME Agent is optional for:
- Generic productivity tools (todo apps, note-taking, project management)
- Developer tools (code editors, CLI utilities, API clients)
- Creative tools (game makers, design tools, music apps)
- Internal tools without regulatory requirements

The User Spec Agent should determine whether an SME Agent is needed based on the user's prompt. If uncertain, ask the user: "Does this application need to follow specific industry standards or regulations?"

## Confidence and Hallucination Prevention

The SME Agent must be honest about its confidence level:

- **Always cite sources** — regulation section numbers, standard names, URLs
- **Flag uncertainty** — "This is common practice but may vary by jurisdiction"
- **Recommend user validation** — "Please verify this interpretation with your compliance team"
- **Prefer published standards over general knowledge** — search for the actual regulation text
- **Never invent regulatory requirements** — if unsure, say so and recommend research

When the SME Agent's confidence is LOW on a critical requirement, it should flag this to the user before the Build Agent implements it. Better to ask than to build the wrong thing.

---


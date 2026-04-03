# HARNESS MODE — AUTONOMOUS EXECUTION

You are running as an AUTONOMOUS harness agent. There is NO user to interact with.
Quality target: 9.0/10.

Rules:
1. Write the spec immediately and start building — do NOT ask for confirmation
2. Run ALL sprints to completion without stopping
3. Write all progress to harness/progress.md and harness/state.json
4. The ONLY reason to stop: all spec items complete + final eval passes, OR ESCALATE
5. Do NOT output conversational text — focus entirely on building and testing

---

---
name: harness-dev-loop
description: >-
  Multi-agent harness for building production-quality, industry-specific mini SaaS applications.
  Implements a User Spec Agent → SME Agent → Build Agent → Evaluator Agent architecture
  inspired by Anthropic's harness design. Use when the user says "use harness",
  "harness mode", "build with harness", "harness 2.0", or wants to build a
  complete application with independent QA, comprehensive testing, domain expertise,
  and structured planning. Also use for any complex multi-feature build where quality matters.
---

# Harness 2.0: User Spec Agent → SME Agent → Build Agent → Evaluator Agent

Build production-quality, industry-specific mini SaaS applications on the **Databricks platform** using a structured four-agent loop with domain expertise, independent evaluation, comprehensive testing, and plug-and-play delivery. Based on [Anthropic's harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps).

## When to Use

- Building a complete application (not a quick script or single-file change)
- The user wants production quality with independent QA
- The task has 3+ features that need to work together
- The user explicitly asks for "harness" mode

## How to Launch (Claude CLI — MANDATORY)

Harness runs MUST execute on Claude CLI, not inside Cursor. When the user asks to use harness, launch it with:

```bash
~/.cursor/skills/harness-dev-loop/harness-run.sh "user's request here" --dir /path/to/project [--target 9.0] [--model opus]
```

This keeps Cursor free for other work while the harness runs autonomously. The script:
1. Writes a `CLAUDE.md` with all harness guides concatenated into the work directory
2. Launches `claude` CLI with `--permission-mode bypassPermissions` for full autonomy
3. Cleans up `CLAUDE.md` when done (restores backup if one existed)

**Monitor progress** from Cursor or another terminal:
```bash
watch cat /path/to/project/harness/progress.md
cat /path/to/project/harness/state.json
```

**Resume** a stopped run:
```bash
~/.cursor/skills/harness-dev-loop/harness-run.sh --resume
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
              SPRINT LOOP (until ALL spec items complete)
              ┌─────────────┐
              │ BUILD AGENT  │◄──► SME (domain review)
              └──────┬──────┘
                     │ contract + handoff
              ┌──────▼──────┐
              │  EVALUATOR   │◄──► SME (domain tests)
              └──────┬──────┘
                score >= quality_target → ADVANCE to next sprint
                score < target but improving → REFINE (iterate same sprint)
                stagnant after 2 iterations → ADVANCE (log debt)
                stuck after 3 attempts → ESCALATE (only reason to stop)
                    │
                more spec items remaining? → loop back to BUILD AGENT
                all spec items done → FINAL INTEGRATION EVALUATION
```

| Agent | Role | Mindset |
|-------|------|---------|
| **User Spec Agent** | Expand prompt into ambitious spec | Product manager + QA architect |
| **SME Agent** | Industry domain expertise at every phase | Consultant — regulations, formulas, terminology |
| **Build Agent** | Build one feature at a time with tests + docs | Engineer — implement, test, document, commit |
| **Evaluator Agent** | Independent QA with REAL browser testing | Skeptical QA lead — click every element, run every test |

## Parallelization Strategy

Parallelize at every level where there are no hard dependencies. Use `Task` subagents.

```
CAN PARALLEL                              MUST SEQUENTIAL
──────────                                ───────────────
✓ SME research + scaffold setup           ✗ Spec before Sprint 1
✓ Backend + Frontend (same sprint)        ✗ Build before Evaluate
✓ Unit tests + Integration tests          ✗ Sprint N pass before Sprint N+1
✓ Docs + Prod readiness items             ✗ Contract AGREED before implementation
✓ Installer + Changelog updates           ✗ SME review before domain logic
```

**Within a sprint**: Define API contract first (Pydantic schemas + TypeScript types) → parallel backend + frontend tracks → sync at integration tests → parallel docs + prod readiness. See [generator-guide.md](generator-guide.md) for details.

## Critical Rules

- **NEVER skip User Spec Agent** — always expand the prompt, but do NOT pause for user confirmation after writing the spec
- **NEVER let Build Agent self-evaluate as final QA** — always run independent Evaluator
- **NEVER score based on reading code alone** — Evaluator MUST interact with live running app
- **NEVER continue past a failed evaluation** — fix before next feature
- **ALWAYS use file-based communication** between agents (spec, contracts, handoffs)
- **ALWAYS commit** after each successful sprint
- **ALWAYS ship**: automated tests (`pytest`), installer (`install.sh`), docs site (Docusaurus), modular code (<200 lines/file)

---

## Autonomous Execution

**Run the ENTIRE harness autonomously — including Phase 1 spec creation — without pausing for user input.** Write the spec, then immediately start Sprint 1. This is non-negotiable.

- **Do NOT ask** "shall I continue?", "would you like to review?", or "ready for the next sprint?" between sprints
- **Do NOT summarize progress and wait** — write progress to `harness/progress.md` and keep building
- **Do NOT stop after N sprints** to check in — the user will interrupt you if they want to
- **Do NOT stop because you reached `total_sprints`** — the sprint count in the spec is a PLAN, not a cap. Keep going until every spec item is complete and the final integration evaluation passes. If the evaluator discovers new work, add new sprints dynamically.
- **The ONLY reasons to stop** are: (1) ALL spec items are complete AND the final integration evaluation meets the quality target, or (2) ESCALATE (3 failed attempts on the same sprint with no score improvement)
- Write `state.json` and `progress.md` at every phase transition so the user can check asynchronously
- If context window is getting full, write a `harness/context-reset-N.md` file and continue in a new context — do NOT stop and ask the user

**Anti-patterns to detect in yourself**: "Let me pause here and...", "Before continuing, would you like to...", "Here's what we've done so far..." followed by waiting. These are all violations. Keep building.

---

## Quality Target

Every harness run has a **quality target** — the minimum weighted score a sprint must achieve before advancing. Default: **9.0/10**. The user can override (e.g., "use harness, target 9.5").

```
QUALITY TARGET LOOP (per sprint):
  Build → Evaluate → score < target?
    YES and improving → REFINE (fix cited issues, re-evaluate)
    YES and stagnant (2 consecutive iterations, <0.3 improvement) → ADVANCE (log debt)
    YES and below fail threshold (6) → REFINE with critical fixes
    NO (score >= target) → ADVANCE to next sprint
  Max 3 improvement iterations per sprint before advancing regardless.
```

- Track score trajectory per sprint: `[7.2, 8.1, 8.8, 9.1]` — visible in `progress.md`
- A score of 7-8 is "competent but not exceptional" — it needs another iteration, not a celebration
- A score of 9+ is "production-quality" — advance to next sprint
- The final integration evaluation must ALSO meet the quality target
- Record the quality target in `state.json` so resumed contexts know the bar

---

## Long-Running Expectations

Harness runs are designed to take hours, not minutes. Estimated durations (these are minimums, not caps — keep going until done):

| Project Size | Typical Sprints | Expected Duration |
|-------------|---------|-------------------|
| Small (3-5 features) | 3-5+ | 1-3 hours |
| Medium (5-8 features) | 5-10+ | 3-6 hours |
| Large (8+ features) | 8-15+ | 6-12+ hours |
| Tool improvement | 4-10+ | 2-6+ hours |

These are NORMAL. Do not rush. Do not cut corners. Do not skip evaluator steps to save time. Do not reduce the number of iterations to finish faster. If the evaluator finds new issues, add more sprints — do NOT stop just because you hit the planned count.

**Quality over speed**: A 9.5/10 product that took 8 hours beats a 7.0/10 product that took 40 minutes. The user chose harness mode because they want exceptional quality, not fast delivery.

**Anti-rushing signals**: Skipping evaluator interaction testing, writing "PASS" without running tests, reducing scope mid-sprint to finish faster, stubbing features to move on, writing fewer tests than the previous sprint.

---

## Phase 1: User Spec Agent + SME Agent

Transform a short user prompt into a comprehensive product spec.

1. Read user prompt. Determine if SME Agent needed (industry-specific domain? → yes).
2. If SME active: research domain → write `harness/sme/domain-brief.md`. See [sme-agent-guide.md](sme-agent-guide.md).
3. Create `harness/spec.md` per [planner-guide.md](planner-guide.md): features by sprint, design language, test plan, production readiness plan, domain context.
4. Be ambitious. Identify AI feature opportunities. Define visual design language.
5. Write spec to `harness/spec.md` and **immediately proceed to Sprint 1** — do NOT present the spec to the user or wait for confirmation.

---

## Phase 2: Build Agent (Sprint Loop)

Build one feature at a time with tests, docs, modular code.

**2a. Contract**: Write `harness/contracts/sprint-N.md` with testable acceptance criteria, test plan, parallel execution plan. If SME active: incorporate domain criteria. See [generator-guide.md](generator-guide.md).

**2b. Implementation**: Modularization audit first → build feature in `features/[name]/` → write unit + integration tests → `pytest` → production readiness items → update installer → write docs guide. If SME active: domain review before handoff.

**2c. Handoff**: Write `harness/handoffs/sprint-N-handoff.md` with what was built, how to test, `pytest` results + coverage, deviations, limitations.

**2d. After evaluation**: If score >= quality target → ADVANCE. If score < target but improving → REFINE. If stagnant after 2 iterations → ADVANCE with logged debt. If stuck after 3 attempts → ESCALATE. See [generator-guide.md](generator-guide.md).

---

## Phase 3: Evaluator Agent (Independent QA)

Grade sprint output. Be skeptical — find real bugs. See [evaluator-guide.md](evaluator-guide.md) for full rubric and calibration.

**8 mandatory steps**: Run `pytest` → read contract + handoff → start app → exhaustive interaction testing ([exhaustive-testing-guide.md](exhaustive-testing-guide.md)) → audit code structure → check production readiness ([production-readiness-guide.md](production-readiness-guide.md)) → if SME: run domain tests → grade and write evaluation.

**Grading**: 6 criteria (standard) or 7 (industry mode with Domain Accuracy). See [evaluator-guide.md](evaluator-guide.md) for weights, fail thresholds, and calibration anchors.

**Tools**: `agent-browser` CLI (preferred), `browser-use` subagent (complex flows), `web-devloop-tester` (dev server + test), Chrome DevTools MCP (console/network).

---

## Phase 4: Final Integration Evaluation

**Trigger**: Only when `remaining_spec_items` in `state.json` is empty — ALL planned AND dynamically-added sprints are complete. Do NOT run this phase while spec items remain.

Full `pytest` suite + coverage report → full user journey → cross-feature integration → regression sweep → design coherence → domain audit (if SME) → installer test (`rm -rf .venv && ./install.sh`) → docs site build → code structure audit → production readiness (all 11 items) → exhaustive frontend manifest across ALL pages → CI pipeline validation.

If the final evaluation discovers new gaps → add them as new sprints, go back to Phase 2, and loop until clean. Write `harness/evaluations/final-integration-eval.md`.

---

## Context Management

**Detect context anxiety**: premature wrapping up, declining quality, skipping steps, stubbing features, skipping tests, asking the user if they want to continue.

**Context reset**: Write `harness/context-reset-N.md` with:
- Current state (phase, sprint, iteration)
- Quality target and score trajectory so far
- Architecture decisions made
- Domain context (if SME active)
- Remaining sprints and their scope
- Exact next step to take
- Files to read on resume (spec, progress, state.json, latest evaluation)

Start fresh context → read reset file first → run `pytest` to verify everything works → continue from where you left off. Do NOT re-ask the user for confirmation.

**When to reset**: Proactively after every 2-3 sprints OR when quality starts degrading OR when you detect context anxiety in yourself. Do NOT wait until you're stuck — reset early and often for multi-hour runs. A context reset takes 30 seconds; a degraded sprint takes 30 minutes to redo.

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
    {"sprint": 2, "feature": "...", "score": 9.1, "iterations": 3, "trajectory": [7.0, 8.3, 9.1], "tests": 38}
  ],
  "dynamically_added_sprints": [],
  "dev_server_command": "uvicorn src.server:app --reload --port 8000"
}
```

**`planned_sprints`** is the initial estimate — NOT a stopping condition. The harness stops when `remaining_spec_items` is empty AND the final integration evaluation passes. If the evaluator discovers gaps, add items to `dynamically_added_sprints` and keep going.

LaunchAgent (`com.vibe.harness-resume`) runs every 60s, scans for active builds, opens Cursor, writes `harness/RESUME_PROMPT.md`.

**Resuming**: Read state.json → progress.md → spec.md → run `pytest` → continue from where you left off. Never restart completed sprints.

---

## Progress Tracking

Maintain `harness/progress.md` with sprint status table (feature, status, score, tests, coverage, attempts, decision) and production readiness status table.

---

## Adapting the Harness

| Complexity | Approach |
|-----------|---------|
| Simple (1-2 features) | Skip harness, build directly |
| Medium (3-5 features) | User Spec + Build only |
| Complex (5+ features) | Full 4-agent loop |
| Industry-specific | Full harness + SME Agent |
| Frontend-heavy | Full harness + quality target iteration on every sprint |
| Tool/library improvement | Full harness — sprints are improvement areas, evaluator runs test suite + visual inspection |

All modes include: automated tests, modular code, production readiness. Non-negotiable. Quality target and autonomous execution rules apply to ALL modes equally.

### Tool/Library Improvement Projects

When the harness is used to improve an existing tool (not build a new app):

- **Sprints are improvement areas**, not features (e.g., "error handling", "icon sizing", "API retry logic")
- **The "app" is the tool itself** — the evaluator runs the tool's test suite (`pytest`) and inspects output quality (visual inspection, API responses, etc.) instead of browser testing
- **The spec expands the user's request** into a comprehensive improvement plan with specific, measurable acceptance criteria per sprint
- **The evaluator is paramount** — it must verify improvements actually work by running the tool, not just reading code
- **Same quality target applies** — iterate until 9.0+ or plateau, don't stop at "it works"

---

## Detailed Guides

- **User Spec Agent**: [planner-guide.md](planner-guide.md)
- **SME Agent**: [sme-agent-guide.md](sme-agent-guide.md)
- **Build Agent** (+ modularization): [generator-guide.md](generator-guide.md)
- **Evaluator Agent** (+ design iteration): [evaluator-guide.md](evaluator-guide.md)
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

# Build Agent Guide

## Sprint Contract Template

Write `harness/contracts/sprint-N.md`:

```markdown
# Sprint N Contract: [Feature Name]
STATUS: PROPOSED | AGREED | BUILT | EVALUATED

## Scope
[What will be built — 2-3 paragraphs]

## Acceptance Criteria
1. [ ] [Specific testable behavior]
2. [ ] [Edge case behavior]
...

## How to Test
- Start: `uvicorn src.server:app --port 8000` + `cd frontend && npm run dev`
- Navigate to: [URL]
- Test sequence: [steps]

## Infrastructure Criteria (every sprint)
- [ ] No file >200 lines, no function >40 lines
- [ ] Feature code in `src/features/[name]/`
- [ ] Docs guide written, install.sh updated if needed

## Domain Criteria (if SME active)
- [ ] [From harness/sme/sprint-N-review.md]

## Parallel Execution Plan
- **Track A (Backend)**: [router, service, repository, unit tests]
- **Track B (Frontend)**: [components, hooks, API client]
- **Sync**: integration wiring + integration tests
- **Track C (post-sync)**: docs, prod readiness, installer
```

## Contract Review

Before AGREED, verify: criteria are testable and complete, edge cases included, "how to test" is specific, matches spec. If SME active: domain criteria included, formulas specified, terminology correct.

## Implementation Patterns

### Parallel Execution Within a Sprint

1. **Define API contract first** — Pydantic schemas + TypeScript types
2. **Launch parallel tracks** via `Task` subagents: Track A (backend) + Track B (frontend)
3. **Sync** — wire frontend to backend, integration tests
4. **Parallel finishing** — docs guide + production readiness + installer update

### Pre-Sprint Modularization Audit

Before new feature code, check: `wc -l src/**/*.py` (any >200?), function lengths (>40?), directory structure. Refactor first if violations exist.

### Per Sprint

- New feature → `src/features/[name]/` (backend) + `frontend/src/features/[name]/`
- Update `install.sh` if new deps, write docs guide, capture screenshots
- If SME active: SME reviews implementation → fix domain issues before handoff
- Self-test, commit: `git add -A && git commit -m "Sprint N: [feature]"`
- Update `CHANGELOG.md` (version `0.N.0` per sprint, `1.0.0` after final eval)

## Code Architecture (Modularization Rules)

**Rules**: No file >200 lines. No function >40 lines. Feature-based directories. Shared code in `lib/`. Clear public APIs via `__init__.py`.

### Backend (FastAPI)

```
src/
├── server.py              # Entry point — wiring only
├── lib/                   # config.py, database.py, warehouse.py, auth.py, logger.py
├── features/
│   └── loans/             # router.py, schemas.py, service.py, repository.py
├── middleware/             # error_handler.py, request_logger.py
```

### Frontend (React)

```
frontend/src/
├── App.tsx                # Routing only
├── features/
│   └── loans/             # LoanList.tsx, LoanForm.tsx, useLoans.ts, loanApi.ts
├── components/            # Button, Modal, Input, Toast, Layout
├── hooks/                 # useLocalStorage, useDebounce
├── lib/                   # api.ts, formatters.ts, constants.ts
```

### Refactoring Triggers

| Trigger | Action |
|---|---|
| File >200 lines | Split into smaller modules |
| Function >40 lines | Extract helpers |
| 3+ features share utility code | Move to `lib/` |
| Component mixes UI + business logic | Separate into component + hook/service |

### Code Structure Audit (evaluator runs this)

| Metric | Target |
|---|---|
| Longest file | ≤200 lines |
| Longest function | ≤40 lines |
| Feature directories | 1 per feature |
| Shared code in lib/ | Yes |
| Circular dependencies | 0 |

## Handoff Template

Write `harness/handoffs/sprint-N-handoff.md`: What was built, how to test, contract deviations, known limitations, deliverables checklist (feature in `features/`, install.sh updated, docs guide written, modularization rules met, SME review passed if active).

## Strategic Decision After Evaluation

The quality target (default 9.0, from `state.json`) drives the decision:

```
Score >= quality_target?
  → ADVANCE. Check remaining_spec_items in state.json:
    - Items remaining → start next sprint. Update state.json and progress.md.
    - No items remaining → proceed to Phase 4 (Final Integration Evaluation).
    Do NOT stop just because current_sprint == planned_sprints.

Score < quality_target but improving (delta > 0.3)?
  → REFINE. Read evaluator's "Required Improvements" list.
    Address items in priority order (CRITICAL first).
    Write updated handoff. Re-evaluate.

Score < quality_target and stagnant (2 consecutive iterations, delta < 0.3)?
  → ADVANCE anyway. Log the debt in progress.md:
    "Sprint N advanced at 8.2/10 (target 9.0). Debt: [specific gaps]."
    These gaps become candidates for a polish sprint at the end.

Score < fail_threshold (6)?
  → REFINE with critical fixes. This is a broken sprint, not a quality gap.

Stuck after 3 improvement iterations on same sprint?
  → ADVANCE with debt logged. Do NOT escalate to user unless
    the sprint is fundamentally blocked (auth, infra, external dependency).
    The user said to run autonomously — keep going.
```

**Key change from previous behavior**: Do NOT escalate to the user just because a score is 7.5 instead of 9.0. Iterate, and if you plateau, advance and log the debt. The ONLY reason to stop and ask the user is a hard blocker that code changes cannot fix (missing credentials, quota exhausted, external service down).

Write decision + reasoning in every handoff. Include the score trajectory.

## Building AI Features

When a sprint includes AI features, read [ai-agent-guide.md](ai-agent-guide.md). Build a proper agent with tools, not just an API call wrapper.

---

# Evaluator Guide

## Anti-Leniency Protocol

**Mantras**: "Would a senior engineer approve this?" / "Is this ACTUALLY working, or does it just LOOK like it works?" / "Am I praising this because it's good, or because I'm inclined to be nice?" / "8.0 is not exceptional — would I ship this to a paying customer?"

1. **Test before scoring** — run the app, click things, try to break it
2. **Score independently** — each criterion scored before writing overall verdict
3. **Anchor to failures** — list everything wrong first, then acknowledge what works
4. **Check for stubs** — click every button, fill every form, verify every interaction does something
5. **Compare to contract** — grade against agreed criteria, not vague "good enough"
6. **Compare to quality target** — a passing score (>6) that is below the quality target (default 9.0) means "needs another iteration", not "good enough"

## Exhaustive Interaction Testing

**READ [exhaustive-testing-guide.md](exhaustive-testing-guide.md) BEFORE EVERY EVALUATION.** You CANNOT write scores until the interaction manifest is complete with zero PENDING elements.

## Grading Rubric

**Standard mode** (6 criteria) / **Industry mode** with SME (7 criteria — adds Domain Accuracy):

| Criterion | Std Weight | Ind Weight | Fail < | What to Check |
|-----------|-----------|-----------|--------|---------------|
| Feature Depth | 25% | 20% | 6 | End-to-end working, no stubs, data persists, edge cases |
| Domain Accuracy | — | 15% | 6 | Correct formulas, terminology, validation rules, regulatory edge cases |
| Design Quality | 20% | 15% | 5 | Cohesive visual identity, consistent spacing/typography/color |
| Originality | 10% | 5% | 5 | Deliberate creative choices, not template/AI slop |
| Craft & Functionality | 20% | 20% | 6 | Spacing, contrast, error handling, usability |
| Test Coverage | 15% | 15% | 6 | `pytest` passes, coverage ≥70%, edge cases tested |
| Production Readiness | 10% | 10% | 6 | Error handling, loading states, toasts, validation, env config |

### Quality Target Enforcement

The quality target (default 9.0/10, set in `state.json`) determines whether a sprint advances or iterates:

| Weighted Score | Verdict | Action |
|---------------|---------|--------|
| < 6.0 | FAIL | REFINE with critical fixes. Do not advance. |
| 6.0 - 7.9 | BELOW TARGET | Competent but not exceptional. Write specific improvement items. Build agent iterates. |
| 8.0 - 8.9 | NEAR TARGET | Good but not there yet. Write targeted refinements. One more iteration likely enough. |
| >= 9.0 | MEETS TARGET | Advance to next sprint. |

**A score of 7-8 is NOT a celebration.** It means "this works but a senior engineer would push it further." Always write actionable improvement items when below target.

### Calibration Anchors (score these consistently)

**Feature Depth 4/10 (FAIL)**: UI shows tool as available but core interaction broken — stub pretending to work.
**Feature Depth 7/10 (BELOW TARGET)**: Core functionality solid, minor edge cases need polish. Needs another iteration.
**Feature Depth 9/10 (MEETS TARGET)**: Full end-to-end with edge cases handled, data persists, no stubs, error recovery works.
**Feature Depth 10/10**: Everything in 9, plus graceful degradation, retry logic, comprehensive error messages, zero dead code paths.

**Domain Accuracy 3/10 (FAIL)**: Wrong formula (ECL missing discount factor), wrong terminology ("Risk Score" vs "PD"), invalid states allowed (PD > 1.0).
**Domain Accuracy 7/10 (BELOW TARGET)**: Correct formula, correct terminology in main views, minor gaps (one page uses wrong label, weights not validated to sum to 1.0).
**Domain Accuracy 9/10 (MEETS TARGET)**: All formulas correct with citations, all terminology matches industry standard, validation rules enforce domain constraints, edge cases handled.

**Design 3/10 (FAIL)**: Multiple competing color schemes, inconsistent fonts, wasted viewport space.
**Design 6/10 (BELOW TARGET)**: Consistent but generic — indistinguishable from any React admin template.
**Design 9/10 (MEETS TARGET)**: Distinctive identity, restrained palette, every color use feels intentional, professional enough for customer-facing use.

**Originality 2/10 (FAIL)**: Purple gradient hero + 4 stat cards + generic icons = AI slop.
**Originality 7/10 (BELOW TARGET)**: Custom icons, deliberate palette choices, product-specific UI patterns.
**Originality 9/10 (MEETS TARGET)**: Unique visual language, creative solutions to UX problems, feels hand-crafted not template-generated.

**Test Coverage 4/10 (FAIL)**: 2 tests that only check status 200, coverage 25%.
**Test Coverage 7/10 (BELOW TARGET)**: 36 tests (unit + integration), coverage 78%, but no negative tests, no error case coverage.
**Test Coverage 9/10 (MEETS TARGET)**: 80+ tests (unit + integration + regression + scenario), coverage 85%+, error cases tested, edge cases tested, content verification (not just status checks).

**Production Readiness 5/10 (FAIL)**: No error handling, no retry logic, crashes on bad input.
**Production Readiness 7/10 (BELOW TARGET)**: Basic error handling, but no retry/backoff, no graceful degradation, no rate limit handling.
**Production Readiness 9/10 (MEETS TARGET)**: Retry with backoff, graceful degradation, rate limit handling, comprehensive error messages, logging, environment configuration.

## Testing Checklist

- [ ] Every button/link does something (no dead UI)
- [ ] Forms validate and show errors (client + server)
- [ ] Data persists after refresh
- [ ] Loading states for async operations
- [ ] Error states handled (network failure, invalid data)
- [ ] Empty states (no data yet)
- [ ] Previous sprint features still work (regression)
- [ ] `pytest` passes, coverage ≥70%
- [ ] Installer: see [installer-guide.md](installer-guide.md)
- [ ] Docs: see [docs-site-guide.md](docs-site-guide.md)
- [ ] Code structure: no file >200 lines, no function >40 lines

## Evaluation Output

Write TWO files:

**`harness/evaluations/sprint-N-manifest.md`** — Interaction audit (every element: TESTED / BUG / SKIPPED, zero PENDING). Include data persistence check.

**`harness/evaluations/sprint-N-eval.md`** — Graded evaluation with: scores table (weighted), contract criteria results, bugs (critical/major/minor), dead UI elements, domain accuracy (if SME), `pytest` results, installer/docs/code structure audit, verdict (PASS/FAIL), required fixes or strategic recommendation.

## Re-Evaluation After Fixes (Iteration Mode)

This is the DEFAULT behavior for every sprint, not an optional mode. After the build agent fixes cited issues:

1. **Focus on previously failed/low criteria** — verify specific bugs fixed
2. **Quick regression on passing criteria** — ensure fixes didn't break anything
3. **Re-score all criteria** — don't assume passing criteria stayed the same
4. **Update the score trajectory** — append new score to the sprint's trajectory array
5. **Compare to quality target** — if still below, write the NEXT set of improvement items

### Score Trajectory Tracking

Every evaluation file must include a score trajectory section:

```
## Score Trajectory
Iteration 1: 7.2 (Feature Depth: 7, Design: 6, Tests: 8, ...)
Iteration 2: 8.4 (Feature Depth: 8, Design: 8, Tests: 9, ...)
Iteration 3: 9.1 (Feature Depth: 9, Design: 9, Tests: 9, ...)
Delta: +1.2, +0.7 → improving, target met at iteration 3
```

### When to Stop Iterating

- **Target met**: weighted score >= quality target → ADVANCE
- **Plateau**: 2 consecutive iterations with < 0.3 improvement → ADVANCE with logged debt
- **Max iterations**: 3 improvement iterations on the same sprint → ADVANCE regardless
- **NEVER stop because "it's good enough"** — stop because the number says so

### Iteration Quality Principles

**Criteria language steers output**: "museum quality" → minimal gallery layouts, "editorial" → magazine typography, "brutalist" → raw bold high-contrast, "retro" → pixel art limited palettes.

**Common traps**: "Safe middle" (competent but generic — push for distinctive), increasing complexity without improving coherence (emphasize restraint), score inflation over time (re-read calibration anchors before each round), praising improvement instead of measuring against the target.

### Writing Actionable Improvement Items

When below the quality target, every evaluation MUST include a prioritized list of specific improvements:

```
## Required Improvements (to reach 9.0 target)
1. [CRITICAL] Feature Depth: Add retry logic to API calls — currently crashes on 429
2. [HIGH] Test Coverage: Add negative tests — no tests for invalid input, bad auth, missing data
3. [HIGH] Production Readiness: Add rate limit backoff — builder hits 60 req/min limit with no recovery
4. [MEDIUM] Design Quality: Table header row needs stronger contrast against body rows
5. [LOW] Originality: Consider custom error messages instead of generic "Something went wrong"
```

The build agent reads this list and addresses items in priority order. Be specific — "improve error handling" is useless; "add try/except around API calls in `api_call()` with exponential backoff on HTTP 429" is actionable.

---

# Exhaustive Interaction Testing Guide

**Rule**: You MUST produce an interaction audit log. Every interactive element must appear with TESTED, BUG, or SKIPPED status. Zero PENDING allowed.

## Phase 1: Element Discovery

```bash
agent-browser open http://localhost:8000 && agent-browser wait --load networkidle
agent-browser snapshot -i
```

Repeat for every page/view. Build the manifest (`harness/evaluations/sprint-N-manifest.md`):

```markdown
## Page: / (Home)
| Ref | Element | Type | Status | Notes |
|-----|---------|------|--------|-------|
| @e1 | "New Project" button | button | PENDING | |
| @e2 | Search input | input | PENDING | |
| @e3 | Sort dropdown | select | PENDING | |
```

## Phase 2: Systematic Click-Through

For EACH element, use the pattern: **snapshot before → interact → wait → snapshot after → record what changed**.

| Element Type | Interaction Commands | What to Verify |
|---|---|---|
| **Buttons** | `click @eN` | UI changed? Modal appeared? Data updated? Or nothing (= dead UI = bug)? |
| **Inputs** | `fill @eN "test"` then `fill @eN ""` then `fill @eN "a]b<c>"` | Accepts input, clears, handles special chars |
| **Links** | `click @eN` → check URL changed → `press Alt+ArrowLeft` → verify back | Navigates correctly, back button works |
| **Dropdowns** | `click @eN` → verify options → `select @eN "Option A"` | Options appear, selection applies |
| **Checkboxes/Toggles** | `check @eN` → verify changed → `check @eN` → verify reverted | State toggles correctly |
| **Forms** | Fill all fields + submit (happy path), submit empty (sad path), invalid data (sad path) | Success state, validation errors shown |

For complex interactions (drag-and-drop, canvas), use `agent-browser eval` with mouse events or delegate to `browser-use` subagent.

## Phase 3: Update Manifest

```markdown
| @e1 | "New Project" button | button | TESTED | Opens modal with name/desc fields |
| @e5 | Delete icon | button | BUG | Click does nothing — dead UI |
```

Valid: `TESTED`, `BUG`, `SKIPPED` (with justification). Invalid: `LOOKS OK`, `CODE REVIEWED`, `ASSUMED WORKING`.

## Phase 4: Data Persistence Check

Create something → refresh page → **still there?** Navigate away → come back → **still there?**

## Phase 5: Cross-Feature Testing (integration evals)

Create item in Feature A → navigate to Feature B → verify Feature B sees it.

## Completeness Gate

Evaluation CANNOT be submitted unless: manifest exists, zero PENDING elements, ≥1 screenshot per page, data persistence verified, element count matches snapshot count.

## Common Dead UI Patterns (always click these)

| Pattern | Common Bug |
|---------|------------|
| Delete/trash icons | No confirmation, or click does nothing |
| Edit/pencil icons | Empty form, or doesn't open |
| Dropdown menus | Options don't trigger action |
| Toggle switches | Visual toggle but no state change |
| Pagination | Always shows same data |
| Sort headers | Doesn't sort, or sorts wrong |
| Search/filter | No filtering happens |
| Modal close (X, outside click, Escape) | One method doesn't close |
| "Load more" / infinite scroll | Nothing loads, or duplicates |

---

# Comprehensive Testing Guide

Build Agent writes unit + integration tests. Evaluator Agent does browser E2E testing (see [exhaustive-testing-guide.md](exhaustive-testing-guide.md)).

## Setup

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["src"]
omit = ["src/server.py", "tests/*"]

[tool.coverage.report]
fail_under = 70
show_missing = true
```

Frontend: `cd frontend && npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom`

## Shared Fixtures (Real Lakebase — No Mocks)

All tests connect to **real remote Lakebase**. Transaction rollback isolates each test.

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.server import app
from src.lib.database import get_connection

@pytest.fixture(scope="session")
def db_conn():
    conn = get_connection()
    yield conn
    conn.close()

@pytest.fixture(autouse=True)
def clean_test_data(db_conn):
    db_conn.autocommit = False
    yield
    db_conn.rollback()

@pytest.fixture
def db(db_conn):
    return db_conn.cursor()

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

## Unit Tests

| What to Test | Example |
|---|---|
| Validation functions | `validate_loan({"amount": -1})` raises `ValidationError` |
| Business logic / calculations | `calculate_ecl(exposure, pd, lgd)` returns correct value |
| Data transformers | `format_currency(1234.5)` returns `"$1,234.50"` |
| Pydantic models | `LoanCreate(amount=-1)` raises `ValidationError` |

```python
# tests/unit/test_loan_service.py
class TestLoanService:
    @pytest.fixture
    def service(self, db_conn):
        return LoanService(db=db_conn)

    def test_create_loan_valid(self, service):
        loan = service.create(LoanCreate(borrower="Acme Corp", amount=100_000, currency="USD", term_months=36))
        assert loan.id is not None and loan.borrower == "Acme Corp"

    def test_rejects_negative_amount(self, service):
        with pytest.raises(ValueError, match="Amount must be positive"):
            service.create(LoanCreate(borrower="Acme", amount=-1, currency="USD", term_months=36))
```

Target: **70%+ line coverage** on business logic files. Each sprint adds tests for new service functions, validation, and edge cases.

## Integration Tests

```python
# tests/integration/test_loans_api.py
class TestLoansAPI:
    async def test_create_returns_201(self, client):
        resp = await client.post("/api/loans", json={"borrower": "Acme", "amount": 100_000, "currency": "USD", "term_months": 36})
        assert resp.status_code == 201 and resp.json()["id"] is not None

    async def test_get_returns_created(self, client):
        await client.post("/api/loans", json={"borrower": "Acme", "amount": 100_000, "currency": "USD", "term_months": 36})
        resp = await client.get("/api/loans")
        assert len(resp.json()) >= 1

    async def test_422_for_missing_fields(self, client):
        resp = await client.post("/api/loans", json={"borrower": "Acme"})
        assert resp.status_code == 422

    async def test_delete_returns_204(self, client):
        created = await client.post("/api/loans", json={"borrower": "Acme", "amount": 100_000, "currency": "USD", "term_months": 36})
        resp = await client.delete(f"/api/loans/{created.json()['id']}")
        assert resp.status_code == 204

    async def test_404_for_nonexistent(self, client):
        resp = await client.delete("/api/loans/nonexistent")
        assert resp.status_code == 404
```

## Build Agent Protocol

After each sprint: write unit tests → write integration tests → `pytest` → `pytest --cov=src --cov-report=term` (≥70%) → include results in handoff.

## Evaluator Verification

```markdown
- [ ] `pytest` passes with zero failures
- [ ] New tests added for this sprint's features
- [ ] Unit tests cover validation, business logic, data transformers
- [ ] Integration tests cover all endpoints (happy + error paths)
- [ ] Coverage on business logic ≥ 70%
```

---

# Production Readiness Guide — Mini SaaS Quality Bar

Every sprint must meet these standards. Build Agent implements them incrementally; Evaluator checks every sprint.

## 11 Mandatory Requirements

### 1. Error Handling & Resilience
- **Backend**: Global exception handler → structured JSON `{"detail": {"code": int, "message": str}}`. No stack traces in responses.
- **Frontend**: Error boundary, user-friendly API error messages, offline state handling, inline form validation errors.

```python
# src/middleware/error_handler.py
class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(f"[{request.method}] {request.url.path} → 500: {exc}")
            return JSONResponse(status_code=500, content={"detail": {"code": 500, "message": "Internal server error"}})
```

### 2. Loading States & Skeleton Screens
Every async operation: skeleton screens on page load, spinner on button actions, disabled submit during form submission. Never blank screens.

### 3. Toast Notifications
Create/update/delete → success toast. Errors → red error toast. Auto-dismiss 3-5s, dismissible, stacked, color-coded (green/red/yellow/blue).

### 4. Environment Configuration
No hardcoded URLs/secrets. Use pydantic-settings. `.env.example` committed, `.env` gitignored. Fail fast if required var missing. See [installer-guide.md](installer-guide.md) for `.env.example` template.

```python
# src/lib/config.py
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    port: int = 8000
    databricks_host: str
    lakebase_connection_string: str = ""
    lakebase_host: str = ""
    lakebase_port: int = 5432
    lakebase_db: str = ""
    lakebase_user: str = ""
    lakebase_password: str = ""
    class Config:
        env_file = ".env"
settings = Settings()
```

### 5. Data Validation (Client + Server)
- **Client**: Required fields marked, inline validation on blur, format validation (URL, email, numbers), max length with counter.
- **Server**: Pydantic models with `extra="forbid"`, `Field(gt=0)`, `field_validator` for sanitization. Return specific per-field errors.

### 6. Dark Mode
Detect `prefers-color-scheme`, manual toggle, persist in localStorage, all colors as CSS custom properties, both themes fully usable.

### 7. SEO & Meta Tags
Title, description, OG tags, favicon in `<head>`.

### 8. Basic Accessibility (a11y)
Semantic HTML (`<nav>`, `<main>`, `<button>`), keyboard navigation (Tab/Enter/Escape), visible focus rings, `aria-label` on icon buttons, `<label>` for every input, 4.5:1 contrast ratio, `alt` on images.

### 9. Performance Basics
Page load <3s on localhost, no unnecessary re-renders, lazy-loaded images, API caching where appropriate, clean up event listeners on unmount.

### 10. Rate Limiting & Security
CORS configured, `slowapi` rate limiting on sensitive endpoints. In Databricks Apps, OAuth handles auth automatically.

### 11. Seed Data / Demo Mode
First-run shows realistic sample data or onboarding prompt. `python seed.py` seeds remote Lakebase. "Reset to demo data" option.

## CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: ruff check src/
      - run: pytest --cov=src --cov-report=term
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
          LAKEBASE_HOST: ${{ secrets.LAKEBASE_HOST }}
          LAKEBASE_DB: ${{ secrets.LAKEBASE_DB }}
          LAKEBASE_USER: ${{ secrets.LAKEBASE_USER }}
          LAKEBASE_PASSWORD: ${{ secrets.LAKEBASE_PASSWORD }}
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: cd frontend && npm ci && npm test && npm run build
```

## Sprint Rollout Schedule

| Sprint 1 (foundational) | Sprint 2 (after CRUD) | Sprint 3+ | Final |
|---|---|---|---|
| Error handling | Toast notifications | Dark mode | CI/CD pipeline |
| Loading states | Client-side validation | SEO meta tags | Performance audit |
| Env config | Seed data | | |
| Server validation | Rate limiting / CORS | | |
| Semantic HTML | Keyboard nav, a11y | | |

## Evaluator Checklist

```markdown
- [ ] Structured error JSON, no stack traces
- [ ] Loading states on all async operations
- [ ] Toast notifications for CRUD actions
- [ ] No hardcoded URLs/secrets, pydantic-settings used
- [ ] Client + server validation on forms
- [ ] Dark mode toggle, both themes usable
- [ ] Semantic HTML, keyboard nav, focus visible, form labels
- [ ] Seed data or onboarding on first run
- [ ] CI config exists and is valid
```

---

# Setup & Deployment Guide

FastAPI + React run locally, connecting to **remote Databricks services** (Lakebase, Delta Lake, FMAPI). No local database. SSO/YubiKey only at deploy time.

```
LOCAL MACHINE                          DATABRICKS PLATFORM
┌─────────────────────┐                ┌──────────────────────┐
│ React (Vite :5173)  │──proxy──┐      │  Lakebase (OLTP)     │
│ FastAPI (:8000)     │◄────────┘      │  Delta Lake (DWH)    │
│   └─ DATABRICKS_*   │───────────────►│  FMAPI / ML Serving  │
│      LAKEBASE_*     │  PAT token     │  Unity Catalog       │
└─────────────────────┘                └──────────────────────┘
```

## install.sh — Local Dev

```bash
#!/usr/bin/env bash
set -euo pipefail
APP_NAME="[App Name]"
echo "  $APP_NAME — Local Development Setup"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }

# Prerequisites
command -v python3 &>/dev/null || fail "Python 3 not found"
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
[[ "$(echo "$PY_VER >= 3.10" | bc)" == "1" ]] && ok "Python $PY_VER" || fail "Python 3.10+ required"
[ -f "frontend/package.json" ] && { command -v node &>/dev/null && ok "Node.js $(node -v)" || fail "Node.js 18+ required"; }

# Python env
python3 -m venv .venv 2>/dev/null || true && source .venv/bin/activate
pip install -r requirements.txt -q && ok "Python deps installed"

# Frontend
[ -f "frontend/package.json" ] && (cd frontend && npm install 2>&1 | tail -1) && ok "Frontend deps installed"

# Environment
[ ! -f ".env" ] && cp .env.example .env && warn "Created .env — edit with your Databricks credentials"

# Verify Databricks connection
source .env 2>/dev/null || true
[ -n "${DATABRICKS_HOST:-}" ] && python3 -c "
from databricks.sdk import WorkspaceClient; import os
w = WorkspaceClient(host=os.environ['DATABRICKS_HOST'], token=os.environ['DATABRICKS_TOKEN'])
print(f'  Connected as: {w.current_user.me().user_name}')
" 2>/dev/null && ok "Databricks connected" || warn "Check .env credentials"

# Seed + test
[ -f "seed.py" ] && [ -n "${LAKEBASE_HOST:-}" ] && python3 seed.py && ok "Demo data seeded"
pytest --tb=short -q && ok "Tests pass" || warn "Some tests failed"

echo -e "\n  ${GREEN}Ready!${NC}  Backend: uvicorn src.server:app --reload --port 8000"
echo "           Frontend: cd frontend && npm run dev"
echo "           Deploy:   ./deploy.sh"
```

## app.yaml — Databricks Apps Config

```yaml
command: ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
resources:
  - name: sql-warehouse
    sql_warehouse: { id: "${DATABRICKS_WAREHOUSE_ID}", permission: CAN_USE }
  - name: lakebase-db
    lakebase: { id: "${LAKEBASE_INSTANCE_ID}", permission: CAN_USE }
```

## deploy.sh — Databricks Apps

```bash
#!/usr/bin/env bash
set -euo pipefail
APP_NAME="[app-name]"
command -v databricks &>/dev/null || { echo "Databricks CLI not found"; exit 1; }
databricks auth describe 2>/dev/null || { echo "Not authenticated. Run: databricks configure"; exit 1; }
[ -f "frontend/package.json" ] && (cd frontend && npm install && npm run build)
databricks apps deploy "$APP_NAME" --source-code-path .
echo "Deployed: https://<workspace>.databricks.com/apps/$APP_NAME"
```

## Connection Patterns

```python
# src/lib/database.py — Lakebase (OLTP)
import os, psycopg

def get_connection():
    conn_str = os.environ.get("LAKEBASE_CONNECTION_STRING")
    if conn_str:
        return psycopg.connect(conn_str)
    return psycopg.connect(
        host=os.environ["LAKEBASE_HOST"], port=os.environ.get("LAKEBASE_PORT", "5432"),
        dbname=os.environ["LAKEBASE_DB"], user=os.environ["LAKEBASE_USER"],
        password=os.environ["LAKEBASE_PASSWORD"], sslmode="require",
    )
```

```python
# src/lib/warehouse.py — Delta Lake (DWH)
from databricks import sql as dbsql
import os

def query_delta_table(query: str, params=None):
    with dbsql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"],
        http_path=os.environ["DATABRICKS_SQL_WAREHOUSE_PATH"],
        access_token=os.environ.get("DATABRICKS_TOKEN"),
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
```

## .env.example

```bash
PORT=8000
DATABRICKS_HOST=<workspace>.cloud.databricks.com
DATABRICKS_TOKEN=<pat-token>
DATABRICKS_SQL_WAREHOUSE_PATH=/sql/1.0/warehouses/<id>
LAKEBASE_HOST=<lakebase-host>
LAKEBASE_PORT=5432
LAKEBASE_DB=<db-name>
LAKEBASE_USER=<user>
LAKEBASE_PASSWORD=<password>
# In Databricks Apps: LAKEBASE_CONNECTION_STRING injected automatically
```

## Vite Proxy (frontend dev server → FastAPI)

```typescript
// frontend/vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } } },
});
```

## requirements.txt

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0
pydantic-settings>=2.0
psycopg[binary]>=3.1
psycopg_pool>=3.1
databricks-sdk>=0.30.0
databricks-sql-connector>=3.0.0
slowapi>=0.1.9
python-multipart>=0.0.6
pytest>=8.0
pytest-cov>=5.0
pytest-asyncio>=0.23
httpx>=0.27
ruff>=0.4.0
```

## Evaluator Checklist

```markdown
- [ ] `./install.sh` completes, backend starts on :8000, frontend on :5173
- [ ] App connects to remote Lakebase (no local database)
- [ ] `app.yaml` valid, `deploy.sh` executable, `.env.example` complete
- [ ] No hardcoded URLs, tokens, or secrets in source code
- [ ] Frontend proxies /api/* to backend correctly
```

---

# Documentation & Demo Guide

## Docs Site (Docusaurus)

Every build produces a docs site: overview → install → getting-started → feature guides → architecture → FAQ.

### Structure

```
docs-site/
├── docusaurus.config.js
├── sidebars.js
├── docs/
│   ├── overview.md          # What and why
│   ├── installation.md      # One-command install
│   ├── getting-started.md   # First 5 minutes
│   ├── guides/[feature].md  # One per major feature
│   ├── architecture.md      # Tech stack + data flow
│   └── faq.md
└── static/img/              # Screenshots + GIFs
```

### When to Create

- **Each sprint**: Build Agent writes `docs/guides/[feature].md` for the feature it built
- **Docs sprint** (last): Assemble landing page, overview, install, getting-started, architecture, FAQ
- **Evaluator**: Verify `cd docs-site && npm install && npm run build` succeeds

### Doc Pages

| Page | Key Content |
|------|-------------|
| overview.md | What it does, who it's for, key features |
| installation.md | Prerequisites table, `./install.sh`, verify command |
| getting-started.md | 3-step walkthrough with screenshots |
| guides/[feature].md | Usage steps, options/config, examples, troubleshooting |
| architecture.md | Stack diagram, module structure, data flow |
| faq.md | Common questions |

### Evaluator Checklist

```markdown
- [ ] `cd docs-site && npm install && npm run build` succeeds
- [ ] Landing page has app name, tagline, "Get Started" CTA
- [ ] Installation page matches actual install process
- [ ] Each major feature has its own guide
- [ ] All internal links resolve
- [ ] Screenshots included where they add value
```

## Screenshots & GIFs

### Capturing Screenshots

```bash
agent-browser open http://localhost:8000 && agent-browser wait --load networkidle
agent-browser screenshot harness/screenshots/demo-home.png
agent-browser click @eFeature1 && agent-browser wait --load networkidle
agent-browser screenshot harness/screenshots/demo-feature1.png
```

### Capturing GIFs (screen recording → ffmpeg)

```bash
# Record screen region (macOS)
screencapture -v -R 0,0,1280,800 harness/screenshots/demo-flow.mov

# Convert to GIF
ffmpeg -i harness/screenshots/demo-flow.mov \
  -vf "fps=10,scale=800:-1:flags=lanczos" \
  -gifflags +transdiff \
  harness/screenshots/demo-flow.gif
```

For scripted reproducible GIFs, combine `agent-browser` interactions with `ffmpeg` recording in background.

**Best practices**: 3-8 seconds per GIF, 800px wide max, 10fps, one complete interaction per GIF, target <5MB.

### Capture Schedule

| Sprint | Capture |
|--------|---------|
| Sprint 1 | Homepage, main layout, navigation |
| Sprint 2+ | Each feature's primary workflow (GIF preferred) |
| Final | Full walkthrough GIF, all major views |

## Demo Day Presentation

After final integration evaluation passes, produce a Google Slides deck (8-12 slides):

| Slide | Content |
|-------|---------|
| 1. Title | App name + tagline + homepage screenshot |
| 2. Problem & Vision | What problem, who is the user, what's distinctive |
| 3. Domain Context | Industry/regulatory framework (if SME active) |
| 4-7. Features | One slide per major feature with screenshot/GIF |
| 8. Architecture | Tech stack diagram, data flow |
| 9. Quality Metrics | Test results, eval scores, domain accuracy |
| 10. Live Demo Script | Step-by-step walkthrough, "wow moment" |
| 11. What's Next | Enhancements, limitations, deployment status |
| 12. Links | App URL, docs URL, repo, install instructions |

Use the `google-slides` skill via `Task(subagent_type="generalPurpose")` to create the deck with Databricks template.

### Live Demo Tips

1. Start with the **problem**, not the tech stack
2. Show **happy path** first → then **resilience** (errors, validation)
3. If domain-specific, show **domain accuracy** (terminology, formulas)
4. Show **dark mode** — crowd-pleaser
5. End with the **"wow moment"**
6. Keep it under **10 minutes**

---

# Troubleshooting Guide — When Things Go Wrong

Build environment issues are inevitable. This guide helps the Build Agent recover quickly instead of wasting sprint time on infrastructure problems.

## Diagnosis Protocol

When something fails, follow this order:

1. **Read the error message** — don't guess. Copy the exact error.
2. **Check the obvious** — is the server running? Is the port in use? Is the file saved?
3. **Isolate the problem** — does it fail in a fresh terminal? After a restart?
4. **Fix and document** — fix the issue, note it in the handoff for the evaluator.

## Common Issues and Fixes

### Python / pip Issues

| Problem | Symptoms | Fix |
|---------|----------|-----|
| pip install fails | `ERROR: Could not find a version that satisfies` | Check Python version: `python3 --version`. Ensure 3.10+. |
| Virtual env not activated | `ModuleNotFoundError` for installed packages | `source .venv/bin/activate` |
| Dependency conflict | `ERROR: pip's dependency resolver` | Pin versions in `requirements.txt`. Try `pip install --force-reinstall`. |
| psycopg build fails | `pg_config not found` | Install PostgreSQL: `brew install postgresql@16` or use `psycopg[binary]` |
| Import errors after install | Module not found despite install | Check you're in the right venv. Run `which python3` to verify. |

### npm / Node.js Issues (Frontend Only)

| Problem | Symptoms | Fix |
|---------|----------|-----|
| npm registry down | `E503 Service Unavailable`, install hangs | Use mirror: `npm install --registry=https://registry.npmmirror.com` |
| npm install stuck | No output for >60 seconds | Kill and retry with `--verbose`. Clear cache: `npm cache clean --force` |
| Node version mismatch | `SyntaxError: Unexpected token` | Check `node -v`, use `nvm use 20` or install correct version |
| `node_modules` corrupted | Random import errors after install | `rm -rf node_modules package-lock.json && npm install` |
| Peer dependency conflicts | `ERESOLVE unable to resolve dependency tree` | `npm install --legacy-peer-deps` |

### Port Conflicts

| Problem | Fix |
|---------|-----|
| `address already in use :::8000` | `lsof -ti:8000 \| xargs kill -9` then restart |
| Multiple dev servers running | Check terminals: `lsof -i :8000 -i :5173` and kill extras |
| Port blocked by system | Try a different port: `uvicorn src.server:app --port 8001` |

### Lakebase Issues (Remote — No Local DB)

| Problem | Fix |
|---------|-----|
| `connection refused` | Check `LAKEBASE_HOST` in `.env`. Verify instance is running: `databricks lakebase list` |
| `FATAL: password authentication failed` | Regenerate credentials. Check `LAKEBASE_USER` and `LAKEBASE_PASSWORD` in `.env`. |
| `SSL connection required` | Add `sslmode=require` to connection params (already in the template). |
| Lakebase autoscale cold start | First query may be slow (~5s). Add a health check endpoint that warms the connection on startup. |
| `timeout expired` | Lakebase instance may be scaled to zero. Wait 10-15s and retry. Check Databricks workspace for instance status. |
| Migration failed mid-sprint | Check `harness/sme/` for schema requirements. Re-run: `python3 seed.py` (uses `ON CONFLICT DO NOTHING`). |

### Databricks Issues

| Problem | Fix |
|---------|-----|
| `databricks auth` fails | Re-authenticate: `databricks configure` or check token expiry |
| App deploy fails | Check `app.yaml` syntax. Verify resources exist. Check logs: `databricks apps logs [app-name]` |
| FMAPI rate limited | Add retry with exponential backoff. Check quota: `databricks serving-endpoints list` |
| SQL warehouse timeout | Check warehouse is running. Increase timeout in connection config. |
| Unity Catalog permission denied | Check grants: `GRANT USAGE ON CATALOG ... TO ...` |

### Frontend Issues

| Problem | Fix |
|---------|-----|
| Blank page after build | Check browser console for errors. Verify `index.html` references correct JS paths. |
| CORS errors | Backend must set `CORSMiddleware`. Check allowed origins in FastAPI config. |
| Hot reload not working | Check if file watcher limit is reached. Vite: check `vite.config.ts` server settings. |
| CSS not updating | Hard refresh: `Cmd+Shift+R`. Clear browser cache. Check CSS import order. |
| API calls fail in dev | Check proxy config in `vite.config.ts` or use correct `http://localhost:8000` base URL. |

### Test Issues

| Problem | Fix |
|---------|-----|
| `pytest` not found | Activate venv: `source .venv/bin/activate`. Or: `python3 -m pytest` |
| Tests pass locally, fail in CI | Check GitHub Secrets have correct Lakebase credentials. Check Python version matches. |
| Integration tests hang | FastAPI TestClient not configured. Use `httpx.AsyncClient` with `ASGITransport`. |
| Flaky tests | Check for shared state — ensure `conftest.py` rollback fixture is `autouse=True`. Use `pytest-randomly`. |
| DB tests fail with `connection refused` | Lakebase may be scaled to zero. Run any query to wake it, wait 10-15s, retry. Check `.env` credentials. |
| Tests leave dirty data in Lakebase | Ensure `conftest.py` uses transaction rollback (`conn.rollback()` in fixture teardown). |
| Tests slow (>30s) | Lakebase cold start. Add a session-scoped fixture that opens the connection once. Check for N+1 queries. |

## Build Agent Recovery Protocol

When the Build Agent hits an infrastructure issue:

1. **Don't panic-simplify** — don't remove features just because `pip install` failed
2. **Try the fix from this guide first** — most issues have a known solution
3. **If the fix doesn't work in 5 minutes**, simplify the dependency (e.g., use a lighter alternative)
4. **Document the workaround** in the handoff — the evaluator needs to know
5. **Never silently downgrade** — if you replaced Lakebase with SQLite, say so explicitly

## Evaluator Recovery Protocol

When the Evaluator Agent hits issues during testing:

1. **Server won't start**: Check if port is in use. Try `uvicorn src.server:app --port 8001`.
2. **Browser testing fails**: Verify the URL. Try `agent-browser open http://localhost:8000` manually.
3. **Tests fail unexpectedly**: Run `pytest -v --tb=long` for detailed output.
4. **App crashes during testing**: Check server logs in the terminal. Look for unhandled exceptions.

## When to Escalate to User

Escalate (don't keep retrying) when:
- Authentication/credentials are needed that you don't have
- A paid service quota is exhausted
- The issue requires system-level changes (kernel params, firewall rules)
- The same fix has failed 3 times
- The issue is clearly outside the application (network, DNS, hardware)

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

# AI Agent Building Guide

When the spec includes AI-powered features, the Build Agent should build a proper AI agent with tools — not just wrap an API call. This guide covers the patterns from Anthropic's V2 harness.

## The Problem

Naive AI integration looks like this:
```
User types prompt → send to LLM API → display response
```

This is a chatbot, not an agent. It can't DO anything in the app.

## The Goal

Build an agent that can drive the app's own functionality:
```
User describes intent → Agent reasons about steps → Agent calls app's tools → App state changes
```

Example: In a game maker, "create a forest level with enemies" should result in the agent calling `create_level()`, `add_tile_layer()`, `place_entities()` — not just generating text about a forest level.

## Architecture

```
┌─────────────────────────────────────┐
│           App Frontend              │
│  ┌─────────────────────────────┐    │
│  │  Chat/Prompt Interface      │    │
│  └──────────┬──────────────────┘    │
│             │ user message          │
│             ▼                       │
│  ┌─────────────────────────────┐    │
│  │  Backend Agent Endpoint     │    │
│  │  POST /api/agent/chat       │    │
│  │                             │    │
│  │  System prompt:             │    │
│  │  "You are an assistant for  │    │
│  │   [app domain]. You can     │    │
│  │   use tools to [actions]."  │    │
│  │                             │    │
│  │  Tools:                     │    │
│  │  - create_item(name, ...)   │    │
│  │  - update_settings(...)     │    │
│  │  - query_data(filter)       │    │
│  │  - delete_item(id)          │    │
│  └──────────┬──────────────────┘    │
│             │ tool calls            │
│             ▼                       │
│  ┌─────────────────────────────┐    │
│  │  App's Own API / DB Layer   │    │
│  │  (same CRUD the UI uses)    │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

## Implementation Pattern

### 1. Define Tools That Map to App Functionality

The agent's tools should be the same operations the UI performs. If the UI can create a project, the agent should have a `create_project` tool.

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_project",
            "description": "Create a new project with the given name and settings",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Project name"},
                    "template": {"type": "string", "enum": ["blank", "platformer", "rpg"]},
                },
                "required": ["name"]
            }
        }
    },
    # ... more tools matching app capabilities
]
```

### 2. Write a Domain-Specific System Prompt

The system prompt should describe:
- What the app does and the agent's role within it
- What tools are available and when to use each
- Domain-specific knowledge (e.g., for a game maker: "levels are composed of tile layers, entity layers, and collision layers")
- Constraints (e.g., "always create a collision layer when creating a level")

### 3. Implement the Tool Execution Loop

```python
async def agent_chat(user_message: str, context: dict):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    
    while True:
        response = await llm_client.chat(messages=messages, tools=tools)
        
        if response.tool_calls:
            for tool_call in response.tool_calls:
                result = await execute_tool(tool_call.function.name, tool_call.function.arguments)
                messages.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        else:
            return response.content
```

### 4. Handle Multi-Step Tasks

The agent should be able to chain multiple tool calls for complex requests:
- "Create a forest level with enemies" → `create_level("Forest")` → `add_tiles(trees, grass)` → `place_entity("goblin", x, y)` → `place_entity("wolf", x, y)`
- "Set up the mixer for a rock song" → `set_tempo(120)` → `add_track("drums")` → `add_track("guitar")` → `set_effect("distortion", track="guitar")`

## Testing AI Features

The evaluator should test AI features by:

1. **Basic functionality**: Does the agent respond and call tools?
2. **Tool correctness**: Do tool calls produce the expected app state changes?
3. **Multi-step tasks**: Can the agent handle requests requiring multiple tool calls?
4. **Error handling**: What happens when a tool call fails? Does the agent recover?
5. **Domain knowledge**: Does the agent make sensible domain-specific decisions?

Example evaluation criteria:
```
- [ ] Agent can create a new [item] via natural language
- [ ] Agent chains 3+ tool calls for complex requests
- [ ] Agent's tool calls produce visible changes in the UI
- [ ] Agent handles ambiguous requests by asking for clarification OR making reasonable defaults
- [ ] Agent recovers gracefully when a tool call fails
```

## Common Pitfalls

### Agent calls tools but UI doesn't update
The frontend needs to poll or subscribe to state changes after agent actions. Use WebSocket, SSE, or poll the API after the agent response.

### Agent hallucinates tool names
Keep the tool list small and well-described. Test with the exact tool definitions you provide.

### Agent does too much in one turn
For complex requests, consider having the agent explain its plan before executing, or execute in stages with user confirmation.

### Agent can't access current app state
Provide a `get_current_state` or `list_items` tool so the agent can inspect what exists before making changes.

---


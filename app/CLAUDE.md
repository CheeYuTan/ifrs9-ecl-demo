# HARNESS MODE — AUTONOMOUS EXECUTION (11-Agent Architecture)

You are running as an AUTONOMOUS harness agent. There is NO user to interact with.
Quality target: 9.5/10.

Rules:
1. Write the spec immediately and start building — do NOT ask for confirmation
2. Run ALL sprints to completion without stopping
3. Write all progress to harness/progress.md and harness/state.json
4. The ONLY reason to stop: all spec items complete + final eval passes, OR ESCALATE
5. Do NOT output conversational text — focus entirely on building and testing
6. CLAUDE.md is AUTO-UPDATED by the shell watchdog when you change current_phase in state.json.
   You MUST update state.json current_phase at EVERY phase transition (DISCOVERY, MARKET_RESEARCH, BUILD_AGENT, VISUAL_QA, EVALUATOR, DOCUMENTATION, PRESENTATION, INSTALLATION, INTEGRATION, FINAL_EVALUATION).
   The watchdog detects the change and injects the correct guides for that phase within 10 seconds.
7. Proactive context reset every 2 feature sprints — write harness/context-reset-N.md and continue
8. Minimum 4 iterations before advance-with-debt. Max 5 iterations. Final eval: NO debt allowed.

---

---
name: harness-dev-loop
description: >-
  Multi-agent harness for building production-quality applications on Databricks.
  11-agent architecture: Discovery, Market Research, Spec, SME, Build, Visual QA,
  Evaluator, Documentation, Presentation, Installation, Integration. Supports both
  greenfield and existing projects. Use when the user says "use harness", "harness
  mode", or wants a complete application with independent QA and structured planning.
---

# Harness 3.0: 11-Agent Architecture

Build production-quality applications on **Databricks** using eleven agents. Supports both **greenfield** (new project) and **existing project** (audit → improve → extend) modes.

### Two Modes

| Mode | Trigger | Pre-Spec Pipeline |
|------|---------|-------------------|
| **Greenfield** | Empty directory, "build a..." | Market Research → Spec → sprints |
| **Existing Project** | Has source code, "improve...", "add to...", `--existing` flag | Discovery → Market Research → Spec → sprints |

In existing project mode, the Discovery Agent audits the codebase first, then the Spec Agent generates fix/improve/extend sprints instead of building from scratch.

## When to Use

- Building a complete application (not a quick script)
- 3+ features that need to work together
- User explicitly asks for "harness" mode

## How to Launch

```bash
# Greenfield (new project)
~/.claude/skills/harness-dev-loop/harness-run.sh "build a bookmark manager" --dir ~/new-project [--target 9.5]

# Existing project (auto-detected if source files exist, or use --existing)
~/.claude/skills/harness-dev-loop/harness-run.sh "add search and dark mode" --dir ~/my-existing-app
~/.claude/skills/harness-dev-loop/harness-run.sh "improve test coverage and add CI" --dir ~/my-app --existing

# Resume
~/.claude/skills/harness-dev-loop/harness-run.sh --resume

# Monitor
# watch cat /path/to/project/harness/progress.md
```

## Architecture

```
              ┌──────────────────────────────────────────────┐
              │ Existing project?                             │
              │   YES → DISCOVERY AGENT → discovery-report.md │
              │   NO  → skip                                  │
              └──────────────┬───────────────────────────────┘
                             ▼
User Prompt → MARKET RESEARCH AGENT → competitive-brief.md
                    │
              SPEC AGENT ◄──► SME AGENT
                    │ spec.md → immediately start sprints
                    │ (existing project: fix → improve → extend sprints)
                    ▼
              SPRINT LOOP (until ALL spec items done)
              ┌─────────────┐
              │ BUILD AGENT  │ → contract + handoff
              └──────┬──────┘
              ┌──────▼──────────────┐
              │ VISUAL QA ∥ EVALUATOR│ → parallel independent testing
              └──────┬──────────────┘
                Evaluator cross-checks VQA report, finalizes score
                score >= target → ADVANCE
                improving → REFINE (iterate with VQA ∥ Eval)
                plateau (3 iters, band<0.3) AND iter≥4 → ADVANCE with debt
                max 5 iterations → ADVANCE regardless
                    │
              Every 3 completed sprints (parallel with next Build):
              ┌────────────────────────────┐
              │ INSTALL + INTEGRATION       │ → infra verification
              └────────────────────────────┘
                    │
              Every 5 completed sprints (parallel with next Build):
              ┌────────────────────────────┐
              │ DOC + PRESENTATION          │ → content batch
              └────────────────────────────┘
                    │
              All done + all background agents PASS → FINAL EVALUATION (no debt allowed)
```

### Pipeline: Greenfield

```
MARKET RESEARCH → competitive-brief.md
     ↓
SPEC AGENT → spec.md (new features)
     ↓
S1: Build → (VQA ∥ Eval) → PASS
S2: Build → (VQA ∥ Eval) → PASS
S3: Build → (VQA ∥ Eval) → PASS
     │
     ├─── 3 sprints → infra batch
     ↓                 ↓
S4: Build         Install + Integration
S5: Build → PASS
     │
     ├─── 5 sprints → content batch
     ↓                 ↓
S6: Build         Doc + Presentation
...
```

### Pipeline: Existing Project

```
DISCOVERY AGENT → discovery-report.md (audit existing code)
     ↓
MARKET RESEARCH → competitive-brief.md
     ↓
SPEC AGENT → spec.md (fix → improve → extend sprints)
     ↓
S1: Build (fix critical issues) → (VQA ∥ Eval) → PASS
S2: Build (add test coverage)   → (VQA ∥ Eval) → PASS
S3: Build (prod readiness gaps) → (VQA ∥ Eval) → PASS
     │
     ├─── 3 sprints → infra batch
S4: Build (new feature)         → (VQA ∥ Eval) → PASS
...
```

## Critical Rules

1. **ALWAYS run Market Research** before Spec Agent writes spec — if no external competitors exist, Market Research writes a one-line skip note (see market-research-agent-guide.md)
2. **NEVER skip Spec Agent** — expand prompt, then immediately start Sprint 1
3. **NEVER let Build Agent self-evaluate** — always Visual QA → Evaluator
4. **NEVER score from code alone** — Evaluator MUST test the live running app
5. **NEVER advance with debt before iteration 4** — minimum 4 iterations
6. **NEVER mark final eval COMPLETE below target** — add dynamic sprints
7. **ALWAYS commit AND push to remote** after each successful sprint (`git add -A && git commit -m "Sprint N: [feature]" && git push origin HEAD`). The push is MANDATORY — local-only commits are not acceptable. Every sprint must be pushed immediately.
8. **ALWAYS run Install + Integration batch** every 3 completed sprints (parallel with next Build)
9. **ALWAYS run Doc + Presentation batch** every 5 completed sprints (parallel with next Build)
10. **ALWAYS write regression tests** for every evaluator-reported bug

## Autonomous Execution

Run the ENTIRE harness without pausing for user input. Write spec → start Sprint 1 immediately.

- Do NOT ask "shall I continue?" or summarize and wait
- Do NOT stop at `total_sprints` — keep going until all spec items complete + final eval passes
- Only stop for: (1) all complete + final eval passes, or (2) ESCALATE after 5 failed attempts with no improvement
- Write `state.json` + `progress.md` at every phase transition
- Context reset every 2 feature sprints — see Context Reset Protocol below

## Context Reset Protocol

Long harness runs consume context. Every **2 completed feature sprints**, proactively write a context reset file and continue.

### When to Trigger

- After every 2nd ADVANCE (sprint 2, 4, 6, ...)
- OR when you notice tool outputs being truncated or earlier conversation details becoming unavailable

### What to Write

Write `harness/context-reset-N.md` (N = reset number, starting at 1):

```markdown
# Context Reset N — After Sprint [X]

## Current State
- Sprints completed: [list with scores]
- Current sprint: [N+1] — [feature name]
- Remaining spec items: [list]
- Background agents pending: [list with status]
- Active debt: [any ADVANCE_WITH_DEBT items]

## Key Decisions Made
- [Architecture decisions that affect future sprints]
- [Domain-specific rules discovered during build/eval]

## Open Evaluator Feedback
- [Unresolved suggestions from previous evals that apply to upcoming sprints]

## Files to Re-Read on Resume
- harness/spec.md (remaining sprints section)
- harness/state.json
- harness/contracts/sprint-[N+1].md (if exists)
- harness/evaluations/sprint-[X]-eval.md (most recent eval — may have carryover bugs)
```

### After Writing the Reset File

1. Update `state.json` — set `last_context_reset` to the reset number
2. Re-read `harness/state.json` and `harness/spec.md` (remaining items section only)
3. Continue with the next sprint — do NOT pause or ask for confirmation

### On Resume (after crash or `--resume`)

Read the **highest-numbered** `harness/context-reset-N.md` first, then `state.json`, then `spec.md`. This gives you the most compact summary of where things stand.

## Quality Target

Default: **9.5/10**. User can override (e.g., "target 9.5").

- **Score >= target** → ADVANCE to next sprint
- **Below target, improving (δ>0.3)** → REFINE (fix cited issues)
- **Below target, below 6.0** → REFINE with critical fixes
- **Plateau** AND iteration ≥ 4 → ADVANCE with logged debt. Plateau = last 3 scores fall within a 0.3 band (max − min < 0.3). Example: 7.1, 7.3, 7.2 = plateau (band = 0.2). Example: 7.0, 7.5, 7.2 = NOT plateau (band = 0.5).
- **Declining** (score drops >0.5 from peak) → revert last change, then REFINE with different approach
- **Max 5 iterations** → ADVANCE regardless
- **Final evaluation** → NO advance-with-debt. Must meet target or add dynamic sprints.

## Agent Failure = Harness Signal

When an agent struggles or fails repeatedly, do NOT just retry. Ask: **"What capability is missing?"**

- Missing context → improve the contract or add a reference doc
- Unclear acceptance criteria → make the contract more specific
- Wrong architecture → update the spec's architecture section
- Encode the fix into the harness, then retry. Every failure improves the system.

## Escalation Protocol

When the harness cannot make progress, **escalate** rather than spin. Write `harness/ESCALATION.md` and stop.

### When to Escalate

| Trigger | Example |
|---------|---------|
| 5 iterations with no score improvement (band<0.3 across all 5) | Build keeps breaking the same test |
| Infrastructure failure that self-heals fail to resolve | Lakebase unreachable after 3 retries with backoff |
| Contradictory spec items | Feature A requires X, Feature B requires NOT X |
| Missing external dependency | Needs API key, OAuth token, or dataset the harness can't provision |
| Build Agent cannot implement a spec item | Spec requires capability beyond current tech stack |

### Escalation File

```markdown
# ESCALATION

## Status: BLOCKED
## Phase: [current phase]
## Sprint: [current sprint, iteration N]

## Root Cause
[1-2 sentences: what exactly is preventing progress]

## What Was Tried
1. [Attempt 1 — result]
2. [Attempt 2 — result]
3. [Attempt 3 — result]

## Score Trajectory
[e.g., 6.2 → 6.4 → 6.3 → 6.5 → 6.4 — plateau around 6.3-6.5]

## Recommended Action
- [ ] [Specific action the user should take — e.g., "Provide API key for X service", "Clarify whether feature Y should do A or B", "Simplify spec item Z — current scope requires capabilities not available"]

## To Resume
After resolving, run: `harness-run.sh --resume`
```

### State Update

Set `state.json`:
```json
{
  "status": "ESCALATED",
  "escalation_reason": "[one-line summary]"
}
```

The harness then stops. The user resolves the issue and runs `--resume`.

## State File

Update `harness/state.json` at EVERY phase transition.

```json
{
  "status": "IN_PROGRESS",
  "quality_target": 9.5,
  "current_phase": ["BUILD_AGENT", "INSTALLATION", "INTEGRATION"],
  "current_sprint": 3,
  "remaining_spec_items": ["Sprint 4: ...", "Sprint 5: ..."],
  "sprints_completed": [
    {"sprint": 1, "feature": "...", "score": 9.2, "iterations": 2, "trajectory": [7.4, 9.2]}
  ],
  "project_mode": "existing",
  "discovery_complete": true,
  "market_research_complete": true,
  "feature_sprints_since_last_integration": 1,
  "integration_trigger_interval": 3,
  "feature_sprints_since_last_presentation": 1,
  "presentation_trigger_interval": 5,
  "background_agent_results": {
    "install_sprint_3": "PENDING",
    "integration_sprint_3": "PENDING",
    "doc_sprint_5": "PENDING",
    "presentation_sprint_5": "PENDING"
  },
  "dev_server_port": 8000,
  "current_iteration": 0,
  "min_iterations_before_debt": 4,
  "max_iterations": 5
}
```

## Progress File

Write `harness/progress.md` at every phase transition and sprint advance. This is the primary monitoring interface — a user running `watch cat harness/progress.md` should understand the full picture.

```markdown
# Harness Progress

## Status: [IN_PROGRESS / ESCALATED / COMPLETE]
## Quality Target: X.X/10
## Mode: [greenfield / existing]

## Sprint Summary

| Sprint | Feature | Score | Iters | Status |
|--------|---------|-------|-------|--------|
| 1 | [name] | 9.2 | 2 | DONE |
| 2 | [name] | 8.8 | 3 | DONE |
| 3 | [name] | — | 1 | IN_PROGRESS |

## Current Activity
- **Phase**: BUILD_AGENT (Sprint 3, iteration 1)
- **Working on**: [specific task or fix]
- **Blockers**: [none, or description]

## Background Agents
| Agent | Trigger | Status | Score |
|-------|---------|--------|-------|
| Install | Sprint 3 | PASS | 9.1 |
| Integration | Sprint 3 | RUNNING | — |
| Documentation | Sprint 5 | PENDING | — |
| Presentation | Sprint 5 | PENDING | — |

## Remaining
- Sprint 4: [feature name]
- Sprint 5: [feature name]
- Dynamic: [any evaluator-added sprints]

## Debt Log
- [Sprint 2]: [what was deferred and why]
```

**Write rules**: Only the Build Agent and Evaluator update this file. Build Agent updates "Current Activity" at sprint start and advances the Sprint Summary on ADVANCE. Evaluator fills in scores after grading.

## Agent Guides (progressive disclosure)

Each agent reads ONLY its relevant guide. Details live there, not here.

| Phase | Guide |
|-------|-------|
| Discovery (existing projects) | discovery-agent-guide.md |
| Market Research | market-research-agent-guide.md |
| Spec | planner-guide.md + sme-agent-guide.md |
| Build | generator-guide.md + testing-guide.md + production-readiness-guide.md + troubleshooting-guide.md + ai-agent-guide.md |
| Visual QA | visual-qa-agent-guide.md + exhaustive-testing-guide.md |
| Evaluate | evaluator-guide.md + exhaustive-testing-guide.md |
| Documentation | documentation-agent-guide.md + docs-site-guide.md + doc-screenshot-guide.md + doc-gif-guide.md + doc-video-guide.md |
| Presentation | presentation-agent-guide.md |
| Installation | installation-agent-guide.md + installer-guide.md |
| Integration | integration-agent-guide.md + testing-guide.md |
| Final Eval | All guides |

## Port Management

Multiple harness projects may run on the same local machine. **NEVER kill an existing process** to free a port.

### Local Development
Find an available port before starting the app. Port ranges are intentionally separated:
- **8000-8100**: Main app (Build, VQA, Evaluator agents)
- **8100-8200**: Installation Agent testing (isolated clone, must not conflict with main app)

```python
import socket
def find_free_port(start=8000, end=8100):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError("No free port found in range")

port = int(os.environ.get("DATABRICKS_APP_PORT", 0)) or find_free_port()
```

Store the chosen port in `state.json` as `dev_server_port` so all agents know which port to test.

### Databricks Apps (Production)
Always use `DATABRICKS_APP_PORT`: `port = int(os.environ["DATABRICKS_APP_PORT"])`.
See https://docs.databricks.com/aws/en/dev-tools/databricks-apps/system-env#default-environment-variables.

**Never hardcode ports.** The deployment test `test_no_hardcoded_ports` verifies this.

## Environment

See `harness/templates/databricks-app/ENVIRONMENT.md` for Databricks Apps runtime constraints (Python 3.11, Node 22).

---

# Build Agent Guide

Build one feature per sprint with tests and production readiness items.

## Sprint Contract

Before coding, write `harness/contracts/sprint-N.md`:

```markdown
# Sprint N Contract: [Feature Name]

## Acceptance Criteria
- [ ] [Testable criterion 1]
- [ ] [Testable criterion 2]

## API Contract
- `POST /api/resource` → Request/Response schemas
- `GET /api/resource` → Query params, response shape

## Test Plan
- Unit tests: [what to test]
- Integration tests: [API endpoint tests]
- Regression tests: [bugs from prior eval to guard against]

## Production Readiness Items This Sprint
- [Which of the 15 items from production-readiness-guide.md to address]
```

## Build Flow

1. **Research via subagents** — delegate codebase exploration to subagents to keep main context clean. Use subagents to: scan existing code patterns, find reusable utilities, check how similar features were built. Only the summary enters your context.
2. **Modularization audit** — check file sizes, split anything approaching 200 lines
3. **API contract first** — Pydantic schemas + TypeScript types
4. **Parallel tracks** — backend endpoints + frontend components can be built concurrently
5. **Tests** — organize by type then feature: `tests/unit/[feature]/`, `tests/integration/[feature]/`, `tests/regression/[domain]/`. NEVER by sprint number. See testing-guide.md. Add regression tests for any prior eval bugs in domain-appropriate folders.
6. **Production readiness** — address items assigned to this sprint
7. **Update install.sh** — if new deps were added, update `requirements.txt`, `install.sh`, and `.env.example`
8. **Commit + push to remote** — `git add -A && git commit -m "Sprint N: [feature]" && git push origin HEAD` — this is MANDATORY, every sprint must be pushed to the remote repository immediately after commit. Do NOT skip the push.
9. **Handoff** — write `harness/handoffs/sprint-N-handoff.md`

## Handoff Template

```markdown
# Sprint N Handoff: [Feature Name]

## What Was Built
- [Component/feature list]

## How to Test
- Start: `uvicorn src.server:app --reload --port $PORT`
- Navigate to: http://localhost:$PORT/[route] (PORT from state.json `dev_server_port`)
- Test: [specific user actions]

## Test Results
- `pytest` exit code: 0
- Tests: X passed, coverage: Y%

## Known Limitations
- [Any deviations from contract]
```

## On Sprint ADVANCE

When score >= target, check the evaluator's bug list:
- **Bugs found** → ADVANCE_WITH_FIXES. Fix ALL bugs + write regression tests first. Non-bug findings (suggestions, polish) can be deferred. No re-evaluation needed.
- **No bugs** → ADVANCE directly.

Then increment `feature_sprints_since_last_integration` and `feature_sprints_since_last_presentation`.

**Infra batch** — if `feature_sprints_since_last_integration` reaches 3:
1. Launch Install + Integration in parallel with next sprint's Build
2. Update `current_phase` to `["BUILD_AGENT", "INSTALLATION", "INTEGRATION"]`
3. Reset `feature_sprints_since_last_integration` to 0

**Content batch** — if `feature_sprints_since_last_presentation` reaches 5:
1. Launch Doc + Presentation in parallel with next sprint's Build
2. Update `current_phase` to include `"DOCUMENTATION"` and `"PRESENTATION"`
3. Reset `feature_sprints_since_last_presentation` to 0

Both can trigger simultaneously. Start the next sprint immediately — batch agents do NOT block Build.

## On Iteration 2+

When re-entering a sprint after evaluator feedback:
1. Read `harness/evaluations/sprint-N-eval.md` — check the **Prioritized Fix List**
2. Work fixes **in priority order** (P0 → P1 → P2 → P3). If context is tight, P0 and P1 are mandatory; P2-P3 can be deferred.
3. For each bug: fix it, write a regression test, mark it done in the handoff
4. Do NOT re-architect — make targeted fixes
5. Update handoff with a **Fixes Applied** section listing each eval bug ID and what was done
6. VQA and Evaluator run in parallel again on re-evaluation

The **Fixes Applied** section prevents duplicate work across iterations:
```markdown
## Fixes Applied (Iteration N)
- BUG-3-001: Fixed — added null check in src/routers/items.py:45, regression test in tests/regression/data/test_null_items.py
- BUG-3-002: Fixed — corrected SQL query in src/services/loan.py:82
- BUG-3-003: Deferred (P3 polish) — will address if iteration budget allows
```

## Databricks Connection Patterns

```python
# Lakebase (OLTP): psycopg with env vars
conn = psycopg.connect(host=os.environ["LAKEBASE_HOST"], ...)

# Delta Lake (DWH): databricks-sql-connector
from databricks import sql as dbsql
conn = dbsql.connect(server_hostname=os.environ["DATABRICKS_HOST"], ...)

# FMAPI: databricks-sdk
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
response = w.serving_endpoints.query(name="endpoint", input={"messages": [...]})
```

See `harness/templates/databricks-app/ENVIRONMENT.md` for Databricks Apps runtime constraints. No file > 200 lines, no function > 40 lines.

## Feature Flags

Wrap new features in a flag check so they can be toggled without redeployment:

```python
# src/lib/feature_flags.py
import os, json
_FLAGS = json.loads(os.environ.get("FEATURE_FLAGS", "{}"))
def feature_enabled(name: str) -> bool:
    return _FLAGS.get(name, True)  # default ON
```

Usage in routers: `if not feature_enabled("bulk_export"): raise HTTPException(404)`. Usage in frontend: conditionally render UI based on `/api/feature-flags` endpoint. Document each flag name in the sprint contract.

## Analytics Events

Emit structured events on key user actions. Add event tracking alongside CRUD operations:

```python
# src/lib/analytics.py
import json, logging
analytics_logger = logging.getLogger("analytics")
def track(event: str, properties: dict, user_id: str = "anonymous"):
    analytics_logger.info(json.dumps({"event": event, "properties": properties, "user_id": user_id}))
```

Call `track("bookmark_created", {"category": "work"}, user_id)` in service layer. List all tracked events in the sprint handoff under `## Analytics Events Added`.

---

# Comprehensive Testing Guide

Build Agent writes unit + integration tests. Evaluator Agent does browser E2E testing (see [exhaustive-testing-guide.md](exhaustive-testing-guide.md)).

## Test Directory Structure

Organize tests by **type first, then feature**. NEVER by sprint number.

```
tests/
├── conftest.py                          # Shared fixtures (DB, client, cleanup)
├── unit/                                # Pure logic, no I/O
│   ├── conftest.py                      # Unit-specific fixtures
│   ├── bookmarks/
│   │   ├── test_service.py              # BookmarkService business logic
│   │   └── test_validation.py           # Input validation rules
│   ├── ecl/
│   │   ├── test_calculator.py           # ECL formula calculations
│   │   └── test_stage_transfer.py       # Stage transition logic
│   └── shared/
│       ├── test_formatters.py           # Date, currency, URL formatters
│       └── test_config.py               # Settings / env var parsing
├── integration/                         # API endpoints, DB round-trips
│   ├── conftest.py                      # Integration-specific fixtures (client)
│   ├── bookmarks/
│   │   └── test_api.py                  # POST/GET/DELETE /api/bookmarks
│   ├── ecl/
│   │   └── test_api.py                  # POST /api/ecl/calculate, etc.
│   └── health/
│       └── test_api.py                  # GET /api/health
├── regression/                          # Bug-triggered tests, grouped by domain
│   ├── routing/
│   │   └── test_spa_catchall.py         # BUG: SPA catch-all shadowed API routes
│   ├── settings/
│   │   └── test_null_safety.py          # BUG: null scenarios crashed admin page
│   └── compatibility/
│       └── test_python311.py            # BUG: nested f-string quotes on 3.11
└── deployment/                          # Databricks Apps compatibility
    └── test_databricks_apps_compat.py   # Port config, syntax compat, SPA routing
```

### Naming Rules

| Rule | Good | Bad |
|------|------|-----|
| Group by feature domain | `tests/unit/bookmarks/test_service.py` | `tests/test_sprint1.py` |
| Group regressions by what broke | `tests/regression/routing/test_spa_catchall.py` | `tests/regression/test_sprint3_bugs.py` |
| Test file names describe content | `test_stage_transfer.py` | `test_ecl.py` (too vague) |
| One concern per file | `test_validation.py`, `test_service.py` | `test_all_bookmark_stuff.py` |

**When adding a new feature**: Create `tests/unit/[feature]/` and `tests/integration/[feature]/`. Never add tests to a "sprint" file.

**When fixing a bug**: Add to `tests/regression/[domain]/`. The domain is what the bug affected (routing, settings, auth), not which sprint found it. The docstring still references the bug ID.

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

Frontend test structure mirrors the backend:
```
src/__tests__/
├── unit/
│   ├── bookmarks/
│   │   └── BookmarkForm.test.tsx
│   └── shared/
│       └── formatters.test.ts
├── integration/
│   └── bookmarks/
│       └── BookmarkList.test.tsx
└── regression/
    ├── routing/
    │   └── navigation.test.tsx
    └── rendering/
        └── null-safety.test.tsx
```

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
# tests/unit/loans/test_service.py
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
# tests/integration/loans/test_api.py
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

## Regression Tests (Bug → Fix → Test → Never Again)

**Every bug found during evaluation MUST produce a regression test.** This is non-negotiable. The cycle:

```
Evaluator finds bug → Build Agent fixes bug → Build Agent writes regression test → pytest verifies fix → Bug CANNOT recur
```

### Regression Test Protocol

1. **Evaluator reports bug** in `sprint-N-eval.md` with reproduction steps
2. **Build Agent creates** the test in the appropriate domain folder under `tests/regression/[domain]/`
3. **Test MUST fail** before the fix is applied (verify the bug is real)
4. **Test MUST pass** after the fix (verify the fix works)
5. **Test runs forever** — never deleted, ensures the bug stays dead

### Where to Put Regression Tests

Group by **what broke**, not when it broke:

| Bug Domain | Test Location | Example |
|-----------|---------------|---------|
| API routing | `tests/regression/routing/` | SPA catch-all shadowed `/api/*` |
| Data handling | `tests/regression/data/` | Null scenarios crashed settings page |
| Compatibility | `tests/regression/compatibility/` | Python 3.11 f-string syntax |
| Auth / permissions | `tests/regression/auth/` | Token refresh race condition |
| UI rendering | `src/__tests__/regression/rendering/` | Component crashes on empty props |
| Navigation | `src/__tests__/regression/routing/` | Back button loses state |

### Regression Test Template

Every regression test follows this pattern:
1. File in `tests/regression/[domain]/test_[what_broke].py`
2. Module docstring describes the domain
3. Each test method has a docstring citing `BUG-NNN:` with root cause and fix
4. Test verifies the fix is applied

```python
# tests/regression/routing/test_spa_catchall.py
"""Regression: SPA catch-all must not shadow API routes."""

class TestSPACatchallRegression:
    def test_models_endpoint_returns_json(self, client):
        """BUG-003: /api/models returned SPA HTML instead of JSON.
        Root cause: catch-all route /{full_path:path} shadowed the models API.
        Fix: guard clause rejects api/* paths in SPA handler.
        """
        resp = client.get("/api/models")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
```

Frontend regressions follow the same pattern in `src/__tests__/regression/[domain]/`.

### Evaluator: Regression Verification Checklist

```markdown
- [ ] Every bug from this sprint's eval has a corresponding regression test
- [ ] Regression tests from ALL previous evaluations still pass
- [ ] `tests/regression/` directory exists and is not empty (after first eval with bugs)
- [ ] Each regression test has a docstring citing the bug ID and root cause
- [ ] Regression tests are in domain-appropriate folders (not sprint folders)
```

## Databricks Apps Deployment Tests

**Every deployment MUST be validated.** The Databricks Apps runtime is Python 3.11 on Ubuntu 22.04 — code that works locally on Python 3.12+ may fail in production.

### Pre-Deployment Validation

```python
# tests/deployment/test_databricks_apps_compat.py
"""Validate code is compatible with Databricks Apps runtime."""
import ast
import glob
import sys
import pytest

class TestDatabricksAppsCompat:
    def test_all_python_files_parse_on_311(self):
        """All .py files must parse without SyntaxError on Python 3.11.
        Databricks Apps runs Python 3.11 — features like PEP 701
        (nested f-string quotes) are NOT available.
        """
        errors = []
        for path in glob.glob("**/*.py", recursive=True):
            if ".venv" in path or "node_modules" in path:
                continue
            with open(path) as f:
                try:
                    ast.parse(f.read(), filename=path)
                except SyntaxError as e:
                    errors.append(f"{path}:{e.lineno}: {e.msg}")
        assert not errors, f"Syntax errors found:\n" + "\n".join(errors)

    def test_no_hardcoded_ports(self):
        """App must use DATABRICKS_APP_PORT env var, not hardcoded port."""
        import re
        for path in glob.glob("**/*.py", recursive=True):
            if ".venv" in path or "test" in path:
                continue
            with open(path) as f:
                content = f.read()
            # Allow port in env var fallback: os.environ.get("...", 8000)
            # Flag: uvicorn.run(app, port=8000) without env var
            if "uvicorn.run" in content and "DATABRICKS_APP_PORT" not in content:
                if re.search(r'uvicorn\.run.*port=\d+', content):
                    pytest.fail(f"{path}: hardcoded port in uvicorn.run — use DATABRICKS_APP_PORT")

    def test_spa_catchall_does_not_shadow_api(self):
        """SPA catch-all route must not intercept /api/* requests."""
        from httpx import ASGITransport, AsyncClient
        from app import app  # adjust import
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/health")
            assert resp.headers.get("content-type", "").startswith("application/json"), \
                "/api/health returned non-JSON — SPA catch-all may be shadowing API routes"
```

### Build Agent: Deployment Checklist

```markdown
- [ ] `ast.parse()` passes for all .py files (Python 3.11 compat)
- [ ] Port read from `DATABRICKS_APP_PORT` env var with fallback
- [ ] No nested f-string quotes (use single quotes inside f-strings)
- [ ] `app.yaml` exists with correct command and env vars
- [ ] `requirements.txt` pins all dependencies
- [ ] SPA catch-all excludes `/api/*` and `/docs/*` paths
```

## Running Tests by Category

```bash
# All tests
pytest

# By type
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest tests/regression/              # Regression tests only
pytest tests/deployment/              # Deployment compat only

# By feature
pytest tests/unit/bookmarks/          # All bookmark unit tests
pytest tests/integration/ecl/         # All ECL integration tests

# By type + feature
pytest tests/unit/bookmarks/ tests/integration/bookmarks/ tests/regression/data/

# With coverage
pytest --cov=src --cov-report=term tests/unit/ tests/integration/
```

## Build Agent Protocol

After each sprint: write unit tests (`tests/unit/[feature]/`) → write integration tests (`tests/integration/[feature]/`) → write regression tests for any bugs found (`tests/regression/[domain]/`) → run deployment compat tests → `pytest` → `pytest --cov=src --cov-report=term` (≥70%) → include results in handoff.

## Evaluator Verification

```markdown
- [ ] `pytest` passes with zero failures
- [ ] New tests added for this sprint's features in `tests/unit/[feature]/` and `tests/integration/[feature]/`
- [ ] Regression tests added for ALL bugs found in this sprint's evaluation (in `tests/regression/[domain]/`)
- [ ] Regression tests from previous evaluations still pass
- [ ] Deployment compat tests pass (Python 3.11, port config, SPA routing)
- [ ] Unit tests cover validation, business logic, data transformers
- [ ] Integration tests cover all endpoints (happy + error paths)
- [ ] Coverage on business logic ≥ 70%
- [ ] No test files named by sprint number (e.g., test_sprint3.py)
```

---

# Production Readiness Guide — Mini SaaS Quality Bar

Every sprint must meet these standards. Build Agent implements them incrementally; Evaluator checks every sprint.

## 15 Mandatory Requirements

### 1. Error Handling & Resilience
- **Backend**: Global exception handler → structured JSON `{"detail": {"code": int, "message": str}}`. No stack traces in responses.
- **Frontend**: Error boundary, user-friendly API error messages, offline state handling, inline form validation errors.

Pattern: `BaseHTTPMiddleware` that catches all exceptions → logs `[method] path → 500: exc` → returns `JSONResponse(500, {"detail": {"code": 500, "message": "Internal server error"}})`.

### 2. Loading States & Skeleton Screens
Every async operation: skeleton screens on page load, spinner on button actions, disabled submit during form submission. Never blank screens.

### 3. Toast Notifications
Create/update/delete → success toast. Errors → red error toast. Auto-dismiss 3-5s, dismissible, stacked, color-coded (green/red/yellow/blue).

### 4. Environment Configuration & Databricks Apps Compliance

No hardcoded URLs/secrets. Use pydantic-settings. `.env.example` committed, `.env` gitignored. Fail fast if required var missing. See [installer-guide.md](installer-guide.md) for `.env.example` template.

#### Databricks Apps System Environment

**Runtime**: Ubuntu 22.04 LTS, **Python 3.11** (NOT 3.12+), Node.js 22.16, up to 2 vCPUs / 6 GB RAM.

**CRITICAL — Python 3.11 Constraints**:
- No PEP 701 nested f-string quotes: `f"...{x.get("key")}"` is a **SyntaxError**. Use single quotes: `f"...{x.get('key')}"`
- No `type` keyword for type aliases (PEP 695) — use `TypeAlias` from `typing`
- No exception groups with `except*` unless you need them

**System environment variables** (auto-injected by Databricks, do NOT set manually):

| Variable | Purpose | Usage |
|----------|---------|-------|
| `DATABRICKS_APP_PORT` | Port to listen on | **MUST** use this, not hardcoded `8000` |
| `DATABRICKS_APP_NAME` | App identifier | Logging, telemetry |
| `DATABRICKS_HOST` | Workspace URL | SDK initialization, API calls |
| `DATABRICKS_WORKSPACE_ID` | Workspace ID | Multi-workspace routing |
| `DATABRICKS_CLIENT_ID` | Service principal ID | OAuth M2M auth |
| `DATABRICKS_CLIENT_SECRET` | Service principal secret | OAuth M2M auth |

**Framework auto-configuration** (set automatically, don't override):
- FastAPI/Uvicorn: `UVICORN_PORT`, `UVICORN_HOST=0.0.0.0`
- Streamlit: `STREAMLIT_SERVER_PORT`, `STREAMLIT_SERVER_ADDRESS=0.0.0.0`
- Gradio: `GRADIO_SERVER_PORT`, `GRADIO_SERVER_NAME=0.0.0.0`
- Flask: `FLASK_RUN_PORT`, `FLASK_RUN_HOST=0.0.0.0`

**Telemetry** (when enabled): `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4314`, `OTEL_EXPORTER_OTLP_PROTOCOL=grpc`

Pattern: `pydantic_settings.BaseSettings` class reading `DATABRICKS_APP_PORT`, `DATABRICKS_HOST`, `DATABRICKS_APP_NAME` from env (auto-injected), plus app-specific vars like `LAKEBASE_INSTANCE_NAME`. Use `env_file = ".env"` for local dev.

#### app.yaml Template

```yaml
command:
  - python
  - app.py
env:
  - name: LAKEBASE_INSTANCE_NAME
    value: "your-instance-name"
  - name: LAKEBASE_DATABASE
    value: "databricks_postgres"
resources:
  - name: lakebase-instance
    type: lakebase
    lakebase:
      instance: "your-instance-name"
```

#### Entrypoint Pattern

`app.py` MUST read port: `port = int(os.environ.get("DATABRICKS_APP_PORT", 8000))` then `uvicorn.run(app, host="0.0.0.0", port=port)`.

#### SPA Catch-All Safety

When serving a React SPA from FastAPI, the catch-all `/{full_path:path}` MUST skip `api/` and `docs/` prefixes (raise 404), serve static files if they exist, else return `index.html`.

### 5. Data Validation (Client + Server)
- **Client**: Required fields marked, inline validation on blur, format validation (URL, email, numbers), max length with counter.
- **Server**: Pydantic models with `extra="forbid"`, `Field(gt=0)`, `field_validator` for sanitization. Return specific per-field errors.

### 6. Dark Mode
Detect `prefers-color-scheme`, manual toggle, persist in localStorage, all colors as CSS custom properties, both themes fully usable.

### 7. SEO & Meta Tags
Title, description, OG tags, favicon in `<head>`.

### 8. Basic Accessibility (a11y)
Semantic HTML (`<nav>`, `<main>`, `<button>`), keyboard navigation (Tab/Enter/Escape), visible focus rings, `aria-label` on icon buttons, `<label>` for every input, 4.5:1 contrast ratio, `alt` on images.

### 9. Performance
- Page load <3s on localhost, no unnecessary re-renders, lazy-loaded images, clean up listeners on unmount
- **Core Web Vitals**: LCP <2.5s, INP <200ms, CLS <0.1 (use `lighthouse_audit` MCP to verify)
- **Bundle size**: <500KB JS gzipped. Code-split routes. Tree-shake unused imports.
- **DB queries**: No query >100ms. No N+1 queries (use eager loading / joins). Index all filtered/sorted columns.
- **Caching**: Static assets: `Cache-Control: max-age=31536000, immutable`. API responses: `no-cache` or short TTL for dynamic data.

### 10. Rate Limiting & Security
CORS configured, `slowapi` rate limiting on sensitive endpoints. In Databricks Apps, OAuth handles auth automatically.

### 11. Seed Data / Demo Mode + Onboarding
First-run shows realistic sample data or onboarding prompt. `python seed.py` seeds remote Lakebase. "Reset to demo data" option.
- **Onboarding flow**: First-time user sees guided tour or welcome modal explaining key features
- **Empty state CTAs**: Every list/table with no data shows "Add your first X" with a prominent action button
- **Progressive disclosure**: Advanced features hidden behind "Show advanced" or settings panel — don't overwhelm new users
- **Tooltips**: Complex features have `title` or popover hints on first use

### 12. Data Governance & Compliance
- **PII in logs**: Mask sensitive fields (email, phone, tokens) in all log output. Never log request bodies containing passwords.
- **Data export**: `GET /api/users/{id}/export` returns all user data as JSON (GDPR right of access)
- **Data deletion**: `DELETE /api/users/{id}/data` cascades to all related records (GDPR right to erasure). Soft-delete with 90-day retention, then hard-delete.
- **RBAC**: Sensitive endpoints (admin, delete, bulk ops) require role check. At minimum: `user` and `admin` roles.
- **Audit trail**: Log who performed destructive actions (delete, bulk update, permission change) with timestamp and user ID.

### 13. Feature Flags
- New features wrapped in `feature_enabled("feature_name")` check (env var or JSON config)
- Default: ON for all flags (no hidden features in production unless explicitly gated)
- Graceful degradation: when flag is OFF, UI hides the feature cleanly — no broken links or empty sections
- Flag state visible in admin/settings page
- Pattern: `feature_enabled(name)` reads `FEATURE_FLAGS` env var (JSON dict), returns `_FLAGS.get(name, True)` — default ON.

### 14. Analytics & Telemetry
- Track key user actions: create, update, delete, search, export, login
- Structured event format: `{"event": "bookmark_created", "properties": {"category": "work"}, "timestamp": "...", "user_id": "..."}`
- No PII in analytics events (no email, name, or IP in properties)
- Funnel-critical events identified in spec and tracked (e.g., signup → first action → retention action)
- Implementation: emit events to a lightweight store (SQLite table, Lakebase table, or stdout JSON lines) — no external analytics SDK required

### 15. CI/CD Enhancement
Extends the CI/CD Pipeline section below:
- Tests run on every PR (not just push to main)
- Lint (`ruff check`) + type-check (`mypy` or `pyright`) in CI
- Frontend build verification (`npm run build` must succeed)
- Staging deploy step: deploy to Databricks Apps staging workspace before production
- Production checklist gate: all tests pass + evaluator score ≥ quality target

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`): trigger on `push` + `pull_request`.
- **Backend job**: Python 3.11, `pip install -r requirements.txt`, `ruff check src/`, `pytest --cov=src`. Pass Databricks/Lakebase secrets via `${{ secrets.* }}`.
- **Frontend job**: Node 22, `cd frontend && npm ci && npm test && npm run build`.

## Sprint Rollout Schedule

| Sprint 1 (foundational) | Sprint 2 (after CRUD) | Sprint 3+ | Final |
|---|---|---|---|
| Error handling | Toast notifications | Dark mode | CI/CD enhancement (#15) |
| Loading states | Client-side validation | SEO meta tags | Performance audit (#9) |
| Env config | Seed data + onboarding (#11) | Feature flags (#13) | Data governance (#12) |
| Server validation | Rate limiting / CORS | Analytics events (#14) | |
| Semantic HTML, a11y basics | Keyboard nav, RBAC basics | Audit trail | |

## Evaluator Checklist

```markdown
- [ ] Structured error JSON, no stack traces
- [ ] Loading states on all async operations
- [ ] Toast notifications for CRUD actions
- [ ] No hardcoded URLs/secrets, pydantic-settings used
- [ ] Client + server validation on forms
- [ ] Dark mode toggle, both themes usable
- [ ] Semantic HTML, keyboard nav, focus visible, form labels
- [ ] Performance: LCP <2.5s, no N+1 queries, bundle <500KB
- [ ] Seed data + onboarding flow on first run
- [ ] Data governance: PII masked in logs, export/delete endpoints, RBAC
- [ ] Feature flags: new features gated, graceful degradation
- [ ] Analytics: key actions tracked, no PII in events
- [ ] CI/CD: tests on PR, lint + type-check, build verification
```

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
| `address already in use` | **Don't kill — find a free port.** Use `find_free_port()` from SKILL.md Port Management. Update `dev_server_port` in state.json. |
| Multiple dev servers running | Check terminals: `lsof -i :8000-8100 -i :5173`. Only kill processes from THIS project. **Never kill another harness project's server.** |
| Port blocked by system | Use `find_free_port(8000, 8100)` — it scans automatically |

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
| API calls fail in dev | Check proxy config in `vite.config.ts` — target must match `dev_server_port` from state.json. |

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

1. **Server won't start**: Port in use? Use `find_free_port()` — don't kill other processes. Update `dev_server_port` in state.json.
2. **Browser testing fails**: Verify the URL matches `dev_server_port` from state.json. Try `navigate_page url=http://localhost:$PORT/` manually.
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


# Context Reset — Harness Run 5

## Current State
- **Phase**: BUILD_AGENT
- **Sprint**: 3 (next to build)
- **Quality Target**: 9.0/10
- **Tests**: 485 passing, 61 skipped, 1 pre-existing failure (test_get_jobs_config), 45 pre-existing failures in test_reports_routes.py (excluded)

## Score Trajectory
- Sprint 1 (Audit Trail): [8.01, 9.08] → PASS
- Sprint 2 (Simulation Reproducibility): [6.45, 7.25, 7.95] → ADVANCE with debt

## Architecture Decisions
- Hash-chained audit trail in `domain/audit_trail.py` (append-only, SHA-256)
- Config change tracking in `config_audit_log` table
- Attestation data + ECL hash stored at sign-off in `ecl_workflow` table
- Random seed support in Monte Carlo engine (deterministic RNG)
- Per-product convergence diagnostics (per-simulation path tracking)
- Run comparison endpoint with absolute + relative deltas

## Remaining Goals (5 of 7)
1. **Reporting & Export** — Prior-period comparatives, PDF export, IFRS 7.35J write-offs
2. **Attestation & ECL Hash** — Already partially done in Sprint 1 (attestation persisted, hash computed). Needs frontend wiring and verification endpoint.
3. **Period-End Close** — Orchestrate full pipeline as single workflow
4. **Config Change Tracking** — Already partially done in Sprint 1 (config_audit_log). Needs Admin UI tab.
5. **Installation Fixes** — Add scipy to requirements.txt, improve health check

## Sprint 2 Debt
- Seed not persisted to model_runs DB table
- Compare endpoint only compares aggregate metrics (not per-product/stage/scenario)
- Simulation cap hardcoded at 50,000 (not configurable via admin config)

## Exact Next Step
Write `harness/contracts/sprint-3.md` for Goal 3 (Reporting & Export), then implement:
- Prior-period ECL storage and retrieval
- IFRS 7.35H comparative disclosure
- IFRS 7.35J write-off disclosure
- PDF export using fpdf2 or reportlab

## Files to Read on Resume
1. `harness/state.json` — current state
2. `harness/progress.md` — sprint history
3. `harness/spec.md` — product goals
4. `harness/evaluations/sprint-2-eval.md` — latest evaluation
5. `harness/sme/domain-brief-run5.md` — SME audit (10 personas, 72 gaps)
6. Run `pytest tests/ --ignore=tests/unit/test_reports_routes.py -q` to verify baseline

## Harness Enforcement Rules
- Evaluator MUST be a separate Task subagent (never self-evaluate)
- All artifacts required before advancing: contract, handoff, evaluation (from subagent)
- Score trajectory required in state.json for every completed sprint
- Max 3 iterations per sprint before advancing with debt

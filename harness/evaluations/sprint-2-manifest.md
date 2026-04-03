# Sprint 2 Evaluation Manifest

## Acceptance Criteria Verification

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | `random_seed` parameter added to SimulationConfig (optional int, auto-generated if None) | PASS | `routes/simulation.py:23` — `random_seed: Optional[int] = None` in Pydantic model. Test `test_random_seed_optional` confirms default is None. |
| 2 | ecl_engine.run_simulation() uses seed to initialize numpy RNG — same seed + same data = identical ECL | PASS | `ecl_engine.py:269-271` — auto-generates seed if None, creates `np.random.default_rng(random_seed)`. Test `test_same_seed_same_result` runs seed=42 twice and asserts `ecl_a == ecl_b` (exact equality). Test `test_different_seed_different_result` confirms seed=42 vs seed=99 differ. |
| 3 | Seed stored in simulation result metadata and in model_runs table | PARTIAL | Seed is stored in `run_metadata` dict (line 501: `"random_seed": random_seed`). Test `test_seed_stored_in_metadata` confirms. However, the seed is NOT persisted to the `model_runs` Postgres table — the table schema has no `random_seed` column, and `save_model_run()` does not accept or store it. The seed only lives in the in-memory response. |
| 4 | GET `/api/simulation/compare?run_a={id}&run_b={id}` returns delta by product, stage, scenario | FAIL | Endpoint exists (`routes/simulation.py:259-285`) but returns model_run metadata (satellite model comparison summary), NOT simulation ECL deltas by product/stage/scenario. The handoff explicitly acknowledges this: "returns model_run metadata comparison rather than full ECL delta." No absolute or relative (%) differences are computed. Response is essentially a stub with a string message. No tests exist for this endpoint. |
| 5 | Convergence diagnostics: running mean and 95% CI width per product included in simulation results | PARTIAL | `convergence_by_product` dict is computed (`ecl_engine.py:484-497`) with mean_ecl, std_ecl, ci_95_width, ci_95_pct per product. However, the CI calculation has a conceptual issue: it computes std over the per-loan weighted ECL values within a product (cross-sectional std), not the Monte Carlo standard error of the mean ECL estimate. The `n_check = max(1, n_sims)` denominator uses n_sims but the std is computed over n_loans, conflating two different dimensions. Additionally, there is no "running mean" — only a final snapshot. The portfolio-level `_convergence_check_from_paths` function (used per-scenario) is correct but not exposed at the product level. |
| 6 | Simulation cap raised from 5,000 to 50,000 (configurable via admin config) | PARTIAL | Backend validation cap raised to 50,000 (`routes/simulation.py:230`). Test `test_cap_raised_to_50000` confirms Pydantic accepts 50,000. Test `test_validate_simulation_too_many_sims` validates 60,000 is rejected. However, the cap is hardcoded (not configurable via admin config). Frontend still has `max={5000}` in SimulationPanel.tsx:392. |
| 7 | 10+ new tests for reproducibility, comparison, convergence | PARTIAL | Exactly 10 new tests in `test_simulation_seed.py`. Covers reproducibility (4), convergence (3), config (3). However, 0 tests for the comparison endpoint. The contract says "reproducibility, comparison, convergence" — comparison is untested. |
| 8 | All existing 472 tests still pass (excluding pre-existing test_reports_routes failures) | PASS | 481 passed, 1 failed (pre-existing `test_get_jobs_config`), 61 skipped. The 1 failure is pre-existing (jobs config assertion), not introduced by Sprint 2. |

## Element Checklist

| Element | Status | Notes |
|---------|--------|-------|
| `random_seed` in SimulationConfig | VERIFIED | Pydantic field, Optional[int], default None |
| `np.random.default_rng(seed)` usage | VERIFIED | Line 271, all RNG calls use this instance |
| Seed auto-generation | VERIFIED | Line 269-270, uses `np.random.default_rng().integers(0, 2**31)` |
| Seed in run_metadata response | VERIFIED | Line 501 |
| Seed in model_runs DB table | NOT PRESENT | Table schema lacks column |
| Compare endpoint exists | VERIFIED | GET /api/simulation/compare |
| Compare returns product delta | NOT PRESENT | Returns model_run metadata, not ECL deltas |
| Compare returns stage delta | NOT PRESENT | Not implemented |
| Compare returns scenario delta | NOT PRESENT | Not implemented |
| Compare returns absolute differences | NOT PRESENT | Not implemented |
| Compare returns relative (%) differences | NOT PRESENT | Not implemented |
| Convergence per product | VERIFIED | convergence_by_product dict in metadata |
| Convergence running mean | NOT PRESENT | Only final snapshot, no running mean series |
| Convergence CI width correct | ISSUE | Std computed over loans, divided by sqrt(n_sims) — dimension mismatch |
| Cap raised to 50,000 backend | VERIFIED | Validation endpoint rejects >50,000 |
| Cap configurable via admin config | NOT PRESENT | Hardcoded |
| Cap raised in frontend | NOT PRESENT | Frontend still max=5000 |
| Tests for comparison endpoint | NOT PRESENT | 0 tests |
| Tests for reproducibility | VERIFIED | 4 tests, all pass |
| Tests for convergence | VERIFIED | 3 tests, all pass |

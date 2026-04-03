# Sprint 2 Contract: Reproducible & Comparable Simulations (Simulation Persona)
STATUS: AGREED

## Scope
Add random seed support to the Monte Carlo ECL engine for reproducible results. Implement run comparison endpoint. Add convergence diagnostics. Raise simulation cap.

## Acceptance Criteria
1. [ ] `random_seed` parameter added to SimulationConfig (optional int, auto-generated if None)
2. [ ] ecl_engine.run_simulation() uses seed to initialize numpy RNG — same seed + same data = identical ECL
3. [ ] Seed stored in simulation result metadata and in model_runs table
4. [ ] GET `/api/simulation/compare?run_a={id}&run_b={id}` returns delta by product, stage, scenario
5. [ ] Convergence diagnostics: running mean and 95% CI width per product included in simulation results
6. [ ] Simulation cap raised from 5,000 to 50,000 (configurable via admin config)
7. [ ] 10+ new tests for reproducibility, comparison, convergence
8. [ ] All existing 472 tests still pass (excluding pre-existing test_reports_routes failures)

## How to Test
- POST `/api/simulate` with `{"random_seed": 42, ...}` twice — verify identical ECL results
- POST `/api/simulate` with different seeds — verify different results
- GET `/api/simulation/compare?run_a=X&run_b=Y` — verify delta computation
- Run `pytest` — 482+ tests pass

## Out of Scope
- Variance reduction techniques (importance sampling, antithetic variates)
- PD term structure model improvements
- Frontend UI changes for comparison

## Domain Criteria (SME)
- Reproducibility is required by EBA/GL/2017/16 for model validation
- Convergence diagnostics should report at the product level (not just portfolio)
- Run comparison should show both absolute and relative (%) differences

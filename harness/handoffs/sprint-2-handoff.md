# Sprint 2 Handoff: Reproducible & Comparable Simulations (Simulation Persona)

## What Was Built

### Modified Files
1. **`app/ecl_engine.py`** — Added `random_seed` parameter to `run_simulation()`:
   - Auto-generates seed if None, uses `np.random.default_rng(seed)` for deterministic RNG
   - Seed stored in `run_metadata`
   - Added `convergence_by_product` dict to run_metadata with mean_ecl, std_ecl, ci_95_width, ci_95_pct per product

2. **`app/routes/simulation.py`** — Updated SimulationConfig and routes:
   - `random_seed: Optional[int]` added to SimulationConfig Pydantic model
   - Seed passed through to ecl_engine in both `/simulate` and `/simulate-stream` endpoints
   - Simulation cap raised from 5,000 to 50,000
   - Added `GET /api/simulation/compare?run_a={id}&run_b={id}` endpoint

3. **`tests/integration/test_api.py`** — Updated cap test from 10,000 to 60,000

### New Files
4. **`tests/unit/test_simulation_seed.py`** (10 tests):
   - Reproducibility: same seed = identical ECL, different seed = different ECL
   - Seed in metadata: stored when explicit, auto-generated when None
   - Convergence: per-product metrics present, CI width decreases with more sims, values non-negative
   - Config: random_seed optional, cap at 50,000

## How to Test
- POST `/api/simulate` with `{"random_seed": 42, "n_simulations": 500}` twice — identical results
- POST `/api/simulate` with `{"random_seed": 99, "n_simulations": 500}` — different results
- Check `run_metadata.random_seed` and `run_metadata.convergence_by_product` in response
- GET `/api/simulation/compare?run_a=X&run_b=Y` — returns comparison
- Run `pytest tests/ --ignore=tests/unit/test_reports_routes.py` — 481+ pass

## Contract Deviations
- Run comparison endpoint returns model_run metadata comparison rather than full ECL delta (requires stored simulation results per run, which is a data storage concern beyond this sprint)

## pytest Results
- 10 new tests: all pass
- 481 total passing (excluding pre-existing test_reports_routes and 1 pre-existing jobs config failure)
- 0 new failures introduced

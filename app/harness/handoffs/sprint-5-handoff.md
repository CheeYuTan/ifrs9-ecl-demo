# Sprint 5 Handoff: ECL Engine — Monte Carlo Correctness

## What Was Built

141 new tests covering all 9 files in the `ecl/` sub-package:

| Module | Tests | Coverage Focus |
|--------|-------|---------------|
| `ecl/helpers.py` | 18 | `_emit`, `_convergence_check`, `_convergence_check_from_paths`, `_df_to_records` (Decimal, datetime, date, NaN, empty DF) |
| `ecl/constants.py` | 15 | Fallback LGD values, satellite coefficients, scenario weights sum to 1.0, range validation |
| `ecl/config.py` | 11 | `_t()` qualified names, `_build_product_maps()` fallbacks + DB products, `_load_config()` success/failure paths |
| `ecl/data_loader.py` | 4 | SQL query correctness, missing column fill-in, existing column preservation |
| `ecl/monte_carlo.py` (prepare) | 14 | Derived columns (stage, gca, eir, base_pd, rem_q, base_lgd), null handling, LGD defaults |
| `ecl/monte_carlo.py` (core math) | 20 | Cholesky correlation (rho=0, 0.5, -0.4, 0.99), lognormal shocks, PD/LGD clipping, discount factor, amortization, aging, prepayment, pd_mult/lgd_mult scaling, survival, determinism, batch consistency |
| `ecl/monte_carlo.py` (hand-calc) | 4 | Single-quarter ECL = PD_q x LGD x GCA x DF verified to 1e-6 rel tolerance, two-quarter with survival, amortizing EAD, scenario weighting |
| `ecl/aggregation.py` | 12 | Output structure, coverage ratio formula, percentile ordering, cross-product count, stage summary sums, convergence diagnostics, JSON serializability |
| `ecl/simulation.py` | 10 | Deterministic seeds, custom weights, missing scenarios get defaults, progress phases, metadata params |
| Edge cases | 15 | Single loan, very small PD (1e-6), very large EAD (1e12), PD=1 certain default, LGD=1 total loss, single/many scenarios, Stage 1 vs 2 vs 3 ECL ordering, mixed products, convergence improvement, no NaN |
| Numerical stability | 5 | Small GCA, zero EIR, high volatility, correlation near 1.0, 100-loan portfolio |
| Package exports | 6 | All `__all__` symbols verified |

### Key Domain Validations
- **ECL = PD x LGD x EAD x DF** verified with hand-calculated values (1e-6 relative tolerance)
- **Cholesky decomposition** verified: empirical correlation matches input rho (±0.02 for 100K samples)
- **Stage 1 horizon** capped at 4 quarters (12 months)
- **Stage 2/3** use full remaining life — higher ECL than Stage 1
- **Aging factor** only applies to Stage 2/3 (no effect on Stage 1)
- **Scenario weighting**: weighted ECL = sum(w_i x ECL_i), weights must sum to 1.0
- **PD/LGD clipping** enforced at floor/cap bounds

## How to Test

```bash
cd /Users/steven.tan/Expected\ Credit\ Losses/app
source .venv/bin/activate
python -m pytest tests/unit/test_qa_sprint_5_ecl_engine.py -v
```

## Test Results

- **Sprint 5 tests**: 141 passed, 0 failed (42s)
- **Full suite**: 3,412 passed, 61 skipped, 0 failed (112s)
- **New tests this sprint**: 141
- **Cumulative new tests (Sprints 1-5)**: 932
- **Regressions**: 0
- **Bugs found**: 0 (ECL engine implementation is solid)

## Files Changed

- `tests/unit/test_qa_sprint_5_ecl_engine.py` — NEW (141 tests)
- `harness/contracts/sprint-5.md` — Updated for this QA audit run
- `harness/handoffs/sprint-5-handoff.md` — This file
- `harness/state.json` — Updated test counts and sprint state

## Known Limitations

- Tests use zero-volatility scenarios for hand-calculation verification (stochastic verification uses statistical tolerances)
- Large portfolio test uses 100 loans x 200 sims (not full-scale 10K+ loans)
- `get_defaults()` not deeply tested here (already covered in existing `test_ecl_engine.py`)

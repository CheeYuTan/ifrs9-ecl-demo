# Sprint 5 Handoff: Model Registry & Validation Framework

## What Was Built
Enhanced the existing model registry with validation framework capabilities per BCBS Principle 5.

### New Functions Added to `domain/model_registry.py`
- `generate_model_card(model_id)` — Auto-generates model card with methodology, assumptions, limitations, governance info
- `_extract_assumptions(model)` — Derives assumptions from model type and algorithm
- `_extract_limitations(model)` — Flags limitations (low R², regime sensitivity)
- `compute_sensitivity(model_id, perturbation_pct)` — Parameter perturbation analysis showing estimated ECL impact
- `check_recalibration_due(model_id, max_age_days)` — Alerts when model exceeds recalibration policy period

### Files Modified
- `app/domain/model_registry.py` — Enhanced (323 → 480 lines)
- `app/backend.py` — Updated re-exports
- `tests/unit/test_model_registry.py` — NEW (22 tests)

## Test Results
- **22 new model registry tests pass**

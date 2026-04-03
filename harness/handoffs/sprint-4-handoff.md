# Sprint 4 Handoff: Attribution Waterfall from Actual Data

## What Was Built

Rewrote the ECL attribution engine to eliminate all hardcoded percentage fallbacks per IFRS 7.35I.

### Critical Fixes
- **Removed**: `orig_ecl = {1: closing[1] * 0.18, 2: closing[2] * 0.02}` — hardcoded origination percentages
- **Removed**: `derec_ecl = {1: -(opening[1] * 0.12), ...}` — hardcoded derecognition percentages
- **Removed**: `transfers = {1: -t_1_2 + t_2_1, ...}` with `t_1_2 = opening[1] * 0.04` — hardcoded transfer rates
- **Removed**: `wo = {1: 0.0, 2: 0.0, 3: -(opening[3] * 0.08)}` — hardcoded write-off percentage
- **Removed**: `macro_shift_factor = abs(1.0 - base_weight * 2)` — synthetic macro formula

### Replacement Approach
- Each component now queries actual loan-level data
- When data is unavailable, returns `{"status": "data_unavailable", "reason": "..."}` instead of synthetic values
- Write-offs now sourced from `historical_defaults` table (actual write-off events)
- Added reconciliation check: |sum_of_components − (closing − opening)| must be < 1% of total movement
- `data_gaps` list tracks which components had insufficient data

### Files Modified
- `app/domain/attribution.py` — Rewritten (446 → 480 lines)
- `app/backend.py` — Updated re-exports
- `tests/unit/test_attribution.py` — NEW (17 tests)

## Test Results
- **17 new attribution tests pass**
- All existing tests continue to pass

# SME Implementation Review: Sprint 3 — Domain Accuracy Rules

## Domain Correctness: PASS

### Rules Added (DA-1 through DA-6)
1. **DA-1 (EAD non-negative)**: Correct per IFRS 9.B5.5.31. EAD is gross carrying amount + undrawn — cannot be negative.
2. **DA-2 (LGD unit interval)**: Correct per IFRS 9.B5.5.28. LGD ∈ [0, 1] — inclusive bounds allow full recovery (0) and total loss (1).
3. **DA-3 (Stage 3 PD consistency)**: Correct per IFRS 9.B5.5.37. Stage 3 is credit-impaired; PD should approach 1.0. Threshold of 0.90 is reasonable to allow partial cure expectations.
4. **DA-4 (Discount rate validity)**: Correct per IFRS 9.B5.5.44. EIR > -1 is a mathematical requirement for the discount factor formula.
5. **DA-5 (ECL non-negative)**: Correct. ECL represents expected cash shortfalls — by definition non-negative.
6. **DA-6 (Minimum scenario count)**: Correct per IFRS 9.B5.5.42. Standard requires "at least" base, upside, downside. Minimum of 3 is appropriate.

### Integration
- DA-2, DA-4, DA-6 are included in `run_all_pre_calculation_checks()` by default
- DA-1 and DA-3 are included when `ead_values` or `stage_pd_pairs` are provided
- Backward compatible: new optional parameters don't break existing callers

### Test Coverage
40 new tests covering:
- Valid inputs, boundary conditions, violations
- Empty lists, multiple violations
- IFRS reference verification
- Integration with aggregate checks

## Confidence Level: HIGH
All rules cite specific IFRS 9 sections. Implementation matches published standard.

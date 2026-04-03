# IFRS 9 ECL Platform — SME Domain Brief (Run 7)

**Date:** 2026-03-30
**Focus:** Code quality + domain accuracy hardening for full 8-agent exercise

## Domain Review Findings

### Validation Rules Enhancement Opportunities
1. **EAD boundary validation**: EAD values should be non-negative (IFRS 9.B5.5.31)
2. **LGD range enforcement**: LGD values must be [0, 1] (IFRS 9.B5.5.28)
3. **Discount factor validation**: If EIR is provided, must be > -1 (mathematical constraint)
4. **Stage consistency**: Stage 3 loans should have PD at or near 1.0 (IFRS 9.B5.5.37)

### Terminology Consistency
- Verify all API responses and frontend labels use correct IFRS 9 terms
- "provision" should be "Expected Credit Loss" or "ECL" consistently
- "risk category" should be "Impairment Stage"

### Code Structure for Domain Logic
- Domain logic files should be <200 lines for maintainability
- Separation of concerns: calculation logic vs data access vs validation

## Confidence Level: HIGH
Based on published IFRS 9 standard (sections cited above).

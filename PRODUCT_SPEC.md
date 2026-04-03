# IFRS 9 ECL Platform — Production Spec v2.0

## Vision
Build a plug-and-play IFRS 9 Expected Credit Loss platform that exceeds SAS Solution for IFRS 9 in capability, usability, and modern architecture — running on Databricks Lakebase with React/FastAPI.

## Current State (v1.0): ~65-70% production ready
Strong: Monte Carlo engine, satellite models, interactive drill-downs, admin config, Databricks integration
Weak: No attribution, no model registry, no GL posting, hardcoded backtesting, no Markov chains, no hazard models, no RBAC, no regulatory reports

## Sprint Plan

### Sprint 1: ECL Attribution Analysis (Waterfall Decomposition)
- IFRS 7.35I compliant loss allowance reconciliation
- Decompose ECL movement into: new originations, derecognitions, stage transfers (1→2, 2→3, 3→2, 2→1), model parameter changes, macro scenario changes, management overlays, unwind of discount, FX
- Waterfall chart visualization
- Period-over-period storage and retrieval
- Backend: new tables, computation engine, API endpoints
- Frontend: new Attribution page/section in SignOff

### Sprint 2: Model Registry & Versioning
- Formal model registry with version control
- Model lifecycle: Draft → Validated → Production → Retired
- Challenger vs incumbent comparison
- Model documentation auto-generation
- Approval workflow for model promotion
- Backend: model_registry table, versioned model artifacts
- Frontend: Model Registry page in Admin

### Sprint 3: GL Journal Entry Generation
- Generate IFRS 9 compliant journal entries
- Debit/credit posting rules for ECL provisions
- Stage transfer entries
- Overlay adjustment entries
- Export to CSV/JSON for GL system import
- Reconciliation with generated entries

### Sprint 4: Real Backtesting Engine
- Replace hardcoded Gini/KS/AUC with computed metrics
- PD backtesting: predicted vs actual default rates by cohort
- LGD backtesting: predicted vs realized loss given default
- Traffic light system (Basel green/yellow/red)
- Binomial test, Hosmer-Lemeshow, Jeffreys test
- Time series of model performance

### Sprint 5: Markov Chain State Transition Models
- Estimate transition matrices from historical data
- Forward projection of stage distribution
- Absorbing state (default) probability computation
- Multi-period cumulative PD from transition matrices
- Comparison with current PD-based approach

### Sprint 6: Hazard Models
- Cox Proportional Hazard model implementation
- Discrete-time hazard model
- Survival curves by risk segment
- Macro-variable linkage for forward-looking adjustment
- Integration with ECL engine as alternative PD source

### Sprint 7: RBAC & Authentication
- Role-based access: Analyst, Manager, Validator, Approver, Admin
- Maker-checker-approver enforcement
- Session management with Databricks OAuth
- Audit trail with authenticated user identity
- Permission-gated UI elements

### Sprint 8: Regulatory Report Generation
- IFRS 7 disclosure pack (PDF)
- Loss allowance reconciliation table
- Credit risk exposure by grade and stage
- Stage migration matrix
- Sensitivity analysis summary
- Excel export with formatted worksheets

### Sprint 9: Advanced Credit Risk Models
- Cure rate modeling (Stage 2/3 → Stage 1 transitions)
- Credit Conversion Factors for revolving facilities
- Collateral haircut models with depreciation curves
- EAD modeling for off-balance sheet exposures

### Sprint 10: Comprehensive Testing & QA
- Unit tests for all new engines
- Integration tests for API endpoints
- End-to-end workflow tests
- Data validation tests
- Performance benchmarks

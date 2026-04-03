# IFRS 9 ECL Platform — SME Domain Brief

**Prepared by:** SME Agent (IFRS 9 / Credit Risk Domain Expert)
**Date:** 2026-03-29
**Application:** Expected Credit Loss Platform (React + FastAPI + Lakebase)
**Current Maturity:** ~65-70% production ready

---

## 1. IFRS 9 Regulatory Requirements

### 1.1 Impairment Model (IFRS 9.5.5.1–5.5.20)

IFRS 9 replaces the "incurred loss" model of IAS 39 with a forward-looking "expected credit loss" model. The key requirements are:

| IFRS 9 Section | Requirement | Summary |
|---|---|---|
| **5.5.1** | Recognition of ECL | An entity shall recognise a loss allowance for expected credit losses on financial assets measured at amortised cost |
| **5.5.3** | 12-month vs lifetime | Stage 1 assets recognise 12-month ECL; Stage 2/3 assets recognise lifetime ECL |
| **5.5.5** | Significant increase in credit risk (SICR) | At each reporting date, assess whether credit risk has increased significantly since initial recognition |
| **5.5.9** | SICR assessment criteria | Use reasonable and supportable information (past due status, PD changes, macroeconomic outlook) |
| **5.5.11** | 30-day DPD rebuttable presumption | There is a rebuttable presumption that credit risk has increased significantly when contractual payments are more than 30 days past due |
| **5.5.12** | Low credit risk simplification | An entity may assume credit risk has not increased significantly if the instrument has low credit risk at the reporting date |
| **5.5.15** | Measurement of ECL | ECL shall reflect an unbiased and probability-weighted amount, time value of money, and reasonable/supportable information about past events, current conditions, and forecasts |
| **5.5.17** | Multiple scenarios | ECL measurement shall consider a range of possible outcomes — not just the single most likely outcome |
| **5.5.18** | Maximum contractual period | The maximum period over which ECL is measured is the maximum contractual period (including extension options) |
| **5.5.19** | Modified financial assets | When contractual cash flows are modified, assess whether the modification results in derecognition |
| **5.5.20** | Purchased/originated credit-impaired (POCI) | Special treatment for assets that are credit-impaired at initial recognition |

### 1.2 Disclosure Requirements (IFRS 7.35F–35N)

| IFRS 7 Section | Requirement |
|---|---|
| **35F** | Credit risk management practices and how they relate to ECL recognition/measurement |
| **35G** | Quantitative and qualitative information about amounts arising from ECL |
| **35H** | Reconciliation of opening to closing balance of loss allowance, by stage |
| **35I** | Explanation of changes in loss allowance: transfers between stages, new originations, derecognitions, write-offs, modifications, changes in models/assumptions |
| **35J** | Reconciliation of gross carrying amount by stage |
| **35K** | Modified financial assets |
| **35L** | Collateral and credit enhancements |
| **35M** | Credit risk exposure by credit risk grade and stage |
| **35N** | Concentrations of credit risk |

### 1.3 Basel Committee Guidance

The Basel Committee on Banking Supervision (BCBS) published **BCBS d350 "Guidance on credit risk and accounting for expected credit losses"** (December 2015) with 11 principles:

| Principle | Summary |
|---|---|
| **1** | Board and senior management responsibility for credit risk practices |
| **2** | Sound ECL methodologies with documented policies |
| **3** | Credit risk rating/grouping processes |
| **4** | Adequacy of the overall ECL allowance |
| **5** | ECL model validation — independent review and challenge |
| **6** | Experienced credit judgment in ECL estimation |
| **7** | Common data and systems for credit risk assessment and ECL measurement |
| **8** | Disclosure of ECL information |
| **9** | Supervisory evaluation of credit risk practices |
| **10** | Supervisory evaluation of ECL adequacy |
| **11** | Supervisory cooperation |

Additionally, **BCBS d457 "Instructions for Basel III monitoring"** and the **EBA Guidelines on PD estimation, LGD estimation, and treatment of defaulted exposures (EBA/GL/2017/16)** provide detailed requirements for:
- PD backtesting (discriminatory power, calibration accuracy)
- LGD estimation (downturn LGD, workout LGD, realised LGD)
- Margin of conservatism when data is insufficient

---

## 2. Gap Analysis: Current Implementation vs Regulatory Requirements

### 2.1 What the Application Does Well

| Area | IFRS 9 Alignment | Implementation Quality |
|---|---|---|
| **ECL formula** | Correct: Σ[Survival × PD × LGD × EAD × DF] per quarter | Production-grade vectorized NumPy |
| **Three-stage model** | Correct: 12-month (Stage 1), lifetime (Stage 2/3) | Properly implemented with stage-dependent horizons |
| **Forward-looking scenarios** | IFRS 9.5.5.17 compliant: 8 probability-weighted scenarios | Good scenario diversity (baseline through tail risk) |
| **SICR assessment** | IFRS 9.5.5.9 compliant: PD-ratio, DPD backstop, forbearance triggers | Well-implemented with product-specific thresholds |
| **30-day DPD presumption** | IFRS 9.5.5.11 compliant | Correctly applied as Stage 2 trigger |
| **Satellite models** | Logistic regression linking macro variables to PD/LGD | Calibrated from actual data with R² tracking |
| **Monte Carlo simulation** | Correlated PD-LGD draws via Cholesky decomposition | Statistically sound with convergence checking |
| **Discounting** | Quarterly discounting at EIR | Correct per IFRS 9.5.5.15 |
| **Data quality checks** | Completeness, validity, consistency, IFRS 9-specific checks | 15+ DQ checks with severity classification |
| **GL reconciliation** | Loan tape vs GL balance comparison | Implemented with tolerance thresholds |

### 2.2 Critical Gaps

| # | Gap | IFRS 9 Reference | Current State | Risk |
|---|---|---|---|---|
| **G1** | LGD backtesting uses hardcoded/synthetic metrics for non-PD models | BCBS Principle 5, EBA/GL/2017/16 §150-160 | Lines 2116-2130 in `backend.py`: LGD backtest falls back to `{"AUC": 0.72, "Gini": 0.44, ...}` when no defaulted loans exist, and even when they do, computes `AUC = 0.65 + implied_lgd * 0.2` — a fabricated formula with no statistical basis | **AUDIT FAILURE** — auditors will immediately flag synthetic metrics as non-compliant |
| **G2** | No model validation framework | BCBS Principle 5 | No independent model validation, no challenger model comparison, no model documentation auto-generation | **AUDIT FAILURE** — banks must demonstrate independent model validation |
| **G3** | No RBAC enforcement on API endpoints | BCBS Principle 1, IFRS 7.35F | RBAC tables and permission checks exist (`check_permission()`) but no API endpoint actually enforces them — any user can run simulations, approve overlays, or sign off | **AUDIT FAILURE** — no segregation of duties |
| **G4** | Attribution waterfall uses estimated/synthetic components when data unavailable | IFRS 7.35I | `compute_attribution()` (lines 1256-1278, 1321-1334) falls back to hardcoded percentages (e.g., `orig_ecl = closing * 0.18`) when queries fail | **MAJOR** — reconciliation must be based on actual data |
| **G5** | No Purchased/Originated Credit-Impaired (POCI) handling | IFRS 9.5.5.13-14, 5.5.20 | No POCI flag, no separate ECL treatment for assets credit-impaired at origination | **MAJOR** — POCI assets require lifetime ECL from day one with no SICR assessment |
| **G6** | Markov transition matrices use hardcoded default rate | IFRS 9.B5.5.52 | Line 2693: `default_rate = 0.15` hardcoded for Stage 3 → Default transitions | **MAJOR** — transition probabilities must be estimated from observed data |
| **G7** | No model registry / version control | BCBS Principle 2 | No formal model lifecycle (Draft → Validated → Production → Retired) | **MAJOR** — model governance requires version tracking |
| **G8** | Scenario weights not formally justified | IFRS 9.5.5.17, IFRS 9.B5.5.42 | Weights are configurable but no documentation of how they were derived or what economic rationale supports them | **MAJOR** — scenario probability weights must be supportable |
| **G9** | No write-off policy enforcement | IFRS 9.5.4.4 | Write-offs are flagged but no automated enforcement of write-off criteria (e.g., >180 DPD, no reasonable expectation of recovery) | **MODERATE** |
| **G10** | No modification/restructuring gain/loss calculation | IFRS 9.5.5.12, 5.4.3 | Restructured loans trigger SICR but no modification gain/loss is computed | **MODERATE** |

### 2.3 Architectural Gaps

| # | Gap | Impact |
|---|---|---|
| **A1** | Monolithic `backend.py` (4,807 lines) | Impossible to unit-test individual domain modules; merge conflicts; cognitive overload |
| **A2** | No audit trail with authenticated user identity | Audit log records actions but user identity is self-reported (passed as string parameter), not derived from authentication |
| **A3** | No immutability enforcement on locked ECL runs | Sign-off sets a flag but nothing prevents API calls from modifying a signed-off project |
| **A4** | ECL engine (`ecl_engine.py`) and batch script (`03_run_ecl_calculation.py`) are separate codepaths | Risk of divergence — the in-app simulation may produce different results than the batch pipeline |
| **A5** | No data lineage tracking | Cannot trace which input data version produced which ECL output |

---

## 3. Priority Improvements

### 3.1 CRITICAL — Would Fail an Audit

| ID | Improvement | Effort | IFRS 9 Reference |
|---|---|---|---|
| **C1** | **Replace synthetic backtesting metrics with computed-from-data metrics** — The LGD backtest must compute actual predicted-vs-realised LGD by recovery cohort. The PD backtest already computes real AUC/Gini/KS but the LGD path (lines 2116-2130) fabricates numbers. Implement: (a) workout LGD computation from `historical_defaults`, (b) predicted LGD vs realised LGD by product cohort, (c) Hosmer-Lemeshow calibration test, (d) Jeffreys test for PD calibration, (e) binomial test per rating grade | Medium | BCBS Principle 5, EBA/GL/2017/16 §150-160 |
| **C2** | **Enforce RBAC on all state-changing API endpoints** — Add middleware/dependency that extracts authenticated user from Databricks OAuth token and checks permissions before allowing: simulation execution, overlay submission, sign-off, project creation, admin config changes. The `check_permission()` function exists but is never called from API routes | Medium | BCBS Principle 1 |
| **C3** | **Implement immutability for signed-off ECL runs** — After sign-off, all mutation endpoints for that project must return 403. Store a cryptographic hash of the ECL results at sign-off time. Provide a verification endpoint that re-hashes and compares | Low | IFRS 7.35F, BCBS Principle 2 |
| **C4** | **Add model validation framework** — Independent validation must include: (a) out-of-sample testing, (b) sensitivity analysis of model parameters, (c) comparison with benchmark/challenger models, (d) documentation of model limitations and assumptions, (e) annual recalibration schedule tracking | High | BCBS Principle 5 |

### 3.2 MAJOR — Weakens Model Credibility

| ID | Improvement | Effort | IFRS 9 Reference |
|---|---|---|---|
| **M1** | **Compute attribution waterfall from actual data, eliminate fallback percentages** — Every component (new originations, derecognitions, stage transfers, model changes, macro changes) must be derived from comparing current-period and prior-period loan-level data. The residual should be < 5% of total ECL movement | High | IFRS 7.35I |
| **M2** | **Implement POCI asset handling** — Add `is_poci` flag to loan tape, skip SICR assessment for POCI assets, always compute lifetime ECL, track cumulative changes in lifetime ECL since initial recognition (not absolute ECL) | Medium | IFRS 9.5.5.13-14 |
| **M3** | **Estimate Markov transition matrices from observed data** — Replace hardcoded `default_rate = 0.15` with actual observed Stage 3 → Default transitions. Require minimum observation periods (≥3 years). Implement generator matrix approach for continuous-time transitions | Medium | IFRS 9.B5.5.52 |
| **M4** | **Add model registry with version control** — Track model lifecycle: Draft → Validated → Production → Retired. Store model artifacts, validation reports, approval records. Prevent production use of unvalidated models | High | BCBS Principle 2 |
| **M5** | **Implement formal scenario weight justification** — Require documentation of economic rationale for each scenario weight. Implement constraints: (a) weights sum to 1.0, (b) no single scenario > 50%, (c) adverse scenarios collectively ≥ 20%, (d) log the basis for weight changes between periods | Low | IFRS 9.5.5.17, B5.5.42 |
| **M6** | **Unify batch and in-app ECL calculation codepaths** — The batch script (`03_run_ecl_calculation.py`) and in-app engine (`ecl_engine.py`) implement the same methodology independently. Extract a shared ECL calculation module to ensure identical results regardless of execution path | Medium | BCBS Principle 7 |
| **M7** | **Add PD calibration tests** — Implement binomial test (per rating grade: is observed default rate within confidence interval of predicted PD?), Hosmer-Lemeshow test (across deciles), and Spiegelhalter test. These are standard regulatory expectations beyond discrimination metrics (AUC/Gini/KS) | Medium | EBA/GL/2017/16 §71-80 |
| **M8** | **Implement Population Stability Index (PSI) monitoring** — Track PD distribution stability over time. Alert when PSI > 0.25 (significant shift). The `_compute_psi` function exists but is only used in backtesting, not as ongoing monitoring | Low | EBA/GL/2017/16 §90 |

### 3.3 MINOR — Nice-to-Haves for Completeness

| ID | Improvement | Effort | IFRS 9 Reference |
|---|---|---|---|
| **N1** | **Implement low credit risk simplification** — Allow Stage 1 classification for investment-grade assets regardless of PD change (IFRS 9.5.5.10) | Low | IFRS 9.5.5.10 |
| **N2** | **Add modification gain/loss calculation** — When a loan is restructured, compute the difference between pre-modification and post-modification present value of cash flows | Medium | IFRS 9.5.4.3 |
| **N3** | **Implement Credit Conversion Factors (CCF) for off-balance sheet exposures** — Revolving facilities (credit cards, lines of credit) need CCF to convert undrawn commitments to EAD | Medium | IFRS 9.B5.5.31 |
| **N4** | **Add cure rate modeling** — Track Stage 2/3 → Stage 1 transitions to validate that SICR reversal criteria are appropriate. The `cure_rate_analysis` table exists but is not populated from real data | Medium | IFRS 9.5.5.7 |
| **N5** | **Generate IFRS 7 disclosure pack (PDF/Excel)** — Automated generation of all required IFRS 7.35F-35N disclosures in a format suitable for inclusion in financial statements | High | IFRS 7.35F-35N |
| **N6** | **Add effective interest rate validation** — Verify that the EIR used for discounting is the original EIR (not a revised rate), as required by IFRS 9.5.4.1 | Low | IFRS 9.5.4.1 |
| **N7** | **Implement collateral haircut models** — For secured lending, LGD should reflect collateral value with appropriate haircuts for forced-sale discount, time-to-recovery, and depreciation | Medium | IFRS 7.35L |

---

## 4. Domain-Specific Validation Rules

These rules should be enforced programmatically at data ingestion, model execution, and sign-off stages.

### 4.1 Data Integrity Rules

| Rule ID | Rule | Enforcement Point | Severity |
|---|---|---|---|
| **D1** | `Σ scenario_weights = 1.0 ± 0.001` | Before ECL calculation | CRITICAL — reject if violated |
| **D2** | `0 < PD ≤ 1.0` for all loans | Data processing | CRITICAL |
| **D3** | `0 < LGD ≤ 1.0` for all products | Model configuration | CRITICAL |
| **D4** | `EIR > 0` for all loans (cannot discount at zero rate) | Data processing | CRITICAL |
| **D5** | `remaining_months ≥ 0` | Data processing | CRITICAL |
| **D6** | `gross_carrying_amount > 0` for non-written-off loans | Data processing | CRITICAL |
| **D7** | Stage 3 loans must have `DPD ≥ 90` OR another credit-impairment trigger | SICR assessment | HIGH |
| **D8** | Stage 1 loans must have `DPD < 30` (unless 30-day presumption is rebutted with documented evidence) | SICR assessment | HIGH |
| **D9** | `origination_date < reporting_date` | Data processing | CRITICAL |
| **D10** | `maturity_date > origination_date` | Data processing | HIGH |

### 4.2 Model Reasonableness Rules

| Rule ID | Rule | Enforcement Point | Severity |
|---|---|---|---|
| **M-R1** | ECL coverage ratio by stage must be monotonically increasing: `coverage(S1) < coverage(S2) < coverage(S3)` | Post-calculation validation | HIGH — if violated, staging or ECL calculation is suspect |
| **M-R2** | Weighted average ECL should be within 50-200% of prior period (flag large movements for review) | Post-calculation | MEDIUM |
| **M-R3** | Satellite model R² should be ≥ 0.30 for PD models and ≥ 0.20 for LGD models | Model calibration | HIGH — low R² means macro variables have weak explanatory power |
| **M-R4** | Monte Carlo convergence: coefficient of variation at 100% sims should be < 5% | Post-simulation | HIGH |
| **M-R5** | No single scenario should contribute > 40% of probability-weighted ECL | Post-calculation | MEDIUM |
| **M-R6** | Adverse scenario ECL should be > baseline ECL (otherwise scenario design is suspect) | Post-calculation | HIGH |
| **M-R7** | PD aging factor for Stage 2/3 should produce increasing marginal PD over time | Model configuration | HIGH |
| **M-R8** | Total management overlays should not exceed 15% of base ECL (configurable cap) | Overlay submission | MEDIUM |

### 4.3 Governance Rules

| Rule ID | Rule | Enforcement Point | Severity |
|---|---|---|---|
| **G-R1** | ECL run must not be signed off by the same user who executed the simulation | Sign-off | CRITICAL — segregation of duties |
| **G-R2** | Management overlays must have: reason, IFRS 9 reference, approver, expiry date | Overlay submission | HIGH |
| **G-R3** | Model parameter changes between periods must be documented with rationale | Admin config changes | HIGH |
| **G-R4** | Backtesting must be run before sign-off (at least PD backtest within last 90 days) | Sign-off gate | HIGH |
| **G-R5** | Data quality score must be ≥ 90% before model execution is permitted | Data control gate | HIGH |

---

## 5. Terminology Audit

### 5.1 Incorrect or Imprecise Terminology

| Current Term | Issue | Correct Term | Location |
|---|---|---|---|
| `aging_factor` | Ambiguous — could refer to vintage aging or PD term structure | `pd_hazard_escalation_factor` or `pd_term_structure_slope` | `ecl_engine.py` line 172, throughout |
| `current_lifetime_pd` used as annual PD input to Monte Carlo | The field name suggests a cumulative lifetime PD, but it is used as an annualised point-in-time PD in the ECL formula (`1 - (1-PD)^0.25` for quarterly conversion) | Either rename to `current_annual_pd` or `current_pit_pd`, or add clear documentation that this is an annualised PD despite the "lifetime" name | `ecl_engine.py` line 260, `03_run_ecl_calculation.py` line 382 |
| `coverage_ratio` | Used inconsistently — sometimes ECL/GCA as percentage, sometimes as decimal | Standardise as `ecl_coverage_pct` (always percentage) or `ecl_coverage_ratio` (always decimal) | Multiple locations in `backend.py` |
| `assessed_stage` vs `current_stage` | Two different column names for IFRS 9 stage — `current_stage` is the bank's input, `assessed_stage` is the pipeline's output | Document clearly: `current_stage` = bank's prior assessment, `assessed_stage` = pipeline-reassessed stage. Consider renaming to `input_stage` and `ifrs9_stage` | `02_run_data_processing.py`, `admin_config.py` |
| `satellite model` | While commonly used in practice, the IFRS 9 standard does not use this term | Add glossary note: "Satellite model" is industry terminology for a regression model that links macroeconomic variables to credit risk parameters. IFRS 9 refers to this as "incorporating forward-looking information" (IFRS 9.5.5.17) | README, throughout |
| `ecl_amount` | In `loan_level_ecl` table, this is the unweighted scenario ECL, not the final probability-weighted ECL | Rename to `scenario_ecl` or `unweighted_scenario_ecl` to distinguish from `weighted_ecl` | `03_run_ecl_calculation.py` line 457 |
| `Gini coefficient` in backtesting | While Gini = 2×AUC - 1 is standard, the term "Gini coefficient" can be confused with the income inequality measure | Use `Gini coefficient (Accuracy Ratio)` or simply `Accuracy Ratio (AR)` which is the more precise credit risk term | `backend.py` line 1983 |

### 5.2 Missing Terminology

The application should explicitly use and define these IFRS 9 terms in the UI and documentation:

- **Through-the-Cycle (TTC) PD** vs **Point-in-Time (PIT) PD** — The application uses PIT PD (macro-adjusted) but does not clearly label it
- **Downturn LGD** — The LGD stress via scenario multipliers is effectively a downturn adjustment, but it is not labelled as such
- **Effective Interest Rate (EIR)** — Correctly used for discounting but should note it is the rate at initial recognition, not a current market rate
- **Gross Carrying Amount (GCA)** vs **Amortised Cost** — GCA is used throughout; clarify that GCA = amortised cost before deducting loss allowance
- **Loss Allowance** — The IFRS 9 term for the ECL provision; the app uses "ECL" throughout but "loss allowance" is the balance sheet term

---

## 6. Backtesting Requirements

### 6.1 PD Backtesting (Currently Partially Implemented)

The current implementation computes AUC, Gini, KS, PSI, and Brier score from actual portfolio data for PD models. This is a good foundation but incomplete.

**What is missing for regulatory compliance:**

| Test | Description | Basel/EBA Reference | Status |
|---|---|---|---|
| **Binomial test** | Per rating grade: is the observed default count within the confidence interval of the predicted PD × number of obligors? Uses one-sided binomial test at 95% and 99% confidence levels | EBA/GL/2017/16 §71 | **NOT IMPLEMENTED** |
| **Hosmer-Lemeshow test** | Goodness-of-fit test across PD deciles — tests whether observed default rates match predicted rates across the full PD spectrum | EBA/GL/2017/16 §74 | **NOT IMPLEMENTED** (mentioned in PRODUCT_SPEC but not coded) |
| **Jeffreys test** | Bayesian alternative to binomial test, more appropriate for low-default portfolios | EBA/GL/2017/16 §72 | **NOT IMPLEMENTED** |
| **Spiegelhalter test** | Tests overall calibration of predicted probabilities | Basel IRB guidance | **NOT IMPLEMENTED** |
| **Traffic light approach** | Basel green/amber/red classification based on number of defaults vs predicted | BCBS 2005 "Studies on the Validation of Internal Rating Systems" | **PARTIALLY** — traffic light exists but only for discrimination metrics, not calibration |
| **Cohort-level PD comparison** | Predicted vs actual default rate by vintage cohort, product, stage | EBA/GL/2017/16 §76 | **PARTIALLY** — cohort results exist but use `current_lifetime_pd` mean vs `defaulted` mean, which conflates PD level with default rate |
| **Time series stability** | Track metric trends over multiple periods to detect model degradation | EBA/GL/2017/16 §90 | **PARTIALLY** — `get_backtest_trend` exists |

**Implementation note:** The current PD backtest (lines 2086-2115) correctly computes discrimination metrics from actual data. The main gap is calibration testing (binomial/Hosmer-Lemeshow) and the fact that `current_lifetime_pd` is a lifetime measure being compared against a point-in-time default indicator — this is methodologically questionable. The backtest should compare 12-month PD against 12-month observed default rates.

### 6.2 LGD Backtesting (Currently Not Implemented)

The LGD backtest path (lines 2116-2130) is the most critical gap. It fabricates metrics rather than computing them from data.

**Required LGD backtesting components:**

| Component | Description | Reference |
|---|---|---|
| **Predicted vs realised LGD by product** | Compare model LGD assumptions against actual recovery outcomes from `historical_defaults` table | EBA/GL/2017/16 §150 |
| **Workout LGD** | Compute realised LGD from actual recovery cash flows, discounted at original EIR | EBA/GL/2017/16 §153 |
| **Downturn LGD validation** | Verify that stressed LGD (under adverse scenarios) is consistent with observed LGD during economic downturns | EBA/GL/2017/16 §160 |
| **LGD by collateral type** | For secured products, validate LGD against collateral recovery rates | EBA/GL/2017/16 §155 |
| **Cure rate validation** | Compare assumed cure rates against observed Stage 2/3 → Stage 1 transition rates | EBA/GL/2017/16 §158 |

### 6.3 EAD Backtesting

| Component | Description | Status |
|---|---|---|
| **Predicted vs actual EAD** | Compare amortisation assumptions against actual balance rundown | **NOT IMPLEMENTED** |
| **CCF validation** | For revolving facilities, compare assumed credit conversion factors against observed drawdown at default | **NOT IMPLEMENTED** |
| **Prepayment rate validation** | Compare assumed prepayment rates against actual prepayment behaviour | **NOT IMPLEMENTED** — prepayment rates are hardcoded per product |

---

## 7. Attribution / Waterfall Requirements

### 7.1 IFRS 7.35I Compliance

IFRS 7.35I requires a reconciliation from opening to closing loss allowance showing the following components **by stage**:

| Component | IFRS 7.35I Ref | Current Implementation | Gap |
|---|---|---|---|
| **Opening balance** | 35I(a) | ✅ Implemented — uses prior period closing or estimated opening | Falls back to synthetic estimate when no prior period exists (acceptable for first period only) |
| **Increases due to origination/purchase** | 35I(b)(i) | ⚠️ Partially — queries loans originated in last 90 days | Should use exact reporting period boundaries, not rolling 90-day window |
| **Decreases due to derecognition** | 35I(b)(ii) | ⚠️ Partially — queries matured/expired loans | Should track actual derecognition events, not just maturity |
| **Changes due to stage transfers** | 35I(b)(iii) | ⚠️ Partially — computed from migration matrix and average ECL per stage | Should compute exact ECL impact of each transferred loan (ECL at new stage minus ECL at old stage) |
| **Changes in model/risk parameters** | 35I(b)(iv) | ⚠️ Computed as residual after other components | Should be directly measured by re-running prior-period loans with new parameters |
| **Changes in macro/scenario assumptions** | 35I(b)(iv) | ⚠️ Uses a synthetic `macro_shift_factor` formula | Should be measured by re-running current loans under prior-period scenario weights |
| **Write-offs** | 35I(b)(v) | ⚠️ Partially — estimates from high-DPD Stage 3 loans × 15% | Should track actual write-off events |
| **Management overlays** | Not explicitly in 35I but expected by auditors | ✅ Implemented — reads from project overlays | Good |
| **Unwind of discount** | 35I(b)(vi) | ✅ Implemented — opening ECL × quarterly EIR | Correct methodology |
| **Foreign exchange** | 35I(b)(vii) | ✅ Placeholder (zero for single-currency) | Acceptable |
| **Closing balance** | 35I(a) | ✅ Implemented | Good |

### 7.2 Required Improvements

1. **Eliminate all fallback percentages** — Every waterfall component must be computed from actual loan-level data. If data is unavailable, the component should be reported as "Not available — insufficient data" rather than estimated with hardcoded ratios.

2. **Implement loan-level attribution** — For each loan that existed in both periods:
   - Compute ECL under prior-period parameters with current data → isolates data/risk changes
   - Compute ECL under current parameters with prior-period data → isolates parameter changes
   - The difference between these gives a clean decomposition

3. **Track derecognition events explicitly** — Add a `derecognition_date` and `derecognition_reason` (maturity, prepayment, write-off, sale) to the loan tape.

4. **Reconciliation check** — The sum of all waterfall components must equal (closing ECL − opening ECL) within a materiality threshold (suggest < 1% of total ECL movement). Currently, the residual absorbs all errors.

---

## 8. Modularization Recommendations

### 8.1 Current State

| File | Lines | Responsibility |
|---|---|---|
| `backend.py` | 4,807 | Everything: DB connection, queries, workflow, attribution, backtesting, Markov, hazard, GL journals, reports, RBAC, advanced features |
| `app.py` | 1,642 | All API routes (~100 endpoints) |
| `ecl_engine.py` | 609 | In-app Monte Carlo simulation |
| `admin_config.py` | 886 | Configuration CRUD |

### 8.2 Recommended Module Structure

Split along **domain boundaries** to maintain coherence within each module:

```
app/
├── main.py                          # FastAPI app creation, lifespan, middleware
├── config.py                        # Admin configuration (current admin_config.py)
├── db/
│   ├── __init__.py
│   ├── pool.py                      # Connection pool, token refresh (lines 1-180 of backend.py)
│   └── queries.py                   # Base query_df, execute helpers
├── domain/
│   ├── __init__.py
│   ├── staging.py                   # SICR assessment, stage assignment logic
│   ├── ecl_calculation.py           # Monte Carlo engine (current ecl_engine.py)
│   ├── satellite_models.py          # Satellite model calibration, prediction
│   ├── attribution.py               # ECL waterfall decomposition (lines 1172-1578)
│   ├── backtesting.py               # PD/LGD/EAD backtesting (lines 1925-2260)
│   ├── markov.py                    # Transition matrices, forecasting (lines 2596-2880)
│   ├── hazard.py                    # Hazard models, survival curves (lines 2882-3470)
│   └── scenarios.py                 # Scenario management, weight validation
├── governance/
│   ├── __init__.py
│   ├── rbac.py                      # Users, roles, permissions (lines 4100-4377)
│   ├── approvals.py                 # Approval workflow
│   ├── audit.py                     # Audit trail, immutability enforcement
│   └── model_registry.py            # Model versioning, lifecycle (future)
├── reporting/
│   ├── __init__.py
│   ├── ifrs7_disclosures.py         # IFRS 7 disclosure queries (lines 614-800)
│   ├── gl_journals.py               # GL journal generation (lines 2263-2595)
│   ├── regulatory_reports.py        # Report generation (lines 3700-4100)
│   └── exports.py                   # PDF/Excel export
├── workflow/
│   ├── __init__.py
│   ├── projects.py                  # Project CRUD, workflow state machine
│   ├── overlays.py                  # Management overlay logic
│   └── signoff.py                   # Sign-off, locking, attestation
├── routes/
│   ├── __init__.py
│   ├── projects.py                  # /api/projects/* routes
│   ├── data.py                      # /api/data/* routes
│   ├── simulation.py                # /api/simulation/* routes
│   ├── stress_testing.py            # /api/stress/* routes
│   ├── backtesting.py               # /api/backtesting/* routes
│   ├── attribution.py               # /api/attribution/* routes
│   ├── governance.py                # /api/rbac/*, /api/approvals/* routes
│   ├── reporting.py                 # /api/reports/*, /api/gl/* routes
│   └── admin.py                     # /api/admin/* routes
└── middleware/
    ├── __init__.py
    ├── auth.py                      # Extract user from OAuth token
    └── rbac.py                      # Permission enforcement middleware
```

### 8.3 Modularization Principles

1. **Keep domain logic together** — All ECL calculation logic (Monte Carlo, term structure, convergence) stays in `domain/ecl_calculation.py`. All attribution logic stays in `domain/attribution.py`. This makes it possible for a credit risk specialist to review one file.

2. **Separate routes from business logic** — API routes in `routes/` should be thin wrappers that validate input, call domain functions, and format output. No SQL queries or business logic in route handlers.

3. **Separate database access from domain logic** — Domain modules should call query functions from `db/queries.py` rather than constructing SQL directly. This enables testing with mock data.

4. **Shared constants in one place** — Table names, schema prefixes, metric thresholds, and default parameters should be in a single `constants.py` file.

5. **Middleware for cross-cutting concerns** — Authentication and RBAC enforcement should be middleware/dependencies, not scattered through individual endpoints.

### 8.4 Migration Strategy

Modularize incrementally to avoid a big-bang refactor:

1. **Phase 1:** Extract `db/pool.py` and `db/queries.py` — zero functional change, just moving code
2. **Phase 2:** Extract `domain/backtesting.py` and `domain/attribution.py` — these are self-contained
3. **Phase 3:** Extract `governance/rbac.py` and add `middleware/auth.py` — enables RBAC enforcement
4. **Phase 4:** Extract remaining domain modules (`markov.py`, `hazard.py`, `gl_journals.py`)
5. **Phase 5:** Split `app.py` routes into `routes/` sub-modules
6. **Phase 6:** Extract `domain/ecl_calculation.py` as the unified engine (replacing both `ecl_engine.py` and the batch script logic)

---

## 9. Summary of Key Findings

### Regulatory Risk Assessment

| Category | Count | Highest Severity |
|---|---|---|
| Would fail audit | 4 items (C1-C4) | Synthetic backtesting metrics, no RBAC enforcement, no immutability, no model validation |
| Weakens credibility | 8 items (M1-M8) | Synthetic attribution components, no POCI handling, hardcoded Markov rates |
| Nice-to-have | 7 items (N1-N7) | Low credit risk simplification, modification gain/loss, CCF |

### Top 5 Actions by Impact

1. **Fix LGD backtesting** (C1) — This is the single most damaging finding. An auditor who sees `{"AUC": 0.72, "Gini": 0.44}` hardcoded will question the entire model's integrity.

2. **Enforce RBAC** (C2) — Any user being able to sign off their own ECL run is a fundamental governance failure.

3. **Compute attribution from actual data** (M1) — The waterfall is the primary disclosure artifact. Synthetic percentages undermine the entire IFRS 7.35I reconciliation.

4. **Add calibration tests to backtesting** (M7) — Discrimination metrics (AUC/Gini) show ranking power but not calibration accuracy. Banks need both.

5. **Implement model registry** (M4) — Without version control, there is no way to demonstrate that the model in production was independently validated.

### What Makes This Application Credible Today

Despite the gaps, the application has a strong technical foundation:

- The Monte Carlo engine with Cholesky-correlated PD-LGD draws is methodologically sound
- The logistic satellite model calibration from actual data (with R² tracking) is a genuine forward-looking approach
- The SICR assessment with product-specific thresholds and multiple trigger types is well-designed
- The 8-scenario framework with probability weighting is a reasonable implementation of IFRS 9.5.5.17
- The data quality framework with 15+ checks and severity classification demonstrates good data governance intent

The path from 65-70% to production-ready is primarily about **governance, validation, and auditability** — not about the core ECL methodology, which is already strong.

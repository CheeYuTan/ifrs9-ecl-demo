---
sidebar_position: 8
title: "Step 7: Overlays"
description: "Applying management adjustments to model-computed ECL with documented rationale."
---

# Step 7: Overlays

Overlays are management adjustments applied on top of the model-computed ECL. IFRS 9 recognizes that statistical models cannot capture every risk factor — emerging economic events, sector-specific concerns, or known data limitations may require the institution to adjust the model output. This step provides a governed framework for making, documenting, and approving those adjustments.

:::info Prerequisites
- Completed [Step 6: Stress Testing](step-6-stress-testing)
- Simulation results and stress testing analysis available
- **Risk Manager** or **Analyst** role required to add overlays
:::

## What You'll Do

On this page you will review the current model-computed ECL, add management overlays with documented rationale, ensure overlays stay within governance limits, and see the impact of adjustments on the final ECL figure. Each overlay requires an IFRS 9 justification reference and must be approved through the maker-checker workflow.

## Step-by-Step Instructions

### 1. Review the Model ECL Baseline

At the top of the page, the platform displays the model-computed ECL from Step 5 — this is the starting point before any management adjustments:

| Metric | What It Shows |
|--------|--------------|
| **Model ECL** | The total Expected Credit Loss produced by the Monte Carlo simulation |
| **Gross Carrying Amount** | The total portfolio exposure |
| **Coverage Ratio** | Model ECL divided by GCA |
| **Number of Products** | How many product types are included |

This baseline is the benchmark. Overlays will adjust it upward or downward, and the governance framework ensures adjustments stay within approved bounds.

### 2. Understand the Governance Framework

Before adding overlays, review the governance controls displayed on the page:

**Overlay Cap**: The total net overlay (sum of all upward and downward adjustments) cannot exceed **15% of the model ECL** without escalation to the Board Risk Committee. This cap prevents overlays from dominating the model output — the ECL should remain primarily model-driven.

**Approval Requirements**: Every overlay follows a maker-checker pattern:
- The **maker** (typically a Risk Analyst) creates the overlay with justification
- The **checker** (typically the Chief Risk Officer or delegated approver) reviews and approves or rejects it
- No individual can both create and approve the same overlay

**Classification**: Each overlay must be classified as:
- **Temporary** — expected to be removed within 2 quarters (e.g., a one-off economic event). Temporary overlays expire automatically and trigger a review reminder.
- **Permanent** — reflects an ongoing model limitation. Permanent overlays trigger a model redevelopment review, as the model should eventually capture the risk factor directly.

**Expiry Policy**: Temporary overlays have a mandatory expiry date. The platform alerts when overlays are approaching expiry so they can be reviewed, extended, or removed.

### 3. Add a New Overlay

To create an overlay, click **Add Overlay** and complete the following fields:

| Field | Description | Example |
|-------|------------|---------|
| **Product** | Which product type this overlay applies to | Personal Loans |
| **Overlay Type** | The risk parameter being adjusted | PD Uplift, LGD Uplift, EAD Adjustment, PD Reduction, LGD Reduction |
| **Amount** | The ECL adjustment in currency units | 250,000 |
| **IFRS 9 Reference** | The paragraph justifying this type of adjustment | B5.5.17(c) — sector-specific factors |
| **Reason** | A detailed explanation of why this adjustment is necessary | "Increased PD for commercial real estate loans due to rising vacancy rates in the office sector, not yet reflected in the historical PD model." |
| **Classification** | Temporary or Permanent | Temporary |
| **Expiry Date** | When this overlay should be reviewed (required for Temporary) | 2025-06-30 |
| **Approved By** | The name of the approving authority | Jane Smith (CRO) |

All fields except Expiry Date (which is only required for Temporary overlays) are mandatory. The platform validates that the product exists and that the amount is within the governance cap.

### 4. Review IFRS 9 Justification Categories

IFRS 9 paragraph B5.5.17 identifies several categories of information that may require management adjustment. The platform maps these to overlay types:

| IFRS 9 Reference | Category | When to Use |
|-------------------|----------|-------------|
| **B5.5.17(a)** | Internal data | When your institution's own data shows a trend not captured by the model |
| **B5.5.17(b)** | External data | When market or industry data indicates higher or lower risk |
| **B5.5.17(c)** | Sector-specific factors | When a particular sector faces conditions not reflected in historical averages |
| **B5.5.17(d)** | Macroeconomic conditions | When economic forecasts differ from the scenarios used in the model |
| **B5.5.17(e)** | Lending terms or standards | When changes in underwriting criteria affect future loss rates |

Selecting the correct IFRS 9 reference is important for audit. It demonstrates that the overlay is grounded in the standard's requirements, not arbitrary adjustment.

### 5. View the ECL Waterfall

After adding overlays, the **ECL Waterfall** chart visualizes the path from model ECL to adjusted ECL:

1. **Model ECL** — the starting point from Monte Carlo simulation
2. **+ Upward Overlays** — adjustments that increase ECL (e.g., PD Uplift for a stressed sector)
3. **- Downward Overlays** — adjustments that decrease ECL (e.g., LGD Reduction for improved collateral)
4. **= Adjusted ECL** — the final figure after all overlays

The waterfall makes it easy to see the net impact of overlays at a glance. A large gap between Model ECL and Adjusted ECL warrants scrutiny — if overlays are consistently large, it may signal that the model needs recalibration.

![Overlay waterfall](/img/screenshots/step-7-waterfall.png)
*The ECL waterfall showing model ECL, overlay adjustments, and the final adjusted figure.*

### 6. Review the Overlay Register

The **Overlay Register** is a table listing all active overlays for the current project:

| Column | What It Shows |
|--------|--------------|
| **ID** | Unique identifier (e.g., OVL-001) |
| **Product** | Which product type is affected |
| **Type** | The overlay type (PD Uplift, LGD Reduction, etc.) |
| **Amount** | The ECL adjustment in currency |
| **Reason** | The documented justification |
| **IFRS 9 Ref** | The standard paragraph reference |
| **Classification** | Temporary or Permanent |
| **Expiry** | When the overlay is due for review |
| **Approved By** | Who approved the overlay |

You can edit or delete overlays from this register. Each change is recorded in the audit trail.

### 7. Check the Governance Dashboard

The governance panel at the bottom of the page shows:

- **Total Net Overlay** — the sum of all overlay amounts (positive = net upward, negative = net downward)
- **Overlay as % of Model ECL** — how large the adjustment is relative to the model output
- **Cap Status** — whether the total is within the 15% cap (green) or approaching/exceeding it (amber/red)
- **Classification Distribution** — how many overlays are Temporary vs. Permanent

If the cap is exceeded, the platform flags this and requires Board Risk Committee escalation before the project can proceed to Sign-Off.

### 8. Submit for Approval

After adding all overlays, save the overlay register. The overlays enter the maker-checker approval workflow:

1. The maker's changes are saved with a comment explaining the batch of adjustments
2. The checker (CRO or delegate) reviews each overlay's rationale and amount
3. Approved overlays become part of the project's ECL calculation
4. Rejected overlays are returned with comments for the maker to revise

## Understanding the Results

The adjusted ECL (Model ECL + Net Overlays) is the figure that will be presented for sign-off in Step 8 and used for GL journal entries. It represents the institution's best estimate of credit losses, combining model-driven analysis with expert judgment.

**Coverage ratio** after overlays tells the full story: if the model produced a 2.1% coverage ratio and overlays increased it to 2.4%, the management judgment is that the model alone understates risk by about 0.3 percentage points.

**Overlay materiality** is closely scrutinized by auditors. They will examine whether overlays are:
- Directionally consistent with the stress testing findings from Step 6
- Supported by documented rationale (not vague or generic)
- Within the governance cap
- Classified and expired appropriately

## Tips & Best Practices

:::tip Link Overlays to Stress Testing Findings
The strongest overlays reference specific findings from Step 6. For example: "Sensitivity analysis showed ECL increases 15% under the Severe PD scenario for commercial real estate. This overlay captures the incremental risk from rising vacancy rates not reflected in the historical PD model."
:::

:::tip Keep Overlay Reasons Specific
Avoid generic reasons like "Management judgment" or "Conservative approach." Instead, cite the specific risk factor, the evidence that supports it, and why the model cannot capture it. Specific reasons survive audit scrutiny; generic ones do not.
:::

:::warning Monitor the 15% Cap Throughout the Quarter
As you add overlays across multiple projects, track the cumulative overlay position. Institutions that consistently approach the 15% cap should consider whether the underlying model needs recalibration rather than relying on overlays to bridge the gap.
:::

:::caution Temporary Overlays Must Not Become Permanent by Default
If a temporary overlay is extended quarter after quarter, it is effectively permanent. The platform flags overlays that have been extended more than once, prompting a review of whether the overlay should be reclassified as permanent — which triggers a model redevelopment assessment.
:::

## What's Next?

Proceed to [Step 8: Sign-Off](step-8-sign-off) to review the final ECL summary, complete the attestation, and lock the calculation for the reporting period.

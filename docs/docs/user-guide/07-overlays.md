---
sidebar_position: 8
title: "Step 7: Overlays"
---

# Step 7: Overlays

Apply management post-model adjustments for risks not captured by the statistical model.

**IFRS 9 Reference:** B5.5.17 — management judgement and expert credit assessment.

## What This Step Does

Management overlays are adjustments to the model-computed ECL that account for emerging risks, sector-specific concerns, or other factors that the statistical model cannot capture. Each overlay requires justification and is subject to governance controls.

## Key Metrics (KPI Row)

| Metric | Description |
|--------|-------------|
| Active Overlays | Number of overlays currently applied |
| Net Impact | Sum of all overlay amounts |
| Model ECL | ECL before overlays |
| Adjusted ECL | ECL after overlays |

## ECL Waterfall Chart

A waterfall chart visualises the impact of each overlay:

**Model ECL** → Overlay 1 (+/-) → Overlay 2 (+/-) → ... → **Adjusted ECL**

Red bars indicate uplifts (increased ECL), green bars indicate reductions.

## Overlay Governance Framework

Four governance tiles:

| Control | Description |
|---------|-------------|
| Overlay Cap | Total overlays must not exceed 15% of Model ECL |
| Approval Required | Maker-checker process for all overlays |
| Expiry Policy | Maximum 2 quarters before mandatory review |
| Classification | Temporary or Permanent |

A red warning banner appears if the overlay cap is exceeded.

## Adding Overlays

Click **Add Overlay** to create a new adjustment. Each overlay has:

| Field | Description |
|-------|-------------|
| Overlay ID | Auto-generated (OVL-001, OVL-002, etc.) |
| Type | PD Uplift, LGD Uplift, PD Reduction, LGD Reduction, or EAD Adjustment |
| Classification | Temporary or Permanent |
| Product | Which product type the overlay applies to |
| Reason/Justification | Mandatory explanation for the adjustment |
| Amount | The dollar amount of the adjustment |
| IFRS 9 Reference | Supporting paragraph reference (e.g., B5.5.17(p)) |
| Approved By | Name of the approver |
| Expiry Date | When the overlay should be reviewed/removed |

## Validation Rules

- Every overlay must have a non-empty Product, Reason, and non-zero Amount.
- If the net overlay exceeds 15% of Model ECL, a governance warning is displayed (but does not block submission).

## Submitting Overlays

1. Add or modify overlays as needed.
2. Provide an overall justification in the summary text area.
3. Review the validation checklist for any errors.
4. Click **Submit Overlays**.

:::tip
Pre-populated example overlays are provided as templates. Modify or remove them as appropriate for your portfolio.
:::

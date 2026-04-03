---
sidebar_position: 3
title: Quick Start
---

# Quick Start

Run your first ECL calculation in 15 minutes.

## Prerequisites

- Application deployed and accessible ([Installation](/getting-started/installation))
- Admin configuration complete (data sources mapped, models configured)
- Loan data available in Unity Catalog

## Step-by-Step

### 1. Create a Project

Navigate to the app and you'll land on **Step 1: Create Project**.

- Enter a **Project ID** (e.g., `q4_2025_ecl`)
- Enter a **Project Name** (e.g., "Q4 2025 ECL Calculation")
- Select **Accounting Framework** (IFRS 9)
- Set the **Reporting Date** (e.g., 2025-12-31)
- Click **Create Project**

### 2. Review Portfolio Data

Click **Next** to advance to **Step 2: Data Processing**.

- Review the portfolio summary: total loans, GCA, stage distribution
- Check the data quality score (aim for > 90%)
- Click **Mark Complete** when satisfied

### 3. Validate Staging

Advance to **Step 3: Data Control**.

- Review SICR staging logic (DPD thresholds, PD triggers)
- Verify stage migration patterns look reasonable
- Approve the data control step

### 4. Train Satellite Models

Advance to **Step 4: Satellite Model**.

- The system trains 8 models linking macro variables to default rates
- Compare model performance (R², RMSE, feature importance)
- Select the best-performing model as champion

### 5. Run Monte Carlo Simulation

Advance to **Step 5: Model Execution**.

- Configure simulation parameters (or use defaults)
- Click **Run In-App** for immediate results, or **Run as Databricks Job** for larger runs
- Review ECL by product, scenario, and stage

### 6. Stress Testing

Advance to **Step 6: Stress Testing**.

- Review scenario analysis across 8 macroeconomic scenarios
- Check sensitivity analysis and concentration risk
- Approve stress testing results

### 7. Apply Overlays

Advance to **Step 7: Overlays**.

- Add management overlays if needed (temporary or permanent)
- Provide justification for each overlay
- Submit for approval

### 8. Sign Off

Advance to **Step 8: Sign Off**.

- Review final ECL summary tables
- Check all 4 attestation boxes
- Enter preparer and approver names
- Click **Sign Off & Lock Project**

Your ECL calculation is now complete and locked. GL journal entries are auto-generated and available for posting.

## What's Next?

- [User Guide](/user-guide/overview) — Detailed instructions for each step
- [Admin Guide](/admin-guide/overview) — Configure the system
- [IFRS 9 Concepts](/reference/ifrs9-concepts) — Understand the methodology

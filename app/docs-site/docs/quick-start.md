---
sidebar_position: 2
title: "Your First ECL Project"
description: "A step-by-step guide to logging in, navigating the platform, and creating your first Expected Credit Loss project."
---

# Your First ECL Project

This guide walks you through your first session with the IFRS 9 ECL Platform — from login to seeing your first ECL results. You should be able to complete this in about 15 minutes.

:::info Prerequisites
- Access to the platform (URL provided by your administrator)
- An active user account with at least the **Analyst** role
- A portfolio dataset loaded by your administrator (or the sample data that ships with the platform)
:::

## Step 1: Log In and Explore the Dashboard

Open the platform URL in your browser. After authentication, you will see the home dashboard.

![Home dashboard showing project list and navigation](/img/guides/ecl-homepage.png)
*The home dashboard displays your existing projects, recent activity, and the main navigation.*

The interface has three main areas:

- **Sidebar** — Navigate between projects, the 8-step workflow, and administrative functions
- **Top navigation** — Switch projects, access settings, toggle light/dark mode
- **Main content area** — Displays the current page with data, charts, and forms

## Step 2: Create a New Project

1. Click **Create Project** in the sidebar or from the dashboard
2. Fill in the project details:
   - **Project Name** — A descriptive name (e.g., "Q4 2025 ECL Run")
   - **Reporting Date** — The period-end date for this ECL calculation
   - **Base Currency** — The reporting currency (e.g., USD, EUR, GBP)
3. Click **Create**

![Create project form](/img/guides/ecl-create-project.png)
*The project creation form captures the essential metadata for your ECL run.*

Your new project opens at **Step 1** of the 8-step workflow.

## Step 3: Review Your Portfolio Data

Navigate to **Step 2: Data Processing** in the workflow stepper. This page shows:

- **Portfolio summary** — Total exposure, number of loans, product type breakdown
- **Stage distribution** — How loans are distributed across Stage 1, 2, and 3
- **Key performance indicators** — Default rates, average PD, average LGD

![Portfolio dashboard with stage distribution](/img/guides/portfolio-dashboard.png)
*The data processing page provides an at-a-glance view of your portfolio health.*

:::tip
If this is your first time, the platform ships with sample data — 79,000 loans across 5 product types — so you can explore all features without needing live data.
:::

## Step 4: Run a Simulation

Once you have progressed through data control (Step 3) and satellite model selection (Step 4), you can run a Monte Carlo simulation at **Step 5: Model Execution**.

1. Review the simulation parameters (number of iterations, scenario weights)
2. Click **Run Simulation**
3. Watch the real-time progress bar as the engine computes

![Monte Carlo simulation in progress](/img/guides/monte-carlo-panel.png)
*The simulation panel shows real-time progress and convergence diagnostics.*

When complete, you will see:

- **Total ECL** across all stages and scenarios
- **ECL by stage** — breakdown by Stage 1, 2, and 3
- **Scenario comparison** — how ECL varies across base, optimistic, and pessimistic scenarios
- **Confidence intervals** — statistical bounds on the ECL estimate

![Simulation results with ECL breakdown](/img/guides/simulation-results.png)
*Simulation results show ECL broken down by stage, product type, and macroeconomic scenario.*

## Step 5: Review and Sign Off

After completing stress testing (Step 6) and applying any management overlays (Step 7):

1. Navigate to **Step 8: Sign-Off**
2. Review the final ECL summary
3. Add any attestation notes
4. Click **Sign Off** to lock the calculation

:::warning Segregation of Duties
The platform enforces IFRS 9 governance: the person who signs off cannot be the same person who executed the model. A different authorized user must perform the final approval.
:::

Once signed off, the project is locked. All calculations, data, and decisions are preserved with hash verification for audit purposes.

## What's Next?

Now that you have completed your first project, explore these areas:

- [**8-Step Workflow Overview**](user-guide/workflow-overview) — Understand each step in detail
- [**Regulatory Reports**](user-guide/regulatory-reports) — Generate IFRS 7 disclosures
- [**GL Journals**](user-guide/gl-journals) — Create provisioning journal entries
- [**Backtesting**](user-guide/backtesting) — Validate model performance over time
- [**FAQ**](user-guide/faq) — Answers to common questions

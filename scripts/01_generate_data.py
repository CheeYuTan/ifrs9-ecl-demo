"""
IFRS 9 ECL Synthetic Data Generation - Horizon Financial
=========================================================
Generates 7 realistic tables for an inclusive lending IFRS 9 ECL application:
1. borrower_master     - 62,000 borrowers (underbanked + young professionals)
2. loan_tape           - 85,000 active loans across 5 product types
3. payment_history     - ~1.8M monthly payment records (24 months)
4. general_ledger      - GL trial balance for loan accounts
5. macro_scenarios     - 8 economic scenarios x 12 quarters
6. collateral_register - Savings deposits backing credit-builder loans
7. historical_defaults - 5 years of observed defaults and recoveries
"""

import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "faker", "-q"])

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from faker import Faker
from pyspark.sql import SparkSession

# =============================================================================
# CONFIGURATION
# =============================================================================
CATALOG = "lakemeter_catalog"
SCHEMA = "expected_credit_loss"
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

REPORTING_DATE = date(2025, 12, 31)
SEED = 42

N_BORROWERS = 62000
N_LOANS = 85000

PRODUCT_TYPES = {
    "credit_builder": {
        "count_pct": 0.176,       # ~15,000 loans
        "principal_range": (800, 1200),
        "term_months": (6, 12),
        "eir_range": (0.06, 0.10),
        "secured": True,
        "borrower_segment": "underbanked",
    },
    "emergency_microloan": {
        "count_pct": 0.282,       # ~24,000 loans
        "principal_range": (500, 2500),
        "term_months": (3, 6),
        "eir_range": (0.14, 0.22),
        "secured": False,
        "borrower_segment": "underbanked",
    },
    "career_transition": {
        "count_pct": 0.306,       # ~26,000 loans
        "principal_range": (3000, 10000),
        "term_months": (12, 24),
        "eir_range": (0.10, 0.15),
        "secured": False,
        "borrower_segment": "young_professional",
    },
    "bnpl_professional": {
        "count_pct": 0.176,       # ~15,000 loans
        "principal_range": (200, 2000),
        "term_months": (2, 4),
        "eir_range": (0.04, 0.08),
        "secured": False,
        "borrower_segment": "young_professional",
    },
    "payroll_advance": {
        "count_pct": 0.059,       # ~5,000 loans
        "principal_range": (100, 500),
        "term_months": (1, 1),
        "eir_range": (0.08, 0.12),
        "secured": False,
        "borrower_segment": "both",
    },
}

# =============================================================================
# SETUP
# =============================================================================
np.random.seed(SEED)
Faker.seed(SEED)
fake = Faker()
spark = SparkSession.builder.getOrCreate()

print("=" * 70)
print("IFRS 9 ECL - Synthetic Data Generation")
print(f"Target: {FULL_SCHEMA}")
print(f"Reporting Date: {REPORTING_DATE}")
print("=" * 70)

# =============================================================================
# 1. BORROWER MASTER
# =============================================================================
print("\n[1/7] Generating borrower_master...")

borrowers_data = []
for i in range(N_BORROWERS):
    borrower_id = f"BRW-{fake.uuid4()[:8].upper()}"

    if i < N_BORROWERS * 0.55:
        segment = "underbanked"
        age = int(np.clip(np.random.normal(38, 10), 21, 65))
        income_source = np.random.choice(
            ["gig_worker", "informal_employment", "micro_entrepreneur", "seasonal_worker", "mixed"],
            p=[0.30, 0.25, 0.20, 0.10, 0.15]
        )
        monthly_income = round(np.random.lognormal(7.0, 0.5), 2)
        employment_tenure_months = int(np.clip(np.random.exponential(18), 0, 120))
        education = np.random.choice(
            ["primary", "secondary", "vocational", "some_college"],
            p=[0.15, 0.40, 0.25, 0.20]
        )
        formal_credit_score = None if np.random.random() < 0.6 else int(np.clip(np.random.normal(520, 60), 300, 650))
    else:
        segment = "young_professional"
        age = int(np.clip(np.random.normal(26, 3), 22, 35))
        income_source = np.random.choice(
            ["full_time_employed", "contract_worker", "freelancer", "part_time_employed"],
            p=[0.50, 0.20, 0.20, 0.10]
        )
        monthly_income = round(np.random.lognormal(7.8, 0.4), 2)
        employment_tenure_months = int(np.clip(np.random.exponential(12), 0, 60))
        education = np.random.choice(
            ["bachelors", "masters", "some_college", "vocational"],
            p=[0.50, 0.25, 0.15, 0.10]
        )
        formal_credit_score = None if np.random.random() < 0.3 else int(np.clip(np.random.normal(620, 50), 450, 750))

    rent_payment_score = round(np.clip(np.random.beta(5, 2) * 100, 0, 100), 1)
    utility_payment_score = round(np.clip(np.random.beta(4, 2) * 100, 0, 100), 1)
    mobile_money_velocity = round(np.clip(np.random.lognormal(4.5, 0.8), 10, 5000), 2)
    bank_account_age_months = int(np.clip(np.random.exponential(24), 0, 180))

    alt_data_composite = round(
        0.30 * rent_payment_score +
        0.25 * utility_payment_score +
        0.25 * min(mobile_money_velocity / 50, 100) +
        0.20 * min(bank_account_age_months / 1.2, 100),
        1
    )

    country = "PH"
    region = np.random.choice([
        "NCR", "CALABARZON", "Central Luzon", "Central Visayas",
        "Western Visayas", "Davao Region", "Northern Mindanao",
        "Ilocos Region", "Bicol Region", "Eastern Visayas",
        "Zamboanga Peninsula", "SOCCSKSARGEN", "Caraga", "BARMM",
        "Cordillera", "Cagayan Valley", "MIMAROPA",
    ])

    borrowers_data.append({
        "borrower_id": borrower_id,
        "segment": segment,
        "age": age,
        "gender": np.random.choice(["M", "F", "O"], p=[0.48, 0.48, 0.04]),
        "country": country,
        "region": region,
        "income_source": income_source,
        "monthly_income": monthly_income,
        "employment_tenure_months": employment_tenure_months,
        "education_level": education,
        "formal_credit_score": formal_credit_score,
        "rent_payment_score": rent_payment_score,
        "utility_payment_score": utility_payment_score,
        "mobile_money_velocity": mobile_money_velocity,
        "bank_account_age_months": bank_account_age_months,
        "alt_data_composite_score": alt_data_composite,
        "has_student_loan": segment == "young_professional" and np.random.random() < 0.65,
        "dependents": int(np.random.choice([0, 1, 2, 3, 4], p=[0.30, 0.25, 0.25, 0.15, 0.05])),
        "onboarding_date": fake.date_between(
            start_date=date(2020, 1, 1),
            end_date=date(2025, 6, 30)
        ).isoformat(),
    })

borrowers_pdf = pd.DataFrame(borrowers_data)
borrower_ids = borrowers_pdf["borrower_id"].tolist()
borrower_segment_map = dict(zip(borrowers_pdf["borrower_id"], borrowers_pdf["segment"]))
borrower_alt_score_map = dict(zip(borrowers_pdf["borrower_id"], borrowers_pdf["alt_data_composite_score"]))

print(f"  Generated {len(borrowers_pdf):,} borrowers")
print(f"  Segment split: {borrowers_pdf['segment'].value_counts().to_dict()}")

# =============================================================================
# 2. LOAN TAPE
# =============================================================================
print("\n[2/7] Generating loan_tape...")

loans_data = []
loan_idx = 0

for product, config in PRODUCT_TYPES.items():
    n_product = int(N_LOANS * config["count_pct"])
    print(f"  Generating {n_product:,} {product} loans...")

    segment_filter = config["borrower_segment"]
    if segment_filter == "both":
        eligible_borrowers = borrower_ids
    else:
        eligible_borrowers = [b for b in borrower_ids if borrower_segment_map[b] == segment_filter]

    for _ in range(n_product):
        loan_idx += 1
        loan_id = f"LN-{loan_idx:06d}"
        borrower_id = np.random.choice(eligible_borrowers)

        term = int(np.random.uniform(config["term_months"][0], config["term_months"][1] + 1))
        origination_date = fake.date_between(
            start_date=REPORTING_DATE - timedelta(days=term * 35),
            end_date=REPORTING_DATE - timedelta(days=30)
        )
        maturity_date = origination_date + timedelta(days=term * 30)
        months_on_book = max(1, (REPORTING_DATE - origination_date).days // 30)
        remaining_months = max(0, (maturity_date - REPORTING_DATE).days // 30)

        principal = round(np.random.uniform(*config["principal_range"]), 2)
        eir = round(np.random.uniform(*config["eir_range"]), 4)

        monthly_rate = eir / 12
        if term > 0 and monthly_rate > 0:
            monthly_payment = principal * monthly_rate / (1 - (1 + monthly_rate) ** (-term))
        else:
            monthly_payment = principal / max(term, 1)
        payments_made = min(months_on_book, term)
        outstanding_principal = principal
        for _m in range(payments_made):
            interest_portion = outstanding_principal * monthly_rate
            principal_portion = monthly_payment - interest_portion
            outstanding_principal = max(0, outstanding_principal - principal_portion)
        gross_carrying_amount = round(max(outstanding_principal, 0), 2)

        alt_score = borrower_alt_score_map.get(borrower_id, 50)

        product_base_pd = {
            "credit_builder": 0.025, "emergency_microloan": 0.06,
            "career_transition": 0.04, "bnpl_professional": 0.035,
            "payroll_advance": 0.07,
        }
        base_pd = product_base_pd.get(product, 0.04)
        score_adj = (70 - alt_score) / 500
        origination_pd = round(np.clip(base_pd + score_adj + np.random.normal(0, 0.008), 0.005, 0.30), 4)

        base_dpd_prob = origination_pd * 2.5
        if np.random.random() < base_dpd_prob:
            if np.random.random() < 0.6:
                days_past_due = int(np.random.uniform(1, 30))
            elif np.random.random() < 0.7:
                days_past_due = int(np.random.uniform(30, 90))
            else:
                days_past_due = int(np.random.uniform(90, 270))
        else:
            days_past_due = 0

        origination_alt_score = round(alt_score + np.random.normal(0, 5), 1)
        current_alt_score = round(alt_score + np.random.normal(0, 8), 1)

        dpd_factor = 1.0 + (days_past_due / 150) ** 1.3
        score_factor = 1.0 + max(0, (origination_alt_score - current_alt_score)) / 150
        aging_factor = 1.0 + months_on_book * 0.003
        current_pd = round(np.clip(origination_pd * dpd_factor * score_factor * aging_factor, 0.005, 0.80), 4)

        pd_ratio = current_pd / max(origination_pd, 0.001)
        score_drop = origination_alt_score - current_alt_score

        if days_past_due >= 90:
            current_stage = 3
        elif days_past_due >= 30 or pd_ratio > 2.5 or score_drop > 20:
            current_stage = 2
        else:
            current_stage = 1

        # Prior stage: simulate that most loans were Stage 1 last quarter,
        # with some already in Stage 2/3 (cured or deteriorated)
        if current_stage == 1:
            prior_stage = np.random.choice([1, 2], p=[0.95, 0.05])
        elif current_stage == 2:
            prior_stage = np.random.choice([1, 2, 3], p=[0.40, 0.50, 0.10])
        else:
            prior_stage = np.random.choice([2, 3], p=[0.35, 0.65])

        # Cure period: loans moving from Stage 2/3 back to Stage 1 require
        # 3 consecutive on-time payments (probation)
        consecutive_on_time = 0 if days_past_due > 0 else int(np.clip(np.random.geometric(0.3), 1, 12))
        in_probation = prior_stage > current_stage and consecutive_on_time < 3
        if in_probation:
            current_stage = prior_stage

        is_restructured = days_past_due > 60 and np.random.random() < 0.15
        if is_restructured and current_stage < 2:
            current_stage = 2

        # Write-off: Stage 3 loans past 180 DPD with probability
        is_write_off = days_past_due >= 180 and np.random.random() < 0.60

        loans_data.append({
            "loan_id": loan_id,
            "borrower_id": borrower_id,
            "product_type": product,
            "origination_date": origination_date.isoformat(),
            "maturity_date": maturity_date.isoformat(),
            "original_principal": principal,
            "gross_carrying_amount": gross_carrying_amount,
            "effective_interest_rate": eir,
            "contractual_term_months": term,
            "months_on_book": months_on_book,
            "remaining_months": remaining_months,
            "days_past_due": days_past_due,
            "origination_pd": origination_pd,
            "current_lifetime_pd": current_pd,
            "origination_alt_score": origination_alt_score,
            "current_alt_score": current_alt_score,
            "current_stage": current_stage,
            "prior_stage": prior_stage,
            "consecutive_on_time_payments": consecutive_on_time,
            "is_restructured": is_restructured,
            "is_write_off": is_write_off,
            "currency": "USD",
            "reporting_date": REPORTING_DATE.isoformat(),
        })

loans_pdf = pd.DataFrame(loans_data)
loan_ids = loans_pdf["loan_id"].tolist()
loan_product_map = dict(zip(loans_pdf["loan_id"], loans_pdf["product_type"]))
loan_borrower_map = dict(zip(loans_pdf["loan_id"], loans_pdf["borrower_id"]))
loan_gca_map = dict(zip(loans_pdf["loan_id"], loans_pdf["gross_carrying_amount"]))

print(f"  Generated {len(loans_pdf):,} loans")
print(f"  Product distribution:\n{loans_pdf['product_type'].value_counts().to_string()}")
print(f"  Stage distribution:\n{loans_pdf['current_stage'].value_counts().sort_index().to_string()}")
print(f"  Total gross carrying amount: ${loans_pdf['gross_carrying_amount'].sum():,.0f}")

# =============================================================================
# 3. PAYMENT HISTORY (24 months of monthly payments)
# =============================================================================
print("\n[3/7] Generating payment_history...")

payment_data = []
payment_start = REPORTING_DATE - timedelta(days=730)

sample_loans = loans_pdf.sample(min(len(loans_pdf), 60000), random_state=SEED)

for _, loan in sample_loans.iterrows():
    orig = date.fromisoformat(loan["origination_date"])
    start = max(orig, payment_start)
    n_payments = max(1, min(24, (REPORTING_DATE - start).days // 30))
    dpd = loan["days_past_due"]
    product = loan["product_type"]

    if dpd == 0:
        late_prob = 0.05
    elif dpd < 30:
        late_prob = 0.25
    elif dpd < 90:
        late_prob = 0.50
    else:
        late_prob = 0.80

    monthly_amt = loan["original_principal"] / max(loan["contractual_term_months"], 1)

    for m in range(n_payments):
        pay_date = start + timedelta(days=30 * (m + 1))
        if pay_date > REPORTING_DATE:
            break

        amount_due = round(monthly_amt, 2)

        if np.random.random() < late_prob:
            days_late = int(np.random.exponential(15)) + 1
            if np.random.random() < 0.1:
                amount_paid = 0
                payment_status = "missed"
            else:
                amount_paid = round(amount_due * np.random.uniform(0.5, 1.0), 2)
                payment_status = "partial" if amount_paid < amount_due * 0.99 else "late"
        else:
            days_late = 0
            amount_paid = amount_due
            payment_status = "on_time"

        payment_method = np.random.choice(
            ["mobile_money", "bank_transfer", "cash", "payroll_deduction", "card"],
            p=[0.35, 0.25, 0.15, 0.15, 0.10]
        )

        payment_data.append({
            "loan_id": loan["loan_id"],
            "payment_date": pay_date.isoformat(),
            "payment_period": m + 1,
            "amount_due": amount_due,
            "amount_paid": amount_paid,
            "days_late": days_late,
            "payment_status": payment_status,
            "payment_method": payment_method,
        })

payments_pdf = pd.DataFrame(payment_data)
print(f"  Generated {len(payments_pdf):,} payment records")
print(f"  Payment status distribution:\n{payments_pdf['payment_status'].value_counts().to_string()}")

# =============================================================================
# 4. GENERAL LEDGER
# =============================================================================
print("\n[4/7] Generating general_ledger...")

product_gca = loans_pdf.groupby("product_type")["gross_carrying_amount"].sum()

gl_data = []
for product, total in product_gca.items():
    variance = round(np.random.uniform(-0.003, 0.003) * total, 2)
    if product == "emergency_microloan":
        variance = 200000.0

    gl_data.append({
        "account_code": f"1{list(PRODUCT_TYPES.keys()).index(product) + 1}00",
        "account_name": f"Loans Receivable - {product.replace('_', ' ').title()}",
        "account_type": "asset",
        "gl_balance": round(total + variance, 2),
        "loan_tape_balance": round(total, 2),
        "variance": round(variance, 2),
        "as_of_date": REPORTING_DATE.isoformat(),
        "currency": "USD",
    })

    gl_data.append({
        "account_code": f"2{list(PRODUCT_TYPES.keys()).index(product) + 1}00",
        "account_name": f"ECL Allowance - {product.replace('_', ' ').title()}",
        "account_type": "contra_asset",
        "gl_balance": round(-total * np.random.uniform(0.02, 0.12), 2),
        "loan_tape_balance": None,
        "variance": None,
        "as_of_date": REPORTING_DATE.isoformat(),
        "currency": "USD",
    })

gl_data.append({
    "account_code": "3100",
    "account_name": "Interest Receivable - All Products",
    "account_type": "asset",
    "gl_balance": round(loans_pdf["gross_carrying_amount"].sum() * 0.008, 2),
    "loan_tape_balance": None,
    "variance": None,
    "as_of_date": REPORTING_DATE.isoformat(),
    "currency": "USD",
})

gl_pdf = pd.DataFrame(gl_data)
print(f"  Generated {len(gl_pdf):,} GL entries")

# =============================================================================
# 5. MACROECONOMIC SCENARIOS
# =============================================================================
print("\n[5/7] Generating macro_scenarios...")

macro_data = []

# 8 plausible economic scenarios spanning a realistic range of outcomes.
# Each scenario represents a coherent macro-economic narrative with
# correlated shocks across GDP, unemployment, inflation, and interest rates.
scenarios = {
    "baseline": {
        "weight": 0.30,
        "description": "Current trajectory continues",
        "unemployment_adj": 0, "gdp_adj": 0, "inflation_adj": 0,
    },
    "mild_recovery": {
        "weight": 0.15,
        "description": "Gradual improvement in labor market and consumer spending",
        "unemployment_adj": -0.8, "gdp_adj": 0.5, "inflation_adj": -0.3,
    },
    "strong_growth": {
        "weight": 0.05,
        "description": "Rapid expansion driven by digital economy boom",
        "unemployment_adj": -1.5, "gdp_adj": 1.5, "inflation_adj": 0.5,
    },
    "mild_downturn": {
        "weight": 0.15,
        "description": "Modest slowdown with rising delinquencies",
        "unemployment_adj": 1.5, "gdp_adj": -0.8, "inflation_adj": 0.5,
    },
    "adverse": {
        "weight": 0.15,
        "description": "Recession with significant job losses in gig/informal sector",
        "unemployment_adj": 3.0, "gdp_adj": -1.5, "inflation_adj": 1.5,
    },
    "stagflation": {
        "weight": 0.08,
        "description": "High inflation + stagnant growth, rate hikes squeeze borrowers",
        "unemployment_adj": 2.0, "gdp_adj": -1.0, "inflation_adj": 3.5,
    },
    "severely_adverse": {
        "weight": 0.07,
        "description": "Deep recession, credit markets freeze, mass defaults",
        "unemployment_adj": 6.0, "gdp_adj": -3.0, "inflation_adj": 2.0,
    },
    "tail_risk": {
        "weight": 0.05,
        "description": "Systemic crisis: pandemic-scale shock to emerging markets",
        "unemployment_adj": 8.0, "gdp_adj": -5.0, "inflation_adj": 4.0,
    },
}

for scenario_name, params in scenarios.items():
    for q in range(12):
        quarter_date = REPORTING_DATE + timedelta(days=90 * (q + 1))
        quarter_label = f"Q{((quarter_date.month - 1) // 3) + 1}-{quarter_date.year}"

        # Non-linear mean-reversion: shocks peak at Q2-Q3 then decay
        if q <= 2:
            shock_factor = 0.7 + q * 0.1  # ramp up: 0.7, 0.8, 0.9
        elif q <= 4:
            shock_factor = 1.0  # peak stress
        else:
            shock_factor = max(0.1, 1.0 - (q - 4) * 0.12)  # gradual decay

        base_unemployment = 5.2 + np.random.normal(0, 0.15)
        base_gdp = 2.1 + np.random.normal(0, 0.2)
        base_inflation = 3.5 + np.random.normal(0, 0.15)
        base_interest_rate = 4.5 + np.random.normal(0, 0.1)
        base_gig_index = 52 + np.random.normal(0, 1.5)
        base_consumer_confidence = 98 + np.random.normal(0, 2)

        # Interest rate responds to both inflation AND growth shocks
        rate_adj = params["inflation_adj"] * 0.4 - min(params["gdp_adj"], 0) * 0.15

        macro_data.append({
            "scenario_name": scenario_name,
            "scenario_weight": params["weight"],
            "scenario_description": params["description"],
            "forecast_quarter": quarter_label,
            "forecast_date": quarter_date.isoformat(),
            "quarters_ahead": q + 1,
            "unemployment_rate": round(base_unemployment + params["unemployment_adj"] * shock_factor, 2),
            "gdp_growth_rate": round(base_gdp + params["gdp_adj"] * shock_factor, 2),
            "inflation_rate": round(base_inflation + params["inflation_adj"] * shock_factor, 2),
            "policy_interest_rate": round(base_interest_rate + rate_adj * shock_factor, 2),
            "gig_economy_index": round(base_gig_index - params["unemployment_adj"] * 3 * shock_factor, 1),
            "consumer_confidence_index": round(base_consumer_confidence - params["unemployment_adj"] * 5 * shock_factor, 1),
            "reporting_date": REPORTING_DATE.isoformat(),
        })

macro_pdf = pd.DataFrame(macro_data)
print(f"  Generated {len(macro_pdf):,} macro scenario records ({len(scenarios)} scenarios x 12 quarters)")

# =============================================================================
# 6. COLLATERAL REGISTER (credit_builder loans only)
# =============================================================================
print("\n[6/7] Generating collateral_register...")

cb_loans = loans_pdf[loans_pdf["product_type"] == "credit_builder"]
collateral_data = []

for _, loan in cb_loans.iterrows():
    savings_balance = loan["original_principal"]

    if loan["days_past_due"] > 60:
        erosion = np.random.uniform(0.1, 0.4)
    elif loan["days_past_due"] > 30:
        erosion = np.random.uniform(0.0, 0.15)
    else:
        erosion = np.random.uniform(-0.05, 0.05)

    current_value = round(savings_balance * (1 - erosion), 2)
    ltv = round(loan["gross_carrying_amount"] / max(current_value, 1), 4)

    collateral_data.append({
        "loan_id": loan["loan_id"],
        "collateral_type": "savings_deposit",
        "original_collateral_value": savings_balance,
        "current_collateral_value": current_value,
        "loan_to_value_ratio": ltv,
        "last_valuation_date": (REPORTING_DATE - timedelta(days=np.random.randint(0, 30))).isoformat(),
        "collateral_status": "impaired" if current_value < loan["gross_carrying_amount"] * 0.8 else "adequate",
        "reporting_date": REPORTING_DATE.isoformat(),
    })

collateral_pdf = pd.DataFrame(collateral_data)
print(f"  Generated {len(collateral_pdf):,} collateral records")

# =============================================================================
# 7. HISTORICAL DEFAULTS (5 years of observed defaults)
#    Defaults are correlated with macro conditions so that regression-based
#    satellite model calibration produces meaningful coefficients.
# =============================================================================
print("\n[7/7] Generating historical_defaults (macro-correlated)...")

# Historical macro conditions (Q1-2021 to Q4-2025 = 20 quarters).
# These are PAST observations (not forward-looking scenarios) used to calibrate
# the satellite model via regression: default_rate ~ unemployment + gdp + inflation.
HIST_QUARTERS = []
hist_start = date(2021, 1, 1)
for q in range(20):
    q_date = hist_start + timedelta(days=90 * q)
    q_label = f"Q{((q_date.month - 1) // 3) + 1}-{q_date.year}"
    HIST_QUARTERS.append({"quarter": q_label, "quarter_date": q_date})

# Realistic macro trajectory 2021-2025:
# COVID recovery → normalization → mild tightening → stable
hist_macro = pd.DataFrame({
    "quarter": [q["quarter"] for q in HIST_QUARTERS],
    "quarter_date": [q["quarter_date"] for q in HIST_QUARTERS],
    "unemployment_rate": [
        10.4, 9.3, 8.7, 7.8,   # 2021: COVID recovery
        7.1, 6.5, 6.0, 5.8,    # 2022: normalization
        5.6, 5.4, 5.3, 5.2,    # 2023: stable
        5.3, 5.5, 5.7, 5.4,    # 2024: mild uptick then recovery
        5.2, 5.1, 5.3, 5.2,    # 2025: stable
    ],
    "gdp_growth_rate": [
        -4.2, 1.5, 5.8, 7.1,   # 2021: rebound
        3.2, 2.8, 2.5, 2.3,    # 2022: slowing
        2.0, 2.1, 2.3, 2.5,    # 2023: stable
        2.2, 1.8, 1.5, 2.0,    # 2024: mild dip
        2.1, 2.3, 2.0, 2.1,    # 2025: stable
    ],
    "inflation_rate": [
        4.5, 4.2, 3.8, 3.5,    # 2021: elevated
        4.0, 5.2, 6.1, 5.8,    # 2022: inflation spike
        5.0, 4.2, 3.8, 3.5,    # 2023: normalizing
        3.3, 3.5, 3.8, 3.6,    # 2024: stable
        3.5, 3.4, 3.6, 3.5,    # 2025: stable
    ],
})

# True sensitivity coefficients (hidden ground truth that the regression should recover).
# These define how macro conditions drive default rates per product.
TRUE_COEFFICIENTS = {
    "credit_builder":      {"base_dr": 0.025, "beta_unemp": 0.006, "beta_gdp": -0.004, "beta_infl": 0.001},
    "emergency_microloan": {"base_dr": 0.060, "beta_unemp": 0.012, "beta_gdp": -0.008, "beta_infl": 0.004},
    "career_transition":   {"base_dr": 0.040, "beta_unemp": 0.010, "beta_gdp": -0.007, "beta_infl": 0.003},
    "bnpl_professional":   {"base_dr": 0.035, "beta_unemp": 0.009, "beta_gdp": -0.006, "beta_infl": 0.0025},
    "payroll_advance":     {"base_dr": 0.070, "beta_unemp": 0.014, "beta_gdp": -0.009, "beta_infl": 0.005},
}

# LGD sensitivity to macro (higher unemployment → lower recovery → higher LGD)
TRUE_LGD_COEFFICIENTS = {
    "credit_builder":      {"base_lgd": 0.20, "beta_unemp": 0.020, "beta_gdp": -0.015, "beta_infl": 0.005},
    "emergency_microloan": {"base_lgd": 0.55, "beta_unemp": 0.040, "beta_gdp": -0.030, "beta_infl": 0.010},
    "career_transition":   {"base_lgd": 0.40, "beta_unemp": 0.035, "beta_gdp": -0.025, "beta_infl": 0.008},
    "bnpl_professional":   {"base_lgd": 0.35, "beta_unemp": 0.030, "beta_gdp": -0.020, "beta_infl": 0.008},
    "payroll_advance":     {"base_lgd": 0.65, "beta_unemp": 0.050, "beta_gdp": -0.035, "beta_infl": 0.015},
}

# Portfolio size per product (for generating realistic default counts)
PORTFOLIO_SIZE = {
    "credit_builder": 12000, "emergency_microloan": 20000,
    "career_transition": 22000, "bnpl_professional": 13000, "payroll_advance": 4500,
}

# Generate quarterly default rates driven by macro, then sample individual defaults
defaults_data = []
quarterly_default_rates = []
def_counter = 0

for _, macro_row in hist_macro.iterrows():
    unemp = macro_row["unemployment_rate"]
    gdp = macro_row["gdp_growth_rate"]
    infl = macro_row["inflation_rate"]
    q_date = macro_row["quarter_date"]
    q_label = macro_row["quarter"]

    for product, coeff in TRUE_COEFFICIENTS.items():
        # Quarterly default rate = base + β₁×unemp + β₂×gdp + β₃×infl + noise
        expected_dr = (coeff["base_dr"]
                       + coeff["beta_unemp"] * unemp
                       + coeff["beta_gdp"] * gdp
                       + coeff["beta_infl"] * infl)
        noise = np.random.normal(0, 0.003)
        actual_dr = np.clip(expected_dr + noise, 0.005, 0.30)

        quarterly_default_rates.append({
            "quarter": q_label, "quarter_date": q_date,
            "product_type": product,
            "unemployment_rate": unemp, "gdp_growth_rate": gdp, "inflation_rate": infl,
            "expected_default_rate": round(expected_dr, 6),
            "observed_default_rate": round(actual_dr, 6),
            "portfolio_size": PORTFOLIO_SIZE[product],
        })

        # Sample individual defaults from this quarterly rate
        n_defaults = int(PORTFOLIO_SIZE[product] * actual_dr / 4)  # quarterly
        lgd_coeff = TRUE_LGD_COEFFICIENTS[product]
        expected_lgd = np.clip(
            lgd_coeff["base_lgd"]
            + lgd_coeff["beta_unemp"] * unemp
            + lgd_coeff["beta_gdp"] * gdp
            + lgd_coeff["beta_infl"] * infl,
            0.05, 0.95)

        for _ in range(n_defaults):
            def_counter += 1
            default_date = q_date + timedelta(days=int(np.random.uniform(0, 89)))
            if default_date > REPORTING_DATE:
                continue

            if product == "credit_builder":
                exposure = round(np.random.uniform(400, 1200), 2)
            elif product == "emergency_microloan":
                exposure = round(np.random.uniform(300, 2500), 2)
            elif product == "career_transition":
                exposure = round(np.random.uniform(2000, 10000), 2)
            elif product == "bnpl_professional":
                exposure = round(np.random.uniform(150, 2000), 2)
            else:
                exposure = round(np.random.uniform(80, 500), 2)

            loan_lgd = np.clip(expected_lgd + np.random.normal(0, 0.10), 0.02, 0.98)
            recovery_rate = 1.0 - loan_lgd
            recovery_amount = round(exposure * recovery_rate, 2)
            loss_amount = round(exposure - recovery_amount, 2)
            recovery_lag_days = int(np.random.exponential(90)) + 30
            recovery_date = default_date + timedelta(days=recovery_lag_days)

            defaults_data.append({
                "default_id": f"DEF-{def_counter:06d}",
                "product_type": product,
                "default_date": default_date.isoformat(),
                "quarter": q_label,
                "exposure_at_default": exposure,
                "recovery_amount": recovery_amount,
                "recovery_date": recovery_date.isoformat() if recovery_date <= REPORTING_DATE else None,
                "loss_amount": loss_amount,
                "loss_given_default": round(loan_lgd, 4),
                "default_reason": np.random.choice(
                    ["income_loss", "over_indebtedness", "business_failure", "health_emergency",
                     "employer_closure", "fraud", "voluntary_default", "natural_disaster"],
                    p=[0.25, 0.20, 0.15, 0.12, 0.10, 0.05, 0.08, 0.05]
                ),
                "was_restructured_before_default": np.random.random() < 0.2,
                "months_to_default": int(np.random.exponential(8)) + 1,
            })

defaults_pdf = pd.DataFrame(defaults_data)
quarterly_dr_pdf = pd.DataFrame(quarterly_default_rates)

print(f"  Generated {len(defaults_pdf):,} historical default records across {len(HIST_QUARTERS)} quarters")
print(f"  Generated {len(quarterly_dr_pdf):,} quarterly default rate observations (for regression)")
print(f"  Avg LGD by product:\n{defaults_pdf.groupby('product_type')['loss_given_default'].mean().to_string()}")

# =============================================================================
# SAVE ALL TABLES TO DELTA
# =============================================================================
print("\n" + "=" * 70)
print("Saving all tables to Delta...")
print("=" * 70)

tables = {
    "borrower_master": borrowers_pdf,
    "loan_tape": loans_pdf,
    "payment_history": payments_pdf,
    "general_ledger": gl_pdf,
    "macro_scenarios": macro_pdf,
    "collateral_register": collateral_pdf,
    "historical_defaults": defaults_pdf,
    "quarterly_default_rates": quarterly_dr_pdf,
}

for table_name, pdf in tables.items():
    full_table = f"{FULL_SCHEMA}.{table_name}"
    print(f"  Writing {table_name} ({len(pdf):,} rows)...")
    sdf = spark.createDataFrame(pdf)
    sdf.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(full_table)
    print(f"    -> {full_table} ✓")

# =============================================================================
# VALIDATION
# =============================================================================
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

for table_name in tables:
    full_table = f"{FULL_SCHEMA}.{table_name}"
    count = spark.sql(f"SELECT COUNT(*) as cnt FROM {full_table}").collect()[0]["cnt"]
    print(f"  {table_name}: {count:,} rows")

total_gca = spark.sql(f"SELECT SUM(gross_carrying_amount) as total FROM {FULL_SCHEMA}.loan_tape").collect()[0]["total"]
print(f"\n  Total Gross Carrying Amount: ${total_gca:,.2f}")

stage_dist = spark.sql(f"""
    SELECT current_stage, COUNT(*) as cnt,
           ROUND(SUM(gross_carrying_amount), 2) as total_gca
    FROM {FULL_SCHEMA}.loan_tape
    GROUP BY current_stage ORDER BY current_stage
""").collect()

print("\n  Stage Distribution:")
for row in stage_dist:
    print(f"    Stage {row['current_stage']}: {row['cnt']:,} loans, ${row['total_gca']:,.2f}")

print("\n✅ Data generation complete!")

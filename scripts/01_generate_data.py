"""
IFRS 9 ECL Synthetic Data Generation
=====================================
Generates realistic banking data for an IFRS 9 ECL application.
Product types: Credit Card, Residential Mortgage, Commercial Loan,
Personal Loan, Auto Loan.

Cohort dimensions aligned with IFRS 9 / IFRS 7 requirements:
  - Credit rating grade (internal)
  - Industry sector (commercial)
  - Geography / region
  - Origination vintage
  - Delinquency bucket
  - LTV band (secured products)
  - Employment type
  - Age group

Tables generated:
1. borrower_master       - Borrower demographics & financials
2. loan_tape             - Active loan facilities
3. payment_history       - Monthly payment records (24 months)
4. general_ledger        - GL trial balance for loan accounts
5. macro_scenarios       - Economic scenarios x 12 quarters
6. collateral_register   - Collateral for secured products
7. historical_defaults   - Historical defaults and recoveries
8. quarterly_default_rates - Aggregated default rates for satellite model
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from faker import Faker
from pyspark.sql import SparkSession

# =============================================================================
# CONFIGURATION
# =============================================================================
try:
    CATALOG = dbutils.widgets.get("catalog")  # type: ignore[name-defined]
except Exception:
    CATALOG = "lakemeter_catalog"
try:
    SCHEMA = dbutils.widgets.get("schema")  # type: ignore[name-defined]
except Exception:
    SCHEMA = "expected_credit_loss"
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"

try:
    _rd = dbutils.widgets.get("reporting_date")  # type: ignore[name-defined]
    REPORTING_DATE = date.fromisoformat(_rd)
except Exception:
    REPORTING_DATE = date(2025, 12, 31)

try:
    SEED = int(dbutils.widgets.get("seed"))  # type: ignore[name-defined]
except Exception:
    SEED = 42

try:
    N_BORROWERS = int(dbutils.widgets.get("n_borrowers"))  # type: ignore[name-defined]
except Exception:
    N_BORROWERS = 50000

try:
    N_LOANS = int(dbutils.widgets.get("n_loans"))  # type: ignore[name-defined]
except Exception:
    N_LOANS = 80000

try:
    CURRENCY = dbutils.widgets.get("currency")  # type: ignore[name-defined]
except Exception:
    CURRENCY = "USD"

try:
    COUNTRY = dbutils.widgets.get("country")  # type: ignore[name-defined]
except Exception:
    COUNTRY = "US"

try:
    _pc = dbutils.widgets.get("product_config")  # type: ignore[name-defined]
    PRODUCT_TYPES = json.loads(_pc)
    for k, v in PRODUCT_TYPES.items():
        v["principal_range"] = tuple(v["principal_range"])
        v["term_months"] = tuple(v["term_months"])
        v["eir_range"] = tuple(v["eir_range"])
except Exception:
    PRODUCT_TYPES = {
        "credit_card": {
            "count_pct": 0.30,
            "principal_range": (2000, 50000),
            "term_months": (0, 0),  # revolving
            "eir_range": (0.15, 0.26),
            "base_pd": 0.035,
            "secured": False,
            "collateral_type": None,
            "borrower_segment": "retail",
        },
        "residential_mortgage": {
            "count_pct": 0.25,
            "principal_range": (150000, 800000),
            "term_months": (180, 360),
            "eir_range": (0.035, 0.065),
            "base_pd": 0.012,
            "secured": True,
            "collateral_type": "residential_property",
            "borrower_segment": "retail",
        },
        "commercial_loan": {
            "count_pct": 0.15,
            "principal_range": (100000, 5000000),
            "term_months": (12, 84),
            "eir_range": (0.045, 0.09),
            "base_pd": 0.025,
            "secured": True,
            "collateral_type": "commercial_property",
            "borrower_segment": "commercial",
        },
        "personal_loan": {
            "count_pct": 0.20,
            "principal_range": (5000, 50000),
            "term_months": (12, 60),
            "eir_range": (0.06, 0.18),
            "base_pd": 0.04,
            "secured": False,
            "collateral_type": None,
            "borrower_segment": "retail",
        },
        "auto_loan": {
            "count_pct": 0.10,
            "principal_range": (15000, 80000),
            "term_months": (36, 72),
            "eir_range": (0.04, 0.09),
            "base_pd": 0.02,
            "secured": True,
            "collateral_type": "vehicle",
            "borrower_segment": "retail",
        },
    }

_total_pct = sum(v["count_pct"] for v in PRODUCT_TYPES.values())
if abs(_total_pct - 1.0) > 0.01:
    for v in PRODUCT_TYPES.values():
        v["count_pct"] = v["count_pct"] / _total_pct

# =============================================================================
# REFERENCE DATA
# =============================================================================
REGIONS = [
    "Northeast", "Southeast", "Midwest", "Southwest", "West Coast",
    "Pacific Northwest", "Mountain", "Mid-Atlantic",
]

INDUSTRY_SECTORS = [
    "manufacturing", "professional_services", "retail_trade",
    "construction", "healthcare", "technology",
    "hospitality", "transportation", "real_estate", "agriculture",
]

CREDIT_GRADES = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
CREDIT_GRADE_PD_MULT = {
    "AAA": 0.15, "AA": 0.30, "A": 0.55, "BBB": 0.85,
    "BB": 1.30, "B": 2.00, "CCC": 3.50,
}
CREDIT_GRADE_PROBS_RETAIL = [0.03, 0.08, 0.20, 0.30, 0.22, 0.12, 0.05]
CREDIT_GRADE_PROBS_COMMERCIAL = [0.05, 0.10, 0.22, 0.28, 0.20, 0.10, 0.05]

EMPLOYMENT_TYPES = ["salaried", "self_employed", "business_owner", "retired", "contract"]
EMPLOYMENT_PROBS = [0.45, 0.20, 0.15, 0.10, 0.10]

EDUCATION_LEVELS = ["high_school", "bachelors", "masters", "doctorate", "vocational", "some_college"]
EDUCATION_PROBS = [0.20, 0.35, 0.20, 0.05, 0.10, 0.10]

# =============================================================================
# SETUP
# =============================================================================
np.random.seed(SEED)
Faker.seed(SEED)
fake = Faker("en_US")
spark = SparkSession.builder.getOrCreate()

print("=" * 70)
print("IFRS 9 ECL - Synthetic Data Generation (Banking Portfolio)")
print(f"Target: {FULL_SCHEMA}")
print(f"Reporting Date: {REPORTING_DATE}")
print(f"Products: {', '.join(PRODUCT_TYPES.keys())}")
print("=" * 70)

# =============================================================================
# 1. BORROWER MASTER
# =============================================================================
print("\n[1/7] Generating borrower_master...")

borrowers_data = []
for i in range(N_BORROWERS):
    borrower_id = f"BRW-{i+1:06d}"
    is_commercial = i >= int(N_BORROWERS * 0.80)

    if is_commercial:
        segment = "commercial"
        age = int(np.clip(np.random.normal(48, 10), 25, 75))
        employment_type = np.random.choice(["business_owner", "self_employed"], p=[0.7, 0.3])
        annual_income = round(np.random.lognormal(12.5, 0.8), 2)
        credit_grade = np.random.choice(CREDIT_GRADES, p=CREDIT_GRADE_PROBS_COMMERCIAL)
        industry_sector = np.random.choice(INDUSTRY_SECTORS)
        company_name = fake.company()
        years_in_business = int(np.clip(np.random.exponential(12), 1, 50))
        annual_revenue = round(annual_income * np.random.uniform(3, 20), 2)
    else:
        segment = "retail"
        age = int(np.clip(np.random.normal(42, 14), 21, 80))
        employment_type = np.random.choice(EMPLOYMENT_TYPES, p=EMPLOYMENT_PROBS)
        if employment_type == "retired":
            annual_income = round(np.random.lognormal(10.5, 0.5), 2)
        elif employment_type == "salaried":
            annual_income = round(np.random.lognormal(11.0, 0.6), 2)
        else:
            annual_income = round(np.random.lognormal(10.8, 0.7), 2)
        credit_grade = np.random.choice(CREDIT_GRADES, p=CREDIT_GRADE_PROBS_RETAIL)
        industry_sector = None
        company_name = None
        years_in_business = None
        annual_revenue = None

    credit_score = {
        "AAA": int(np.clip(np.random.normal(800, 15), 780, 850)),
        "AA": int(np.clip(np.random.normal(760, 20), 730, 800)),
        "A": int(np.clip(np.random.normal(720, 25), 680, 770)),
        "BBB": int(np.clip(np.random.normal(680, 30), 620, 740)),
        "BB": int(np.clip(np.random.normal(630, 30), 560, 680)),
        "B": int(np.clip(np.random.normal(570, 35), 500, 630)),
        "CCC": int(np.clip(np.random.normal(500, 40), 400, 560)),
    }[credit_grade]

    region = np.random.choice(REGIONS)
    education = np.random.choice(EDUCATION_LEVELS, p=EDUCATION_PROBS)
    marital_status = np.random.choice(
        ["single", "married", "divorced", "widowed"],
        p=[0.30, 0.45, 0.18, 0.07],
    )
    dependents = int(np.random.choice([0, 1, 2, 3, 4], p=[0.25, 0.25, 0.25, 0.15, 0.10]))
    employment_tenure_years = int(np.clip(np.random.exponential(8), 0, 40))
    existing_debt_ratio = round(np.clip(np.random.beta(2, 5), 0, 0.8), 3)

    borrowers_data.append({
        "borrower_id": borrower_id,
        "segment": segment,
        "age": age,
        "gender": np.random.choice(["M", "F"], p=[0.52, 0.48]),
        "marital_status": marital_status,
        "dependents": dependents,
        "education_level": education,
        "employment_type": employment_type,
        "employment_tenure_years": employment_tenure_years,
        "annual_income": annual_income,
        "existing_debt_ratio": existing_debt_ratio,
        "credit_score": credit_score,
        "credit_grade": credit_grade,
        "country": COUNTRY,
        "region": region,
        "industry_sector": industry_sector,
        "company_name": company_name,
        "years_in_business": years_in_business,
        "annual_revenue": annual_revenue,
        "onboarding_date": fake.date_between(
            start_date=date(2015, 1, 1),
            end_date=date(2025, 6, 30),
        ).isoformat(),
    })

borrowers_pdf = pd.DataFrame(borrowers_data)

def age_bucket(age):
    if age <= 25: return "18-25"
    if age <= 35: return "26-35"
    if age <= 45: return "36-45"
    if age <= 55: return "46-55"
    if age <= 65: return "56-65"
    return "65+"

borrowers_pdf["age_bucket"] = borrowers_pdf["age"].apply(age_bucket)

borrower_ids = borrowers_pdf["borrower_id"].tolist()
retail_borrower_ids = borrowers_pdf[borrowers_pdf["segment"] == "retail"]["borrower_id"].tolist()
commercial_borrower_ids = borrowers_pdf[borrowers_pdf["segment"] == "commercial"]["borrower_id"].tolist()
borrower_map = borrowers_pdf.set_index("borrower_id").to_dict("index")

print(f"  Generated {len(borrowers_pdf):,} borrowers")
print(f"  Segment: {borrowers_pdf['segment'].value_counts().to_dict()}")
print(f"  Credit grade: {borrowers_pdf['credit_grade'].value_counts().sort_index().to_dict()}")
print(f"  Region: {borrowers_pdf['region'].value_counts().to_dict()}")

# =============================================================================
# 2. LOAN TAPE
# =============================================================================
print("\n[2/7] Generating loan_tape...")

loans_data = []
loan_idx = 0

for product, cfg in PRODUCT_TYPES.items():
    n_product = int(N_LOANS * cfg["count_pct"])
    print(f"  Generating {n_product:,} {product} loans...")

    if cfg["borrower_segment"] == "commercial":
        eligible = commercial_borrower_ids
    else:
        eligible = retail_borrower_ids

    for _ in range(n_product):
        loan_idx += 1
        loan_id = f"LN-{loan_idx:06d}"
        borrower_id = np.random.choice(eligible)
        brw = borrower_map[borrower_id]

        is_revolving = product == "credit_card"

        if is_revolving:
            credit_limit = round(np.random.uniform(*cfg["principal_range"]), 2)
            utilization = round(np.clip(np.random.beta(2, 3), 0.05, 0.95), 3)
            principal = round(credit_limit * utilization, 2)
            term = 0
            origination_date = fake.date_between(
                start_date=REPORTING_DATE - timedelta(days=365 * 8),
                end_date=REPORTING_DATE - timedelta(days=90),
            )
            maturity_date = None
        else:
            credit_limit = None
            utilization = None
            term = int(np.random.uniform(cfg["term_months"][0], cfg["term_months"][1] + 1))
            origination_date = fake.date_between(
                start_date=REPORTING_DATE - timedelta(days=min(term * 30, 365 * 10)),
                end_date=REPORTING_DATE - timedelta(days=30),
            )
            maturity_date = origination_date + timedelta(days=term * 30)
            principal = round(np.random.uniform(*cfg["principal_range"]), 2)

        months_on_book = max(1, (REPORTING_DATE - origination_date).days // 30)
        remaining_months = max(0, (maturity_date - REPORTING_DATE).days // 30) if maturity_date else None
        vintage_year = origination_date.year

        eir = round(np.random.uniform(*cfg["eir_range"]), 4)

        if is_revolving:
            gross_carrying_amount = principal
        else:
            monthly_rate = eir / 12
            if term > 0 and monthly_rate > 0:
                monthly_payment = principal * monthly_rate / (1 - (1 + monthly_rate) ** (-term))
            else:
                monthly_payment = principal / max(term, 1)
            payments_made = min(months_on_book, term)
            outstanding = principal
            for _m in range(payments_made):
                interest_portion = outstanding * monthly_rate
                principal_portion = monthly_payment - interest_portion
                outstanding = max(0, outstanding - principal_portion)
            gross_carrying_amount = round(max(outstanding, 0), 2)

        grade = brw["credit_grade"]
        grade_mult = CREDIT_GRADE_PD_MULT[grade]
        base_pd = cfg["base_pd"] * grade_mult
        origination_pd = round(np.clip(base_pd + np.random.normal(0, base_pd * 0.15), 0.001, 0.50), 5)

        dpd_prob = origination_pd * 2.0
        if np.random.random() < dpd_prob:
            r = np.random.random()
            if r < 0.50:
                days_past_due = int(np.random.uniform(1, 30))
            elif r < 0.75:
                days_past_due = int(np.random.uniform(30, 90))
            elif r < 0.90:
                days_past_due = int(np.random.uniform(90, 180))
            else:
                days_past_due = int(np.random.uniform(180, 365))
        else:
            days_past_due = 0

        dpd_factor = 1.0 + (days_past_due / 120) ** 1.3
        aging_factor = 1.0 + months_on_book * 0.002
        current_pd = round(np.clip(origination_pd * dpd_factor * aging_factor, 0.001, 0.95), 5)

        if days_past_due >= 90:
            current_stage = 3
        elif days_past_due >= 30 or current_pd / max(origination_pd, 0.001) > 2.5:
            current_stage = 2
        else:
            current_stage = 1

        if current_stage == 1:
            prior_stage = np.random.choice([1, 2], p=[0.95, 0.05])
        elif current_stage == 2:
            prior_stage = np.random.choice([1, 2, 3], p=[0.35, 0.55, 0.10])
        else:
            prior_stage = np.random.choice([2, 3], p=[0.30, 0.70])

        is_restructured = days_past_due > 60 and np.random.random() < 0.12
        if is_restructured and current_stage < 2:
            current_stage = 2

        is_write_off = days_past_due >= 180 and np.random.random() < 0.55

        if days_past_due == 0:
            delinquency_bucket = "Current"
        elif days_past_due <= 30:
            delinquency_bucket = "1-30 DPD"
        elif days_past_due <= 60:
            delinquency_bucket = "31-60 DPD"
        elif days_past_due <= 90:
            delinquency_bucket = "61-90 DPD"
        else:
            delinquency_bucket = "90+ DPD"

        risk_band = grade  # use credit grade as risk band

        if cfg["secured"] and cfg["collateral_type"] == "residential_property":
            ltv = round(np.clip(gross_carrying_amount / (principal * np.random.uniform(1.0, 1.8)), 0.2, 1.3), 3)
        elif cfg["secured"] and cfg["collateral_type"] == "vehicle":
            depreciation = 1.0 - months_on_book * 0.012
            ltv = round(np.clip(gross_carrying_amount / (principal * max(depreciation, 0.3)), 0.3, 1.5), 3)
        elif cfg["secured"] and cfg["collateral_type"] == "commercial_property":
            ltv = round(np.clip(gross_carrying_amount / (principal * np.random.uniform(1.1, 2.0)), 0.2, 1.2), 3)
        else:
            ltv = None

        if ltv is not None:
            if ltv < 0.60:
                ltv_band = "< 60%"
            elif ltv < 0.80:
                ltv_band = "60-80%"
            elif ltv <= 1.0:
                ltv_band = "80-100%"
            else:
                ltv_band = "> 100%"
        else:
            ltv_band = None

        industry = brw["industry_sector"] if brw["segment"] == "commercial" else None

        loans_data.append({
            "loan_id": loan_id,
            "borrower_id": borrower_id,
            "product_type": product,
            "origination_date": origination_date.isoformat(),
            "maturity_date": maturity_date.isoformat() if maturity_date else None,
            "original_principal": principal,
            "gross_carrying_amount": gross_carrying_amount,
            "credit_limit": credit_limit,
            "utilization_rate": utilization,
            "effective_interest_rate": eir,
            "contractual_term_months": term,
            "months_on_book": months_on_book,
            "remaining_months": remaining_months,
            "days_past_due": days_past_due,
            "delinquency_bucket": delinquency_bucket,
            "origination_pd": origination_pd,
            "current_lifetime_pd": current_pd,
            "current_stage": current_stage,
            "prior_stage": prior_stage,
            "assessed_stage": current_stage,
            "credit_grade": grade,
            "risk_band": risk_band,
            "vintage_year": vintage_year,
            "age_bucket": brw["age_bucket"],
            "employment_type": brw["employment_type"],
            "region": brw["region"],
            "industry_sector": industry,
            "ltv_ratio": ltv,
            "ltv_band": ltv_band,
            "is_restructured": is_restructured,
            "is_write_off": is_write_off,
            "currency": CURRENCY,
            "reporting_date": REPORTING_DATE.isoformat(),
        })

loans_pdf = pd.DataFrame(loans_data)

loan_ids = loans_pdf["loan_id"].tolist()
loan_product_map = dict(zip(loans_pdf["loan_id"], loans_pdf["product_type"]))
loan_borrower_map = dict(zip(loans_pdf["loan_id"], loans_pdf["borrower_id"]))
loan_gca_map = dict(zip(loans_pdf["loan_id"], loans_pdf["gross_carrying_amount"]))

print(f"  Generated {len(loans_pdf):,} loans")
print(f"  Product distribution:\n{loans_pdf['product_type'].value_counts().to_string()}")
print(f"  Stage distribution:\n{loans_pdf['assessed_stage'].value_counts().sort_index().to_string()}")
print(f"  Total GCA: ${loans_pdf['gross_carrying_amount'].sum():,.0f}")
print(f"  Credit grades: {loans_pdf['credit_grade'].value_counts().sort_index().to_dict()}")
print(f"  Delinquency: {loans_pdf['delinquency_bucket'].value_counts().to_dict()}")
print(f"  Regions: {loans_pdf['region'].value_counts().to_dict()}")

# =============================================================================
# 3. PAYMENT HISTORY (24 months)
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

    if dpd == 0:
        late_prob = 0.04
    elif dpd < 30:
        late_prob = 0.20
    elif dpd < 90:
        late_prob = 0.45
    else:
        late_prob = 0.75

    if loan["product_type"] == "credit_card":
        monthly_amt = loan["gross_carrying_amount"] * 0.03  # min payment
    else:
        monthly_amt = loan["original_principal"] / max(loan["contractual_term_months"], 1)

    for m in range(n_payments):
        pay_date = start + timedelta(days=30 * (m + 1))
        if pay_date > REPORTING_DATE:
            break

        amount_due = round(monthly_amt, 2)

        if np.random.random() < late_prob:
            days_late = int(np.random.exponential(15)) + 1
            if np.random.random() < 0.08:
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
            ["bank_transfer", "direct_debit", "online_banking", "check", "auto_pay"],
            p=[0.25, 0.30, 0.20, 0.05, 0.20],
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
print(f"  Status: {payments_pdf['payment_status'].value_counts().to_dict()}")

# =============================================================================
# 4. GENERAL LEDGER
# =============================================================================
print("\n[4/7] Generating general_ledger...")

product_gca = loans_pdf.groupby("product_type")["gross_carrying_amount"].sum()
gl_data = []

for idx, (product, total) in enumerate(product_gca.items()):
    variance = round(np.random.uniform(-0.002, 0.002) * total, 2)
    if product == "credit_card":
        variance = round(total * 0.0015, 2)

    gl_data.append({
        "account_code": f"1{idx+1}00",
        "account_name": f"Loans Receivable - {product.replace('_', ' ').title()}",
        "account_type": "asset",
        "gl_balance": round(total + variance, 2),
        "loan_tape_balance": round(total, 2),
        "variance": round(variance, 2),
        "as_of_date": REPORTING_DATE.isoformat(),
        "currency": CURRENCY,
    })
    gl_data.append({
        "account_code": f"2{idx+1}00",
        "account_name": f"ECL Allowance - {product.replace('_', ' ').title()}",
        "account_type": "contra_asset",
        "gl_balance": round(-total * np.random.uniform(0.01, 0.08), 2),
        "loan_tape_balance": None,
        "variance": None,
        "as_of_date": REPORTING_DATE.isoformat(),
        "currency": CURRENCY,
    })

gl_data.append({
    "account_code": "3100",
    "account_name": "Interest Receivable - All Products",
    "account_type": "asset",
    "gl_balance": round(loans_pdf["gross_carrying_amount"].sum() * 0.006, 2),
    "loan_tape_balance": None,
    "variance": None,
    "as_of_date": REPORTING_DATE.isoformat(),
    "currency": CURRENCY,
})

gl_pdf = pd.DataFrame(gl_data)
print(f"  Generated {len(gl_pdf):,} GL entries")

# =============================================================================
# 5. MACROECONOMIC SCENARIOS
# =============================================================================
print("\n[5/7] Generating macro_scenarios...")

scenarios = {
    "baseline": {
        "weight": 0.40, "description": "Current trajectory continues",
        "unemployment_adj": 0, "gdp_adj": 0, "inflation_adj": 0,
    },
    "upside": {
        "weight": 0.10, "description": "Strong recovery with falling unemployment",
        "unemployment_adj": -1.2, "gdp_adj": 1.0, "inflation_adj": -0.3,
    },
    "mild_downturn": {
        "weight": 0.20, "description": "Modest slowdown with rising delinquencies",
        "unemployment_adj": 1.5, "gdp_adj": -0.8, "inflation_adj": 0.5,
    },
    "adverse": {
        "weight": 0.15, "description": "Recession with significant job losses",
        "unemployment_adj": 3.5, "gdp_adj": -2.0, "inflation_adj": 1.5,
    },
    "severely_adverse": {
        "weight": 0.10, "description": "Deep recession, housing crash, credit freeze",
        "unemployment_adj": 6.0, "gdp_adj": -4.0, "inflation_adj": 2.5,
    },
    "stagflation": {
        "weight": 0.05, "description": "High inflation + stagnant growth",
        "unemployment_adj": 2.5, "gdp_adj": -1.0, "inflation_adj": 4.0,
    },
}

macro_data = []
for scenario_name, params in scenarios.items():
    for q in range(12):
        quarter_date = REPORTING_DATE + timedelta(days=90 * (q + 1))
        quarter_label = f"Q{((quarter_date.month - 1) // 3) + 1}-{quarter_date.year}"

        if q <= 2:
            shock_factor = 0.7 + q * 0.1
        elif q <= 4:
            shock_factor = 1.0
        else:
            shock_factor = max(0.1, 1.0 - (q - 4) * 0.12)

        base_unemployment = 4.2 + np.random.normal(0, 0.1)
        base_gdp = 2.3 + np.random.normal(0, 0.15)
        base_inflation = 2.8 + np.random.normal(0, 0.1)
        base_interest_rate = 5.0 + np.random.normal(0, 0.1)
        base_hpi = 105 + np.random.normal(0, 1.5)  # house price index
        base_consumer_confidence = 100 + np.random.normal(0, 2)

        rate_adj = params["inflation_adj"] * 0.4 - min(params["gdp_adj"], 0) * 0.15
        hpi_adj = params["gdp_adj"] * 3 - params["unemployment_adj"] * 2

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
            "house_price_index": round(base_hpi + hpi_adj * shock_factor, 1),
            "consumer_confidence_index": round(base_consumer_confidence - params["unemployment_adj"] * 5 * shock_factor, 1),
            "reporting_date": REPORTING_DATE.isoformat(),
        })

macro_pdf = pd.DataFrame(macro_data)
print(f"  Generated {len(macro_pdf):,} macro records ({len(scenarios)} scenarios x 12 quarters)")

# =============================================================================
# 6. COLLATERAL REGISTER (secured products)
# =============================================================================
print("\n[6/7] Generating collateral_register...")

secured_loans = loans_pdf[loans_pdf["product_type"].isin(
    [p for p, c in PRODUCT_TYPES.items() if c.get("secured", False)]
)]
collateral_data = []

for _, loan in secured_loans.iterrows():
    product = loan["product_type"]
    coll_type = PRODUCT_TYPES[product]["collateral_type"]

    if coll_type == "residential_property":
        original_value = round(loan["original_principal"] / np.random.uniform(0.6, 0.85), 2)
        appreciation = np.random.uniform(-0.05, 0.15)
        current_value = round(original_value * (1 + appreciation), 2)
    elif coll_type == "vehicle":
        original_value = round(loan["original_principal"] / np.random.uniform(0.75, 0.95), 2)
        months = loan["months_on_book"]
        depreciation = 1.0 - months * 0.012
        current_value = round(original_value * max(depreciation, 0.25), 2)
    elif coll_type == "commercial_property":
        original_value = round(loan["original_principal"] / np.random.uniform(0.5, 0.75), 2)
        appreciation = np.random.uniform(-0.10, 0.12)
        current_value = round(original_value * (1 + appreciation), 2)
    else:
        original_value = round(loan["original_principal"], 2)
        current_value = original_value

    ltv = round(loan["gross_carrying_amount"] / max(current_value, 1), 4)

    collateral_data.append({
        "loan_id": loan["loan_id"],
        "collateral_type": coll_type,
        "original_collateral_value": original_value,
        "current_collateral_value": current_value,
        "loan_to_value_ratio": ltv,
        "last_valuation_date": (REPORTING_DATE - timedelta(days=np.random.randint(0, 90))).isoformat(),
        "collateral_status": "impaired" if current_value < loan["gross_carrying_amount"] * 0.8 else "adequate",
        "reporting_date": REPORTING_DATE.isoformat(),
    })

_COLL_COLS = ["loan_id", "collateral_type", "original_collateral_value",
              "current_collateral_value", "loan_to_value_ratio",
              "last_valuation_date", "collateral_status", "reporting_date"]
collateral_pdf = pd.DataFrame(collateral_data, columns=_COLL_COLS) if collateral_data else pd.DataFrame(columns=_COLL_COLS)
print(f"  Generated {len(collateral_pdf):,} collateral records")

# =============================================================================
# 7. HISTORICAL DEFAULTS (5 years, macro-correlated)
# =============================================================================
print("\n[7/7] Generating historical_defaults (macro-correlated)...")

HIST_QUARTERS = []
hist_start = date(2021, 1, 1)
for q in range(20):
    q_date = hist_start + timedelta(days=90 * q)
    q_label = f"Q{((q_date.month - 1) // 3) + 1}-{q_date.year}"
    HIST_QUARTERS.append({"quarter": q_label, "quarter_date": q_date})

hist_macro = pd.DataFrame({
    "quarter": [q["quarter"] for q in HIST_QUARTERS],
    "quarter_date": [q["quarter_date"] for q in HIST_QUARTERS],
    "unemployment_rate": [
        8.5, 7.8, 6.9, 6.2,   # 2021: COVID recovery
        5.5, 5.0, 4.7, 4.5,   # 2022: normalization
        4.3, 4.2, 4.1, 4.0,   # 2023: stable
        4.1, 4.3, 4.5, 4.3,   # 2024: mild uptick
        4.2, 4.1, 4.2, 4.2,   # 2025: stable
    ],
    "gdp_growth_rate": [
        -2.5, 2.0, 5.5, 6.5,  # 2021: rebound
        3.5, 3.0, 2.6, 2.4,   # 2022: slowing
        2.2, 2.3, 2.5, 2.6,   # 2023: stable
        2.3, 2.0, 1.8, 2.1,   # 2024: mild dip
        2.3, 2.4, 2.2, 2.3,   # 2025: stable
    ],
    "inflation_rate": [
        3.5, 3.8, 4.2, 4.8,   # 2021: rising
        5.5, 6.5, 7.0, 6.5,   # 2022: peak
        5.5, 4.5, 3.8, 3.2,   # 2023: normalizing
        3.0, 2.9, 3.1, 2.8,   # 2024: stable
        2.8, 2.7, 2.9, 2.8,   # 2025: stable
    ],
    "house_price_index": [
        95, 97, 100, 103,      # 2021: recovery
        106, 108, 107, 105,    # 2022: peak then cool
        104, 103, 104, 105,    # 2023: stable
        105, 104, 103, 104,    # 2024: flat
        105, 106, 105, 105,    # 2025: stable
    ],
})

def _derive_coefficients(product_types):
    coeffs = {}
    for name, cfg in product_types.items():
        bp = cfg.get("base_pd", 0.04)
        coeffs[name] = {
            "base_dr": bp,
            "beta_unemp": round(bp * 0.18, 6),
            "beta_gdp": round(-bp * 0.12, 6),
            "beta_infl": round(bp * 0.05, 6),
        }
    return coeffs

TRUE_COEFFICIENTS = _derive_coefficients(PRODUCT_TYPES)

GRADE_MODIFIERS = {
    "AAA": 0.15, "AA": 0.30, "A": 0.55, "BBB": 0.85,
    "BB": 1.30, "B": 2.00, "CCC": 3.50,
}
AGE_MODIFIERS = {
    "18-25": 1.25, "26-35": 1.05, "36-45": 0.85,
    "46-55": 0.90, "56-65": 0.95, "65+": 1.10,
}
EMPLOYMENT_MODIFIERS = {
    "salaried": 0.80, "self_employed": 1.15, "business_owner": 1.10,
    "retired": 0.90, "contract": 1.20,
}
REGION_MODIFIERS = {
    "Northeast": 0.90, "Southeast": 1.10, "Midwest": 0.95,
    "Southwest": 1.05, "West Coast": 0.85, "Pacific Northwest": 0.88,
    "Mountain": 1.00, "Mid-Atlantic": 0.92,
}

cohort_combos = []
for product in PRODUCT_TYPES:
    for grade in ["A", "BBB", "BB", "B"]:
        cohort_combos.append((product, grade))

def _derive_lgd_coefficients(product_types):
    coeffs = {}
    for name, cfg in product_types.items():
        if cfg.get("secured", False):
            if cfg.get("collateral_type") == "residential_property":
                base_lgd = 0.15
            elif cfg.get("collateral_type") == "vehicle":
                base_lgd = 0.35
            else:
                base_lgd = 0.25
        else:
            bp = cfg.get("base_pd", 0.04)
            base_lgd = min(0.75, 0.30 + bp * 4)
        coeffs[name] = {
            "base_lgd": round(base_lgd, 4),
            "beta_unemp": round(base_lgd * 0.06, 4),
            "beta_gdp": round(-base_lgd * 0.05, 4),
            "beta_infl": round(base_lgd * 0.02, 4),
        }
    return coeffs

TRUE_LGD_COEFFICIENTS = _derive_lgd_coefficients(PRODUCT_TYPES)

PORTFOLIO_SIZE = {}
for _pname, _pcfg in PRODUCT_TYPES.items():
    PORTFOLIO_SIZE[_pname] = max(500, int(N_LOANS * _pcfg["count_pct"] * 0.85))

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
        expected_dr = (coeff["base_dr"]
                       + coeff["beta_unemp"] * unemp
                       + coeff["beta_gdp"] * gdp
                       + coeff["beta_infl"] * infl)
        noise = np.random.normal(0, 0.002)
        actual_dr = np.clip(expected_dr + noise, 0.002, 0.25)

        quarterly_default_rates.append({
            "quarter": q_label, "quarter_date": q_date,
            "product_type": product, "cohort_id": "__ALL__",
            "unemployment_rate": unemp, "gdp_growth_rate": gdp, "inflation_rate": infl,
            "expected_default_rate": round(expected_dr, 6),
            "observed_default_rate": round(actual_dr, 6),
            "portfolio_size": PORTFOLIO_SIZE[product],
        })

        for combo_product, combo_grade in cohort_combos:
            if combo_product != product:
                continue
            mod = GRADE_MODIFIERS.get(combo_grade, 1.0)
            c_expected = expected_dr * mod
            c_noise = np.random.normal(0, 0.003)
            c_actual = np.clip(c_expected + c_noise, 0.002, 0.30)
            c_size = max(50, int(PORTFOLIO_SIZE[product] / 7))
            quarterly_default_rates.append({
                "quarter": q_label, "quarter_date": q_date,
                "product_type": product, "cohort_id": combo_grade,
                "unemployment_rate": unemp, "gdp_growth_rate": gdp, "inflation_rate": infl,
                "expected_default_rate": round(c_expected, 6),
                "observed_default_rate": round(c_actual, 6),
                "portfolio_size": c_size,
            })

        n_defaults = int(PORTFOLIO_SIZE[product] * actual_dr / 4)
        lgd_coeff = TRUE_LGD_COEFFICIENTS[product]
        expected_lgd = np.clip(
            lgd_coeff["base_lgd"]
            + lgd_coeff["beta_unemp"] * unemp
            + lgd_coeff["beta_gdp"] * gdp
            + lgd_coeff["beta_infl"] * infl,
            0.05, 0.95,
        )

        for _ in range(n_defaults):
            def_counter += 1
            default_date = q_date + timedelta(days=int(np.random.uniform(0, 89)))
            if default_date > REPORTING_DATE:
                continue

            pr = PRODUCT_TYPES.get(product, {}).get("principal_range", (5000, 50000))
            exposure = round(np.random.uniform(pr[0] * 0.3, pr[1] * 0.8), 2)

            loan_lgd = np.clip(expected_lgd + np.random.normal(0, 0.08), 0.02, 0.98)
            recovery_rate = 1.0 - loan_lgd
            recovery_amount = round(exposure * recovery_rate, 2)
            loss_amount = round(exposure - recovery_amount, 2)
            recovery_lag_days = int(np.random.exponential(120)) + 30
            recovery_date = default_date + timedelta(days=recovery_lag_days)

            defaults_data.append({
                "default_id": f"DEF-{def_counter:06d}",
                "product_type": product,
                "credit_grade": np.random.choice(CREDIT_GRADES, p=[0.01, 0.02, 0.05, 0.12, 0.25, 0.30, 0.25]),
                "region": np.random.choice(REGIONS),
                "default_date": default_date.isoformat(),
                "quarter": q_label,
                "exposure_at_default": exposure,
                "recovery_amount": recovery_amount,
                "recovery_date": recovery_date.isoformat() if recovery_date <= REPORTING_DATE else None,
                "loss_amount": loss_amount,
                "loss_given_default": round(loan_lgd, 4),
                "default_reason": np.random.choice(
                    ["income_loss", "over_indebtedness", "business_failure", "health_emergency",
                     "employer_closure", "fraud", "voluntary_default", "divorce"],
                    p=[0.25, 0.20, 0.15, 0.12, 0.10, 0.05, 0.08, 0.05],
                ),
                "was_restructured_before_default": np.random.random() < 0.18,
                "months_to_default": int(np.random.exponential(10)) + 1,
            })

defaults_pdf = pd.DataFrame(defaults_data)
quarterly_dr_pdf = pd.DataFrame(quarterly_default_rates)

print(f"  Generated {len(defaults_pdf):,} historical defaults")
print(f"  Generated {len(quarterly_dr_pdf):,} quarterly default rate observations")
if not defaults_pdf.empty:
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
    if pdf.empty:
        from pyspark.sql.types import StructType, StructField, StringType
        if len(pdf.columns) > 0:
            schema = StructType([StructField(c, StringType(), True) for c in pdf.columns])
            sdf = spark.createDataFrame([], schema)
        else:
            print(f"    -> SKIPPED (no columns)")
            continue
    else:
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
    SELECT assessed_stage, COUNT(*) as cnt,
           ROUND(SUM(gross_carrying_amount), 2) as total_gca
    FROM {FULL_SCHEMA}.loan_tape
    GROUP BY assessed_stage ORDER BY assessed_stage
""").collect()

print("\n  Stage Distribution:")
for row in stage_dist:
    print(f"    Stage {row['assessed_stage']}: {row['cnt']:,} loans, ${row['total_gca']:,.2f}")

product_dist = spark.sql(f"""
    SELECT product_type, COUNT(*) as cnt,
           ROUND(SUM(gross_carrying_amount), 2) as total_gca
    FROM {FULL_SCHEMA}.loan_tape
    GROUP BY product_type ORDER BY total_gca DESC
""").collect()

print("\n  Product Distribution:")
for row in product_dist:
    print(f"    {row['product_type']}: {row['cnt']:,} loans, ${row['total_gca']:,.2f}")

print("\n✅ Data generation complete!")

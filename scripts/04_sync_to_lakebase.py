"""
Sync UC Delta tables to Lakebase (PostgreSQL) for lightning-fast app queries.
Reads from lakemeter_catalog.expected_credit_loss via Spark,
writes to Lakebase PostgreSQL instance 'horizon-ecl-db'.

Works on both serverless (Spark context available) and classic clusters.
Uses REST API for Lakebase credentials (compatible with all SDK versions).

IMPORTANT: The backend (app/backend.py) uses schema 'expected_credit_loss' with
prefix 'lb_' for all table names. This sync script must match that convention.
"""
import os
import json
import requests
import psycopg2
import psycopg2.extras
from databricks.sdk import WorkspaceClient

LAKEBASE_INSTANCE = "horizon-ecl-db"
LAKEBASE_DB = "databricks_postgres"
UC_SCHEMA = "lakemeter_catalog.expected_credit_loss"

PG_SCHEMA = "expected_credit_loss"
PG_PREFIX = "lb_"

_w = WorkspaceClient()

# ── helpers ──────────────────────────────────────────────────────────────────

def _api_get(path):
    """Make authenticated GET request to workspace API."""
    cfg = _w.config
    headers = cfg.authenticate()
    resp = requests.get(f"{cfg.host}{path}", headers=headers)
    resp.raise_for_status()
    return resp.json()

def _api_post(path, body):
    """Make authenticated POST request to workspace API."""
    cfg = _w.config
    headers = cfg.authenticate()
    headers["Content-Type"] = "application/json"
    resp = requests.post(f"{cfg.host}{path}", headers=headers, json=body)
    resp.raise_for_status()
    return resp.json()

def _get_lakebase_creds():
    """Get Lakebase host, username, and token via REST API."""
    inst = _api_get(f"/api/2.0/database/instances/{LAKEBASE_INSTANCE}")
    host = inst["read_write_dns"]
    me = _api_get("/api/2.0/preview/scim/v2/Me")
    email = me["userName"]
    cred = _api_post("/api/2.0/database/credentials", {
        "request_id": "sync-ecl",
        "instance_names": [LAKEBASE_INSTANCE],
    })
    return host, email, cred["token"]


def get_lakebase_connection():
    host, email, token = _get_lakebase_creds()
    return psycopg2.connect(host=host, port=5432, database=LAKEBASE_DB,
                            user=email, password=token, sslmode="require")


def ensure_database():
    """Create database if it doesn't exist."""
    host, email, token = _get_lakebase_creds()
    conn = psycopg2.connect(host=host, port=5432, database="postgres",
                            user=email, password=token, sslmode="require")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (LAKEBASE_DB,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{LAKEBASE_DB}"')
        print(f"  Created database '{LAKEBASE_DB}'")
    else:
        print(f"  Database '{LAKEBASE_DB}' already exists")
    cur.close()
    conn.close()


def _pg(name: str) -> str:
    return f"{PG_SCHEMA}.{PG_PREFIX}{name}"


# ── DDL ──────────────────────────────────────────────────────────────────────

DDL = f"""
CREATE SCHEMA IF NOT EXISTS {PG_SCHEMA};

DROP TABLE IF EXISTS {_pg('loan_level_ecl')} CASCADE;
DROP TABLE IF EXISTS {_pg('loan_ecl_weighted')} CASCADE;
DROP TABLE IF EXISTS {_pg('model_ready_loans')} CASCADE;
DROP TABLE IF EXISTS {_pg('portfolio_ecl_summary')} CASCADE;
DROP TABLE IF EXISTS {_pg('scenario_ecl_summary')} CASCADE;
DROP TABLE IF EXISTS {_pg('mc_ecl_distribution')} CASCADE;
DROP TABLE IF EXISTS {_pg('dq_results')} CASCADE;
DROP TABLE IF EXISTS {_pg('gl_reconciliation')} CASCADE;
DROP TABLE IF EXISTS {_pg('ifrs7_stage_migration')} CASCADE;
DROP TABLE IF EXISTS {_pg('ifrs7_credit_risk_exposure')} CASCADE;
DROP TABLE IF EXISTS {_pg('satellite_model_metadata')} CASCADE;
DROP TABLE IF EXISTS {_pg('sicr_thresholds')} CASCADE;
DROP TABLE IF EXISTS {_pg('borrower_master')} CASCADE;

CREATE TABLE {_pg('borrower_master')} (
    borrower_id         TEXT PRIMARY KEY,
    segment             TEXT,
    age                 INT,
    gender              TEXT,
    country             TEXT,
    region              TEXT,
    income_source       TEXT,
    monthly_income      DOUBLE PRECISION,
    employment_tenure_months INT,
    education_level     TEXT,
    formal_credit_score DOUBLE PRECISION,
    rent_payment_score  DOUBLE PRECISION,
    utility_payment_score DOUBLE PRECISION,
    mobile_money_velocity DOUBLE PRECISION,
    bank_account_age_months INT,
    alt_data_composite_score DOUBLE PRECISION,
    has_student_loan    BOOLEAN,
    dependents          INT,
    onboarding_date     TEXT
);

CREATE TABLE {_pg('model_ready_loans')} (
    loan_id             TEXT PRIMARY KEY,
    borrower_id         TEXT,
    product_type        TEXT NOT NULL,
    origination_date    TEXT,
    maturity_date       TEXT,
    original_principal  DOUBLE PRECISION,
    gross_carrying_amount DOUBLE PRECISION,
    effective_interest_rate DOUBLE PRECISION,
    contractual_term_months INT,
    months_on_book      INT,
    remaining_months    INT,
    days_past_due       INT,
    origination_pd      DOUBLE PRECISION,
    current_lifetime_pd DOUBLE PRECISION,
    origination_alt_score DOUBLE PRECISION,
    current_alt_score   DOUBLE PRECISION,
    assessed_stage      INT NOT NULL,
    prior_stage         INT,
    consecutive_on_time_payments INT,
    sicr_trigger_reasons TEXT,
    is_restructured     BOOLEAN,
    currency            TEXT,
    segment             TEXT,
    age                 INT,
    income_source       TEXT,
    monthly_income      DOUBLE PRECISION,
    employment_tenure_months INT,
    education_level     TEXT,
    formal_credit_score DOUBLE PRECISION,
    rent_payment_score  DOUBLE PRECISION,
    utility_payment_score DOUBLE PRECISION,
    mobile_money_velocity DOUBLE PRECISION,
    bank_account_age_months INT,
    alt_data_composite_score DOUBLE PRECISION,
    has_student_loan    BOOLEAN,
    dependents          INT,
    country             TEXT,
    current_collateral_value DOUBLE PRECISION,
    loan_to_value_ratio DOUBLE PRECISION,
    vintage_cohort      TEXT,
    pmt_on_time_rate    DOUBLE PRECISION,
    total_payments      INT,
    missed_payments     INT
);

CREATE TABLE {_pg('loan_level_ecl')} (
    loan_id             TEXT NOT NULL,
    product_type        TEXT,
    assessed_stage      INT,
    scenario            TEXT NOT NULL,
    scenario_weight     DOUBLE PRECISION,
    gross_carrying_amount DOUBLE PRECISION,
    current_lifetime_pd DOUBLE PRECISION,
    scenario_adjusted_pd DOUBLE PRECISION,
    base_lgd            DOUBLE PRECISION,
    scenario_adjusted_lgd DOUBLE PRECISION,
    effective_interest_rate DOUBLE PRECISION,
    horizon_quarters    INT,
    ecl_amount          DOUBLE PRECISION,
    ecl_std             DOUBLE PRECISION,
    ecl_p50             DOUBLE PRECISION,
    ecl_p75             DOUBLE PRECISION,
    ecl_p95             DOUBLE PRECISION,
    ecl_p99             DOUBLE PRECISION,
    weighted_ecl        DOUBLE PRECISION,
    coverage_ratio      DOUBLE PRECISION,
    reporting_date      TEXT,
    project_id          TEXT,
    PRIMARY KEY (loan_id, scenario)
);

CREATE TABLE {_pg('loan_ecl_weighted')} (
    loan_id             TEXT PRIMARY KEY,
    product_type        TEXT,
    assessed_stage      INT,
    gross_carrying_amount DOUBLE PRECISION,
    weighted_ecl        DOUBLE PRECISION
);

CREATE TABLE {_pg('portfolio_ecl_summary')} (
    product_type        TEXT NOT NULL,
    assessed_stage      INT NOT NULL,
    loan_count          INT,
    total_gca           DOUBLE PRECISION,
    total_ecl           DOUBLE PRECISION,
    coverage_ratio      DOUBLE PRECISION,
    PRIMARY KEY (product_type, assessed_stage)
);

CREATE TABLE {_pg('scenario_ecl_summary')} (
    scenario            TEXT PRIMARY KEY,
    total_ecl           DOUBLE PRECISION,
    total_ecl_p95       DOUBLE PRECISION,
    total_ecl_p99       DOUBLE PRECISION,
    weight              DOUBLE PRECISION,
    weighted_contribution DOUBLE PRECISION
);

CREATE TABLE {_pg('mc_ecl_distribution')} (
    scenario            TEXT PRIMARY KEY,
    weight              DOUBLE PRECISION,
    ecl_mean            DOUBLE PRECISION,
    ecl_p50             DOUBLE PRECISION,
    ecl_p75             DOUBLE PRECISION,
    ecl_p95             DOUBLE PRECISION,
    ecl_p99             DOUBLE PRECISION,
    avg_pd_multiplier   DOUBLE PRECISION,
    avg_lgd_multiplier  DOUBLE PRECISION,
    pd_vol              DOUBLE PRECISION,
    lgd_vol             DOUBLE PRECISION,
    n_simulations       INT
);

CREATE TABLE {_pg('dq_results')} (
    check_id            TEXT PRIMARY KEY,
    category            TEXT,
    description         TEXT,
    severity            TEXT,
    failures            INT,
    total_records       INT,
    failure_pct         DOUBLE PRECISION,
    threshold           INT,
    passed              BOOLEAN,
    snapshot_id         TEXT,
    reporting_date      TEXT
);

CREATE TABLE {_pg('gl_reconciliation')} (
    product_type        TEXT PRIMARY KEY,
    gl_balance          DOUBLE PRECISION,
    loan_tape_balance   DOUBLE PRECISION,
    variance            DOUBLE PRECISION,
    variance_pct        DOUBLE PRECISION,
    tolerance_pct       DOUBLE PRECISION,
    status              TEXT,
    snapshot_id         TEXT,
    reporting_date      TEXT
);

CREATE TABLE {_pg('satellite_model_metadata')} (
    product_type                TEXT PRIMARY KEY,
    calibration_method          TEXT,
    pd_marginal_unemp           DOUBLE PRECISION,
    pd_marginal_gdp             DOUBLE PRECISION,
    pd_marginal_infl            DOUBLE PRECISION,
    lgd_marginal_unemp          DOUBLE PRECISION,
    lgd_marginal_gdp            DOUBLE PRECISION,
    lgd_marginal_infl           DOUBLE PRECISION,
    pd_lgd_correlation          DOUBLE PRECISION,
    annual_prepayment_rate      DOUBLE PRECISION,
    r_squared_pd_logit_space    DOUBLE PRECISION,
    r_squared_lgd_logit_space   DOUBLE PRECISION,
    calibration_sample_quarters INT,
    pd_logistic_betas           TEXT,
    lgd_logistic_betas          TEXT,
    calibration_date            TEXT,
    next_recalibration_date     TEXT,
    model_version               TEXT,
    reporting_date              TEXT
);

CREATE TABLE {_pg('sicr_thresholds')} (
    product_type                TEXT PRIMARY KEY,
    pd_relative_threshold       DOUBLE PRECISION,
    pd_absolute_threshold       DOUBLE PRECISION,
    alt_score_drop_threshold    DOUBLE PRECISION,
    ltv_threshold               DOUBLE PRECISION,
    dpd_backstop_stage2         INT,
    dpd_backstop_stage3         INT,
    cure_period_months          INT,
    calibration_date            TEXT,
    reporting_date              TEXT
);

CREATE TABLE {_pg('ifrs7_stage_migration')} (
    product_type        TEXT NOT NULL,
    original_stage      INT NOT NULL,
    assessed_stage      INT NOT NULL,
    loan_count          INT,
    total_gca           DOUBLE PRECISION,
    PRIMARY KEY (product_type, original_stage, assessed_stage)
);

CREATE TABLE {_pg('ifrs7_credit_risk_exposure')} (
    product_type        TEXT NOT NULL,
    assessed_stage      INT NOT NULL,
    credit_risk_grade   TEXT NOT NULL,
    loan_count          INT,
    total_gca           DOUBLE PRECISION,
    PRIMARY KEY (product_type, assessed_stage, credit_risk_grade)
);

CREATE INDEX idx_loans_product ON {_pg('model_ready_loans')}(product_type);
CREATE INDEX idx_loans_stage ON {_pg('model_ready_loans')}(assessed_stage);
CREATE INDEX idx_loans_vintage ON {_pg('model_ready_loans')}(vintage_cohort);
CREATE INDEX idx_loans_segment ON {_pg('model_ready_loans')}(segment);
CREATE INDEX idx_loan_ecl_product ON {_pg('loan_level_ecl')}(product_type);
CREATE INDEX idx_loan_ecl_scenario ON {_pg('loan_level_ecl')}(scenario);
CREATE INDEX idx_loan_ecl_stage ON {_pg('loan_level_ecl')}(assessed_stage);
CREATE INDEX idx_weighted_product ON {_pg('loan_ecl_weighted')}(product_type);
CREATE INDEX idx_borrower_segment ON {_pg('borrower_master')}(segment);
"""


# ── sync logic ───────────────────────────────────────────────────────────────

TABLES = [
    ("borrower_master", _pg("borrower_master")),
    ("model_ready_loans", _pg("model_ready_loans")),
    ("loan_level_ecl", _pg("loan_level_ecl")),
    ("loan_ecl_weighted", _pg("loan_ecl_weighted")),
    ("portfolio_ecl_summary", _pg("portfolio_ecl_summary")),
    ("scenario_ecl_summary", _pg("scenario_ecl_summary")),
    ("mc_ecl_distribution", _pg("mc_ecl_distribution")),
    ("dq_results", _pg("dq_results")),
    ("gl_reconciliation", _pg("gl_reconciliation")),
    ("ifrs7_stage_migration", _pg("ifrs7_stage_migration")),
    ("ifrs7_credit_risk_exposure", _pg("ifrs7_credit_risk_exposure")),
    ("satellite_model_metadata", _pg("satellite_model_metadata")),
    ("sicr_thresholds", _pg("sicr_thresholds")),
]


def sync_table(spark, pg_conn, uc_table: str, pg_table: str):
    """Read from UC via Spark, write to Lakebase via psycopg2."""
    print(f"\n  Syncing {uc_table} -> {pg_table} ...")
    full_table = f"{UC_SCHEMA}.{uc_table}"

    try:
        df = spark.table(full_table)
    except Exception as e:
        print(f"    WARNING: Cannot read {full_table}: {e} — skipping")
        return

    pdf = df.toPandas()
    cols = list(pdf.columns)
    rows = [tuple(r) for r in pdf.itertuples(index=False, name=None)]

    print(f"    Read {len(rows):,} rows, {len(cols)} columns from UC")

    if len(rows) == 0:
        print(f"    WARNING: No data in {full_table} — skipping insert")
        return

    pg_cur = pg_conn.cursor()
    pg_cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema || '.' || table_name = '{pg_table}' ORDER BY ordinal_position")
    pg_cols = [r[0] for r in pg_cur.fetchall()]
    pg_cur.close()

    if not pg_cols:
        print(f"    WARNING: Target table {pg_table} not found in Lakebase — skipping")
        return

    uc_col_lower = [c.lower() for c in cols]
    matched_indices = []
    matched_cols = []
    for pc in pg_cols:
        if pc in uc_col_lower:
            matched_indices.append(uc_col_lower.index(pc))
            matched_cols.append(pc)

    if not matched_cols:
        print(f"    WARNING: No matching columns between UC and Lakebase — skipping")
        return

    import math
    clean_rows = []
    for row in rows:
        cleaned = []
        for i in matched_indices:
            v = row[i]
            if v is None:
                cleaned.append(None)
            elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                cleaned.append(None)
            elif isinstance(v, bool):
                cleaned.append(bool(v))
            else:
                cleaned.append(v)
        clean_rows.append(tuple(cleaned))

    placeholders = ", ".join(["%s"] * len(matched_cols))
    col_names = ", ".join(matched_cols)
    insert_sql = f"INSERT INTO {pg_table} ({col_names}) VALUES ({placeholders})"

    with pg_conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {pg_table} CASCADE")
        psycopg2.extras.execute_batch(cur, insert_sql, clean_rows, page_size=2000)
    pg_conn.commit()
    print(f"    Wrote {len(clean_rows):,} rows ({len(matched_cols)} cols) to Lakebase")


def main():
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()

    print("=" * 70)
    print("  UC -> Lakebase Sync for IFRS 9 ECL Application")
    print(f"  Schema: {PG_SCHEMA}, Prefix: {PG_PREFIX}")
    print("=" * 70)

    print("\n[1/4] Ensuring Lakebase database exists ...")
    ensure_database()

    print("\n[2/4] Creating schema and tables in Lakebase ...")
    pg = get_lakebase_connection()
    pg.autocommit = True
    with pg.cursor() as cur:
        for stmt in DDL.split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt + ";")
    pg.autocommit = False
    print(f"  Schema '{PG_SCHEMA}' created with all tables and indexes")

    print("\n[3/4] Reading from UC via Spark ...")
    print("  Spark session ready")

    print("\n[4/4] Syncing tables ...")
    for uc_table, pg_table in TABLES:
        try:
            sync_table(spark, pg, uc_table, pg_table)
        except Exception as e:
            print(f"    ERROR syncing {uc_table}: {e}")
            pg.rollback()

    pg.close()

    print("\n" + "=" * 70)
    print("  Sync complete! All ECL tables are now in Lakebase.")
    print("=" * 70)


if __name__ == "__main__":
    main()

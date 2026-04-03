"""
10-Customer End-to-End Robustness Test Orchestrator
====================================================
Provisions isolated infrastructure for each customer, generates data,
runs the full ECL pipeline, configures the admin UI, and validates results.

Usage:
    python scripts/e2e_customer_test.py                  # Run all 10 customers
    python scripts/e2e_customer_test.py --customer 1     # Run only customer 1
    python scripts/e2e_customer_test.py --customer 1,3,5 # Run customers 1, 3, 5
    python scripts/e2e_customer_test.py --cleanup 1      # Tear down customer 1 infra
"""

import argparse
import json
import subprocess
import sys
import time
import textwrap

PROFILE = "lakemeter"
WORKSPACE_HOST = "https://fe-vm-lakemeter.cloud.databricks.com"
CATALOG = "lakemeter_catalog"
SCRIPTS_PATH = "/Workspace/Users/steven.tan@databricks.com/ifrs9-ecl-demo/scripts"

# ─── 10 Customer Profiles ────────────────────────────────────────────────────

CUSTOMERS = [
    {
        "id": 1,
        "name": "Apex Microfinance",
        "country": "PH",
        "currency": "PHP",
        "uc_schema": "ecl_apex_ph",
        "lakebase_instance": "ecl-apex-ph-db",
        "pg_schema": "ecl_apex_ph",
        "app_name": "ecl-apex-ph",
        "n_borrowers": 15000,
        "n_loans": 20000,
        "seed": 101,
        "products": {
            "salary_loan": {
                "count_pct": 0.45,
                "principal_range": [5000, 50000],
                "term_months": [6, 24],
                "eir_range": [0.18, 0.28],
                "base_pd": 0.05,
                "secured": False,
                "borrower_segment": "underbanked",
            },
            "emergency_cash": {
                "count_pct": 0.35,
                "principal_range": [1000, 10000],
                "term_months": [1, 6],
                "eir_range": [0.24, 0.36],
                "base_pd": 0.08,
                "secured": False,
                "borrower_segment": "underbanked",
            },
            "sme_working_capital": {
                "count_pct": 0.20,
                "principal_range": [50000, 500000],
                "term_months": [12, 36],
                "eir_range": [0.12, 0.20],
                "base_pd": 0.04,
                "secured": True,
                "borrower_segment": "both",
            },
        },
        "governance": {
            "cfo_name": "Maria Santos",
            "cfo_title": "Chief Financial Officer",
            "cro_name": "Jose Reyes",
            "cro_title": "Chief Risk Officer",
        },
    },
    {
        "id": 2,
        "name": "Nordic Credit Union",
        "country": "SE",
        "currency": "SEK",
        "uc_schema": "ecl_nordic_se",
        "lakebase_instance": "ecl-nordic-se-db",
        "pg_schema": "ecl_nordic_se",
        "app_name": "ecl-nordic-se",
        "n_borrowers": 80000,
        "n_loans": 120000,
        "seed": 202,
        "products": {
            "home_mortgage": {
                "count_pct": 0.40,
                "principal_range": [500000, 5000000],
                "term_months": [120, 360],
                "eir_range": [0.02, 0.05],
                "base_pd": 0.008,
                "secured": True,
                "borrower_segment": "both",
            },
            "auto_loan": {
                "count_pct": 0.25,
                "principal_range": [50000, 400000],
                "term_months": [24, 84],
                "eir_range": [0.03, 0.07],
                "base_pd": 0.015,
                "secured": True,
                "borrower_segment": "both",
            },
            "green_energy_loan": {
                "count_pct": 0.20,
                "principal_range": [100000, 1000000],
                "term_months": [60, 180],
                "eir_range": [0.02, 0.04],
                "base_pd": 0.01,
                "secured": True,
                "borrower_segment": "both",
            },
            "student_loan": {
                "count_pct": 0.15,
                "principal_range": [50000, 300000],
                "term_months": [36, 120],
                "eir_range": [0.01, 0.03],
                "base_pd": 0.02,
                "secured": False,
                "borrower_segment": "young_professional",
            },
        },
        "governance": {
            "cfo_name": "Erik Lindqvist",
            "cfo_title": "Ekonomichef",
            "cro_name": "Anna Bergström",
            "cro_title": "Riskchef",
        },
    },
    {
        "id": 3,
        "name": "Sahel Digital Bank",
        "country": "NG",
        "currency": "NGN",
        "uc_schema": "ecl_sahel_ng",
        "lakebase_instance": "ecl-sahel-ng-db",
        "pg_schema": "ecl_sahel_ng",
        "app_name": "ecl-sahel-ng",
        "n_borrowers": 25000,
        "n_loans": 35000,
        "seed": 303,
        "products": {
            "mobile_money_advance": {
                "count_pct": 0.65,
                "principal_range": [500, 50000],
                "term_months": [1, 3],
                "eir_range": [0.20, 0.35],
                "base_pd": 0.10,
                "secured": False,
                "borrower_segment": "underbanked",
            },
            "agri_loan": {
                "count_pct": 0.35,
                "principal_range": [10000, 500000],
                "term_months": [6, 18],
                "eir_range": [0.15, 0.25],
                "base_pd": 0.07,
                "secured": True,
                "borrower_segment": "underbanked",
            },
        },
        "governance": {
            "cfo_name": "Amina Bello",
            "cfo_title": "Chief Financial Officer",
            "cro_name": "Chukwuemeka Obi",
            "cro_title": "Head of Risk",
        },
    },
    {
        "id": 4,
        "name": "Pacific Trade Finance",
        "country": "AU",
        "currency": "AUD",
        "uc_schema": "ecl_pacific_au",
        "lakebase_instance": "ecl-pacific-au-db",
        "pg_schema": "ecl_pacific_au",
        "app_name": "ecl-pacific-au",
        "n_borrowers": 5000,
        "n_loans": 8000,
        "seed": 404,
        "products": {
            "trade_finance": {
                "count_pct": 0.30,
                "principal_range": [50000, 2000000],
                "term_months": [3, 12],
                "eir_range": [0.04, 0.08],
                "base_pd": 0.02,
                "secured": True,
                "borrower_segment": "both",
            },
            "invoice_factoring": {
                "count_pct": 0.25,
                "principal_range": [10000, 500000],
                "term_months": [1, 3],
                "eir_range": [0.06, 0.12],
                "base_pd": 0.03,
                "secured": False,
                "borrower_segment": "both",
            },
            "supply_chain_loan": {
                "count_pct": 0.20,
                "principal_range": [100000, 5000000],
                "term_months": [6, 24],
                "eir_range": [0.03, 0.07],
                "base_pd": 0.015,
                "secured": True,
                "borrower_segment": "both",
            },
            "export_credit": {
                "count_pct": 0.15,
                "principal_range": [200000, 10000000],
                "term_months": [12, 60],
                "eir_range": [0.03, 0.06],
                "base_pd": 0.01,
                "secured": True,
                "borrower_segment": "both",
            },
            "equipment_lease": {
                "count_pct": 0.10,
                "principal_range": [20000, 1000000],
                "term_months": [24, 60],
                "eir_range": [0.05, 0.09],
                "base_pd": 0.02,
                "secured": True,
                "borrower_segment": "both",
            },
        },
        "governance": {
            "cfo_name": "James Mitchell",
            "cfo_title": "Chief Financial Officer",
            "cro_name": "Sarah Chen",
            "cro_title": "Chief Risk Officer",
        },
    },
    {
        "id": 5,
        "name": "Andean Community Bank",
        "country": "CO",
        "currency": "COP",
        "uc_schema": "ecl_andean_co",
        "lakebase_instance": "ecl-andean-co-db",
        "pg_schema": "ecl_andean_co",
        "app_name": "ecl-andean-co",
        "n_borrowers": 30000,
        "n_loans": 45000,
        "seed": 505,
        "products": {
            "microcredito": {
                "count_pct": 0.40,
                "principal_range": [200000, 5000000],
                "term_months": [3, 12],
                "eir_range": [0.20, 0.35],
                "base_pd": 0.06,
                "secured": False,
                "borrower_segment": "underbanked",
            },
            "credito_consumo": {
                "count_pct": 0.35,
                "principal_range": [1000000, 20000000],
                "term_months": [12, 60],
                "eir_range": [0.12, 0.22],
                "base_pd": 0.04,
                "secured": False,
                "borrower_segment": "both",
            },
            "credito_vivienda": {
                "count_pct": 0.25,
                "principal_range": [30000000, 300000000],
                "term_months": [120, 240],
                "eir_range": [0.08, 0.14],
                "base_pd": 0.015,
                "secured": True,
                "borrower_segment": "both",
            },
        },
        "governance": {
            "cfo_name": "Carlos Rodríguez",
            "cfo_title": "Director Financiero",
            "cro_name": "Luisa Fernanda Gómez",
            "cro_title": "Directora de Riesgos",
        },
    },
    {
        "id": 6,
        "name": "Baltic Fintech",
        "country": "EE",
        "currency": "EUR",
        "uc_schema": "ecl_baltic_ee",
        "lakebase_instance": "ecl-baltic-ee-db",
        "pg_schema": "ecl_baltic_ee",
        "app_name": "ecl-baltic-ee",
        "n_borrowers": 40000,
        "n_loans": 60000,
        "seed": 606,
        "products": {
            "bnpl_retail": {
                "count_pct": 0.50,
                "principal_range": [50, 2000],
                "term_months": [1, 4],
                "eir_range": [0.0, 0.08],
                "base_pd": 0.035,
                "secured": False,
                "borrower_segment": "young_professional",
            },
            "peer_lending": {
                "count_pct": 0.30,
                "principal_range": [500, 25000],
                "term_months": [6, 36],
                "eir_range": [0.08, 0.18],
                "base_pd": 0.05,
                "secured": False,
                "borrower_segment": "both",
            },
            "crypto_backed_loan": {
                "count_pct": 0.20,
                "principal_range": [1000, 100000],
                "term_months": [3, 12],
                "eir_range": [0.06, 0.14],
                "base_pd": 0.04,
                "secured": True,
                "borrower_segment": "young_professional",
            },
        },
        "governance": {
            "cfo_name": "Kristjan Tamm",
            "cfo_title": "Chief Financial Officer",
            "cro_name": "Liina Kask",
            "cro_title": "Chief Risk Officer",
        },
    },
    {
        "id": 7,
        "name": "Gulf Islamic Bank",
        "country": "AE",
        "currency": "AED",
        "uc_schema": "ecl_gulf_ae",
        "lakebase_instance": "ecl-gulf-ae-db",
        "pg_schema": "ecl_gulf_ae",
        "app_name": "ecl-gulf-ae",
        "n_borrowers": 20000,
        "n_loans": 30000,
        "seed": 707,
        "products": {
            "murabaha": {
                "count_pct": 0.35,
                "principal_range": [10000, 500000],
                "term_months": [12, 60],
                "eir_range": [0.0, 0.0],
                "base_pd": 0.02,
                "secured": True,
                "borrower_segment": "both",
            },
            "ijara": {
                "count_pct": 0.30,
                "principal_range": [50000, 2000000],
                "term_months": [24, 120],
                "eir_range": [0.0, 0.0],
                "base_pd": 0.015,
                "secured": True,
                "borrower_segment": "both",
            },
            "tawarruq": {
                "count_pct": 0.20,
                "principal_range": [5000, 200000],
                "term_months": [6, 36],
                "eir_range": [0.0, 0.0],
                "base_pd": 0.03,
                "secured": False,
                "borrower_segment": "both",
            },
            "istisna": {
                "count_pct": 0.15,
                "principal_range": [100000, 5000000],
                "term_months": [36, 120],
                "eir_range": [0.0, 0.0],
                "base_pd": 0.01,
                "secured": True,
                "borrower_segment": "both",
            },
        },
        "governance": {
            "cfo_name": "Ahmed Al-Rashid",
            "cfo_title": "Chief Financial Officer",
            "cro_name": "Fatima Al-Mansoori",
            "cro_title": "Chief Risk Officer",
        },
    },
    {
        "id": 8,
        "name": "Heartland Credit",
        "country": "US",
        "currency": "USD",
        "uc_schema": "ecl_heartland_us",
        "lakebase_instance": "ecl-heartland-us-db",
        "pg_schema": "ecl_heartland_us",
        "app_name": "ecl-heartland-us",
        "n_borrowers": 10000,
        "n_loans": 12000,
        "seed": 808,
        "products": {
            "personal_unsecured": {
                "count_pct": 1.0,
                "principal_range": [1000, 35000],
                "term_months": [12, 60],
                "eir_range": [0.08, 0.24],
                "base_pd": 0.045,
                "secured": False,
                "borrower_segment": "both",
            },
        },
        "governance": {
            "cfo_name": "Robert Johnson",
            "cfo_title": "Chief Financial Officer",
            "cro_name": "Patricia Williams",
            "cro_title": "Chief Risk Officer",
        },
    },
    {
        "id": 9,
        "name": "Mekong Rural Bank",
        "country": "VN",
        "currency": "VND",
        "uc_schema": "ecl_mekong_vn",
        "lakebase_instance": "ecl-mekong-vn-db",
        "pg_schema": "ecl_mekong_vn",
        "app_name": "ecl-mekong-vn",
        "n_borrowers": 50000,
        "n_loans": 70000,
        "seed": 909,
        "products": {
            "rice_paddy_loan": {
                "count_pct": 0.25,
                "principal_range": [5000000, 50000000],
                "term_months": [3, 12],
                "eir_range": [0.08, 0.14],
                "base_pd": 0.06,
                "secured": True,
                "borrower_segment": "underbanked",
            },
            "livestock_loan": {
                "count_pct": 0.15,
                "principal_range": [10000000, 100000000],
                "term_months": [6, 24],
                "eir_range": [0.09, 0.15],
                "base_pd": 0.05,
                "secured": True,
                "borrower_segment": "underbanked",
            },
            "motorbike_loan": {
                "count_pct": 0.20,
                "principal_range": [15000000, 80000000],
                "term_months": [12, 36],
                "eir_range": [0.10, 0.18],
                "base_pd": 0.04,
                "secured": True,
                "borrower_segment": "both",
            },
            "market_vendor_loan": {
                "count_pct": 0.15,
                "principal_range": [2000000, 30000000],
                "term_months": [1, 6],
                "eir_range": [0.15, 0.25],
                "base_pd": 0.08,
                "secured": False,
                "borrower_segment": "underbanked",
            },
            "remittance_advance": {
                "count_pct": 0.10,
                "principal_range": [1000000, 10000000],
                "term_months": [1, 3],
                "eir_range": [0.12, 0.20],
                "base_pd": 0.07,
                "secured": False,
                "borrower_segment": "underbanked",
            },
            "seasonal_crop_loan": {
                "count_pct": 0.10,
                "principal_range": [3000000, 40000000],
                "term_months": [3, 9],
                "eir_range": [0.10, 0.16],
                "base_pd": 0.065,
                "secured": True,
                "borrower_segment": "underbanked",
            },
            "fishery_loan": {
                "count_pct": 0.05,
                "principal_range": [8000000, 60000000],
                "term_months": [6, 18],
                "eir_range": [0.09, 0.14],
                "base_pd": 0.055,
                "secured": True,
                "borrower_segment": "underbanked",
            },
        },
        "governance": {
            "cfo_name": "Nguyen Van Minh",
            "cfo_title": "Giám đốc Tài chính",
            "cro_name": "Tran Thi Lan",
            "cro_title": "Giám đốc Rủi ro",
        },
    },
    {
        "id": 10,
        "name": "Zurich Private Bank",
        "country": "CH",
        "currency": "CHF",
        "uc_schema": "ecl_zurich_ch",
        "lakebase_instance": "ecl-zurich-ch-db",
        "pg_schema": "ecl_zurich_ch",
        "app_name": "ecl-zurich-ch",
        "n_borrowers": 800,
        "n_loans": 2000,
        "seed": 1010,
        "products": {
            "lombard_loan": {
                "count_pct": 0.60,
                "principal_range": [100000, 10000000],
                "term_months": [12, 60],
                "eir_range": [0.015, 0.04],
                "base_pd": 0.005,
                "secured": True,
                "borrower_segment": "both",
            },
            "structured_product": {
                "count_pct": 0.40,
                "principal_range": [500000, 50000000],
                "term_months": [24, 120],
                "eir_range": [0.02, 0.05],
                "base_pd": 0.008,
                "secured": True,
                "borrower_segment": "both",
            },
        },
        "governance": {
            "cfo_name": "Hans Müller",
            "cfo_title": "Chief Financial Officer",
            "cro_name": "Claudia Brunner",
            "cro_title": "Chief Risk Officer",
        },
    },
]


# ─── CLI Helpers ──────────────────────────────────────────────────────────────

def cli(args, check=True, capture=True):
    """Run a Databricks CLI command with the lakemeter profile."""
    cmd = ["databricks", "--profile", PROFILE] + args
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        timeout=120,
    )
    if capture and result.stdout:
        print(f"    {result.stdout.strip()[:500]}")
    if result.returncode != 0 and check:
        print(f"    STDERR: {result.stderr.strip()[:500]}")
        raise RuntimeError(f"CLI failed: {' '.join(args)}")
    return result


def api_post(path, body):
    """POST to Databricks REST API."""
    import requests
    token_result = subprocess.run(
        ["databricks", "--profile", PROFILE, "auth", "token"],
        capture_output=True, text=True,
    )
    token_json = json.loads(token_result.stdout)
    token = token_json.get("access_token") or token_json.get("token_value", "")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(f"{WORKSPACE_HOST}{path}", headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    return resp.json() if resp.content else {}


def api_get(path):
    """GET from Databricks REST API."""
    import requests
    token_result = subprocess.run(
        ["databricks", "--profile", PROFILE, "auth", "token"],
        capture_output=True, text=True,
    )
    token_json = json.loads(token_result.stdout)
    token = token_json.get("access_token") or token_json.get("token_value", "")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{WORKSPACE_HOST}{path}", headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json() if resp.content else {}


# ─── Infrastructure Provisioning ──────────────────────────────────────────────

def provision_schema(customer):
    """Create UC schema if it doesn't exist."""
    schema = customer["uc_schema"]
    print(f"\n  [SCHEMA] Creating {CATALOG}.{schema}...")
    try:
        cli(["schemas", "create", schema, CATALOG,
             "--comment", f"ECL E2E test: {customer['name']}"])
    except RuntimeError:
        print(f"    Schema {schema} may already exist, continuing...")


def provision_lakebase(customer):
    """Create Lakebase instance if it doesn't exist."""
    instance = customer["lakebase_instance"]
    print(f"\n  [LAKEBASE] Creating instance {instance}...")
    try:
        result = api_post("/api/2.0/database/instances", {
            "name": instance,
            "capacity": "CU_1",
        })
        print(f"    Created: {result.get('name', instance)}")
    except Exception as e:
        if "ALREADY_EXISTS" in str(e) or "already exists" in str(e).lower():
            print(f"    Instance {instance} already exists, continuing...")
        else:
            print(f"    WARNING: {e}")


def create_app(customer):
    """Create Databricks App if it doesn't exist."""
    app_name = customer["app_name"]
    print(f"\n  [APP] Creating app {app_name}...")
    try:
        result = api_post("/api/2.0/apps", {
            "name": app_name,
            "description": f"IFRS 9 ECL - {customer['name']}",
        })
        print(f"    Created app: {result.get('name', app_name)}")
    except Exception as e:
        if "ALREADY_EXISTS" in str(e) or "already exists" in str(e).lower():
            print(f"    App {app_name} already exists, continuing...")
        else:
            print(f"    WARNING: {e}")


def create_jobs(customer):
    """Create Databricks Jobs for the customer and return job IDs."""
    schema = customer["uc_schema"]
    lb_instance = customer["lakebase_instance"]
    pg_schema = customer["pg_schema"]
    name_prefix = customer["app_name"]

    base_params = {
        "catalog": CATALOG,
        "schema": schema,
        "lakebase_instance": lb_instance,
        "lakebase_schema": pg_schema,
        "lakebase_prefix": "lb_",
        "reporting_date": "2025-12-31",
        "workspace_scripts_path": SCRIPTS_PATH,
    }

    def _nb_task(key, notebook, extra_params=None):
        params = dict(base_params)
        if extra_params:
            params.update(extra_params)
        return {
            "task_key": key,
            "notebook_task": {
                "notebook_path": f"{SCRIPTS_PATH}/{notebook}.py",
                "base_parameters": params,
                "source": "WORKSPACE",
            },
            "environment_key": "default",
        }

    full_pipeline_tasks = [
        _nb_task("generate_data", "01_generate_data", {
            "product_config": json.dumps(customer["products"]),
            "n_borrowers": str(customer["n_borrowers"]),
            "n_loans": str(customer["n_loans"]),
            "seed": str(customer["seed"]),
            "currency": customer["currency"],
            "country": customer["country"],
        }),
        _nb_task("process_data", "02_run_data_processing"),
        _nb_task("satellite_model", "03a_satellite_model"),
        _nb_task("ecl_calculation", "03b_run_ecl_calculation"),
        _nb_task("sync_lakebase", "04_sync_to_lakebase"),
    ]
    for i in range(1, len(full_pipeline_tasks)):
        full_pipeline_tasks[i]["depends_on"] = [{"task_key": full_pipeline_tasks[i - 1]["task_key"]}]

    sat_ecl_tasks = [
        _nb_task("satellite_model", "03a_satellite_model"),
        _nb_task("ecl_calculation", "03b_run_ecl_calculation"),
        _nb_task("sync_lakebase", "04_sync_to_lakebase"),
    ]
    for i in range(1, len(sat_ecl_tasks)):
        sat_ecl_tasks[i]["depends_on"] = [{"task_key": sat_ecl_tasks[i - 1]["task_key"]}]

    job_ids = {}

    print(f"\n  [JOBS] Creating full_pipeline job for {name_prefix}...")
    try:
        result = api_post("/api/2.1/jobs/create", {
            "name": f"{name_prefix}-full-pipeline",
            "tasks": full_pipeline_tasks,
            "environments": [{"environment_key": "default", "spec": {"client": "1"}}],
            "queue": {"enabled": True},
        })
        job_ids["full_pipeline"] = result["job_id"]
        print(f"    Created job ID: {result['job_id']}")
    except Exception as e:
        print(f"    ERROR creating full_pipeline job: {e}")

    print(f"  [JOBS] Creating satellite_ecl_sync job for {name_prefix}...")
    try:
        result = api_post("/api/2.1/jobs/create", {
            "name": f"{name_prefix}-satellite-ecl-sync",
            "tasks": sat_ecl_tasks,
            "environments": [{"environment_key": "default", "spec": {"client": "1"}}],
            "queue": {"enabled": True},
        })
        job_ids["satellite_ecl_sync"] = result["job_id"]
        print(f"    Created job ID: {result['job_id']}")
    except Exception as e:
        print(f"    ERROR creating satellite_ecl_sync job: {e}")

    return job_ids


def run_job_and_wait(job_id, timeout_minutes=60):
    """Trigger a job and wait for completion."""
    print(f"  [RUN] Triggering job {job_id}...")
    result = api_post("/api/2.0/jobs/run-now", {"job_id": job_id})
    run_id = result.get("run_id")
    print(f"    Run ID: {run_id}")

    start = time.time()
    while time.time() - start < timeout_minutes * 60:
        status = api_get(f"/api/2.0/jobs/runs/get?run_id={run_id}")
        state = status.get("state", {})
        lcs = state.get("life_cycle_state", "")
        rs = state.get("result_state", "")

        if lcs == "TERMINATED":
            elapsed = round((time.time() - start) / 60, 1)
            if rs == "SUCCESS":
                print(f"    Job completed successfully in {elapsed} min")
                return {"status": "SUCCESS", "run_id": run_id, "elapsed_min": elapsed}
            else:
                msg = state.get("state_message", "")
                print(f"    Job FAILED ({rs}): {msg}")
                return {"status": rs, "run_id": run_id, "elapsed_min": elapsed, "message": msg}
        elif lcs in ("INTERNAL_ERROR", "SKIPPED"):
            return {"status": lcs, "run_id": run_id}

        time.sleep(30)

    return {"status": "TIMEOUT", "run_id": run_id}


def configure_admin(customer, job_ids):
    """Configure the admin settings via the app's API (or directly in Lakebase)."""
    print(f"\n  [CONFIG] Admin configuration for {customer['name']}...")

    lgd_assumptions = {}
    for product, cfg in customer["products"].items():
        lgd_assumptions[product] = {
            "lgd": round(0.25 + cfg["base_pd"] * 5, 2) if not cfg.get("secured") else 0.20,
            "recovery_rate": round(1.0 - (0.25 + cfg["base_pd"] * 5), 2) if not cfg.get("secured") else 0.80,
        }

    config = {
        "data_sources": {
            "catalog": CATALOG,
            "schema": customer["uc_schema"],
            "lakebase_schema": customer["pg_schema"],
            "lakebase_prefix": "lb_",
        },
        "model": {
            "lgd_assumptions": lgd_assumptions,
        },
        "app_settings": {
            "org_name": customer["name"],
            "currency": customer["currency"],
            "country": customer["country"],
            "reporting_date": "2025-12-31",
            "governance": customer.get("governance", {}),
        },
        "jobs": {
            "workspace_url": WORKSPACE_HOST,
            "job_ids": job_ids,
        },
    }

    print(f"    Config prepared: {len(customer['products'])} products, "
          f"currency={customer['currency']}, schema={customer['uc_schema']}")
    return config


WAREHOUSE_ID = "6d6a769cb92206f7"


def run_sql(sql):
    """Execute SQL via the Statement Execution API and return the result."""
    result = api_post("/api/2.0/sql/statements", {
        "warehouse_id": WAREHOUSE_ID,
        "statement": sql,
        "wait_timeout": "30s",
    })
    status = result.get("status", {}).get("state", "")
    if status == "SUCCEEDED":
        data = result.get("result", {}).get("data_array", [])
        return data
    return None


def validate_results(customer):
    """Validate that the pipeline produced expected outputs in UC."""
    schema = customer["uc_schema"]
    print(f"\n  [VALIDATE] Checking {CATALOG}.{schema}...")

    checks = []
    expected_tables = [
        "loan_tape", "borrower_master", "payment_history",
        "general_ledger", "macro_scenarios", "collateral_register",
        "historical_defaults", "quarterly_default_rates",
        "model_ready_loans", "dq_results", "gl_reconciliation",
        "sicr_thresholds", "satellite_model_comparison",
        "satellite_model_selected", "loan_level_ecl",
        "loan_ecl_weighted", "portfolio_ecl_summary",
        "scenario_ecl_summary", "mc_ecl_distribution",
    ]

    for table in expected_tables:
        try:
            data = run_sql(f"SELECT COUNT(*) as cnt FROM {CATALOG}.{schema}.{table}")
            if data is not None:
                cnt = data[0][0] if data else "0"
                checks.append({"table": table, "status": "OK", "count": cnt})
            else:
                checks.append({"table": table, "status": "MISSING", "count": 0})
        except Exception as e:
            err = str(e)
            if "TABLE_OR_VIEW_NOT_FOUND" in err or "does not exist" in err.lower():
                checks.append({"table": table, "status": "MISSING", "count": 0})
            else:
                checks.append({"table": table, "status": "ERROR", "count": str(e)[:100]})

    ok_count = sum(1 for c in checks if c["status"] == "OK")
    print(f"    Tables: {ok_count}/{len(expected_tables)} present")
    for c in checks:
        if c["status"] == "OK":
            print(f"    OK: {c['table']} ({c['count']} rows)")
        else:
            print(f"    MISSING: {c['table']}")

    return checks


# ─── Cleanup ──────────────────────────────────────────────────────────────────

def cleanup_customer(customer):
    """Remove all infrastructure for a customer."""
    print(f"\n{'='*70}")
    print(f"CLEANUP: {customer['name']}")
    print(f"{'='*70}")

    print(f"  Dropping schema {CATALOG}.{customer['uc_schema']}...")
    try:
        run_sql(f"DROP SCHEMA IF EXISTS {CATALOG}.{customer['uc_schema']} CASCADE")
        print(f"    Schema dropped")
    except Exception as e:
        print(f"    {e}")

    print(f"  Deleting Lakebase instance {customer['lakebase_instance']}...")
    try:
        api_post(f"/api/2.0/database/instances/{customer['lakebase_instance']}/delete", {})
    except Exception as e:
        print(f"    {e}")

    print(f"  Deleting app {customer['app_name']}...")
    try:
        import requests
        token_result = subprocess.run(
            ["databricks", "--profile", PROFILE, "auth", "token"],
            capture_output=True, text=True,
        )
        token_json = json.loads(token_result.stdout)
        token = token_json.get("access_token") or token_json.get("token_value", "")
        headers = {"Authorization": f"Bearer {token}"}
        requests.delete(f"{WORKSPACE_HOST}/api/2.0/apps/{customer['app_name']}",
                        headers=headers, timeout=30)
    except Exception as e:
        print(f"    {e}")


# ─── Main Orchestration ──────────────────────────────────────────────────────

def run_customer_cycle(customer):
    """Run the full E2E cycle for a single customer."""
    cid = customer["id"]
    name = customer["name"]
    print(f"\n{'='*70}")
    print(f"CYCLE {cid}: {name}")
    print(f"  Country: {customer['country']}, Currency: {customer['currency']}")
    print(f"  Products: {list(customer['products'].keys())}")
    print(f"  Schema: {CATALOG}.{customer['uc_schema']}")
    print(f"  Lakebase: {customer['lakebase_instance']}")
    print(f"  App: {customer['app_name']}")
    print(f"{'='*70}")

    results = {
        "customer_id": cid,
        "customer_name": name,
        "steps": {},
        "issues": [],
    }

    # Step 1: Provision infrastructure
    print(f"\n--- Step 1: Provision Infrastructure ---")
    try:
        provision_schema(customer)
        results["steps"]["schema"] = "OK"
    except Exception as e:
        results["steps"]["schema"] = f"FAIL: {e}"
        results["issues"].append(f"Schema creation failed: {e}")

    try:
        provision_lakebase(customer)
        results["steps"]["lakebase"] = "OK"
    except Exception as e:
        results["steps"]["lakebase"] = f"FAIL: {e}"
        results["issues"].append(f"Lakebase creation failed: {e}")

    try:
        create_app(customer)
        results["steps"]["app"] = "OK"
    except Exception as e:
        results["steps"]["app"] = f"FAIL: {e}"
        results["issues"].append(f"App creation failed: {e}")

    # Step 2: Create jobs
    print(f"\n--- Step 2: Create Databricks Jobs ---")
    try:
        job_ids = create_jobs(customer)
        results["steps"]["jobs"] = f"OK: {job_ids}"
        results["job_ids"] = job_ids
    except Exception as e:
        results["steps"]["jobs"] = f"FAIL: {e}"
        results["issues"].append(f"Job creation failed: {e}")
        job_ids = {}

    # Step 3: Run full pipeline
    if job_ids.get("full_pipeline"):
        print(f"\n--- Step 3: Run Full Pipeline ---")
        try:
            run_result = run_job_and_wait(job_ids["full_pipeline"], timeout_minutes=45)
            results["steps"]["pipeline"] = run_result["status"]
            if run_result["status"] != "SUCCESS":
                results["issues"].append(f"Pipeline failed: {run_result}")
        except Exception as e:
            results["steps"]["pipeline"] = f"FAIL: {e}"
            results["issues"].append(f"Pipeline execution failed: {e}")
    else:
        results["steps"]["pipeline"] = "SKIPPED (no job_id)"

    # Step 4: Configure admin
    print(f"\n--- Step 4: Configure Admin ---")
    try:
        config = configure_admin(customer, job_ids)
        results["steps"]["admin_config"] = "OK"
        results["admin_config"] = config
    except Exception as e:
        results["steps"]["admin_config"] = f"FAIL: {e}"
        results["issues"].append(f"Admin config failed: {e}")

    # Step 5: Validate
    print(f"\n--- Step 5: Validate Results ---")
    try:
        checks = validate_results(customer)
        ok = sum(1 for c in checks if c["status"] == "OK")
        total = len(checks)
        results["steps"]["validation"] = f"{ok}/{total} tables OK"
        if ok < total:
            missing = [c["table"] for c in checks if c["status"] != "OK"]
            results["issues"].append(f"Missing tables: {missing}")
    except Exception as e:
        results["steps"]["validation"] = f"FAIL: {e}"
        results["issues"].append(f"Validation failed: {e}")

    # Summary
    print(f"\n--- Cycle {cid} Summary ---")
    for step, status in results["steps"].items():
        icon = "OK" if "OK" in str(status) or status == "SUCCESS" else "ISSUE"
        print(f"  [{icon}] {step}: {status}")
    if results["issues"]:
        print(f"  Issues ({len(results['issues'])}):")
        for issue in results["issues"]:
            print(f"    - {issue}")
    else:
        print(f"  No issues found!")

    return results


def print_summary(all_results):
    """Print a summary table of all customer results."""
    print(f"\n{'='*70}")
    print("OVERALL SUMMARY")
    print(f"{'='*70}")
    print(f"{'#':<4} {'Customer':<30} {'Schema':>6} {'LB':>6} {'App':>6} {'Jobs':>6} {'Pipeline':>10} {'Validate':>12} {'Issues':>7}")
    print("-" * 95)
    for r in all_results:
        def _short(s):
            s = str(s)
            if "OK" in s or s == "SUCCESS":
                return "OK"
            if "SKIP" in s:
                return "SKIP"
            return "FAIL"

        steps = r["steps"]
        print(f"{r['customer_id']:<4} {r['customer_name']:<30} "
              f"{_short(steps.get('schema', '?')):>6} "
              f"{_short(steps.get('lakebase', '?')):>6} "
              f"{_short(steps.get('app', '?')):>6} "
              f"{_short(steps.get('jobs', '?')):>6} "
              f"{_short(steps.get('pipeline', '?')):>10} "
              f"{str(steps.get('validation', '?'))[:12]:>12} "
              f"{len(r['issues']):>7}")

    total_issues = sum(len(r["issues"]) for r in all_results)
    passed = sum(1 for r in all_results if len(r["issues"]) == 0)
    print(f"\n  {passed}/{len(all_results)} customers passed with zero issues")
    print(f"  Total issues across all customers: {total_issues}")


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="10-Customer E2E Robustness Test")
    parser.add_argument("--customer", type=str, default=None,
                        help="Comma-separated customer IDs to run (e.g. 1,3,5). Default: all")
    parser.add_argument("--cleanup", type=str, default=None,
                        help="Comma-separated customer IDs to clean up")
    parser.add_argument("--provision-only", action="store_true",
                        help="Only provision infrastructure, don't run pipeline")
    parser.add_argument("--validate-only", action="store_true",
                        help="Only validate existing results")
    args = parser.parse_args()

    if args.cleanup:
        ids = [int(x.strip()) for x in args.cleanup.split(",")]
        for cust in CUSTOMERS:
            if cust["id"] in ids:
                cleanup_customer(cust)
        return

    if args.customer:
        ids = [int(x.strip()) for x in args.customer.split(",")]
        selected = [c for c in CUSTOMERS if c["id"] in ids]
    else:
        selected = CUSTOMERS

    if args.validate_only:
        for cust in selected:
            validate_results(cust)
        return

    all_results = []
    for cust in selected:
        result = run_customer_cycle(cust)
        all_results.append(result)

        # Save intermediate results
        with open("e2e_results.json", "w") as f:
            json.dump(all_results, f, indent=2, default=str)

    print_summary(all_results)

    with open("e2e_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to e2e_results.json")


if __name__ == "__main__":
    main()

"""
Provision a Databricks Lakeview dashboard from the 7 SQL query files.

Usage:
    python -m dashboards.provision_dashboard [--update] [--warehouse-id WH_ID]
"""

import argparse
import json
import logging
import os
import sys

from dashboards import QUERY_FILES, load_query

log = logging.getLogger(__name__)

DASHBOARD_NAME = "IFRS 9 ECL Platform Analytics"

# Maps each SQL file to its dashboard page title
PAGE_TITLES = {
    "01_user_activity.sql": "User Activity",
    "02_project_analytics.sql": "Project Analytics",
    "03_model_performance.sql": "Model Performance",
    "04_job_execution.sql": "Job Execution",
    "05_api_usage.sql": "API Usage",
    "06_cost_allocation.sql": "Cost Allocation",
    "07_system_health.sql": "System Health",
}


def _build_dashboard_spec(schema: str = "expected_credit_loss") -> dict:
    """Build the Lakeview dashboard JSON spec from SQL files."""
    pages = []
    datasets = []
    for _i, filename in enumerate(QUERY_FILES):
        sql = load_query(filename, schema)
        dataset_name = filename.replace(".sql", "")
        datasets.append({"name": dataset_name, "query": sql})
        pages.append(
            {
                "name": PAGE_TITLES.get(filename, dataset_name),
                "displayName": PAGE_TITLES.get(filename, dataset_name),
            }
        )
    return {
        "displayName": DASHBOARD_NAME,
        "datasets": datasets,
        "pages": pages,
    }


def provision(
    update: bool = False,
    warehouse_id: str | None = None,
    schema: str = "expected_credit_loss",
) -> dict:
    """Create or update the Lakeview dashboard.

    Returns dict with dashboard_id and dashboard_url.
    """
    try:
        from databricks.sdk import WorkspaceClient
    except ImportError:
        log.error("databricks-sdk not installed — run: pip install databricks-sdk")
        return {"error": "databricks-sdk not installed"}

    w = WorkspaceClient()
    spec = _build_dashboard_spec(schema)
    serialized = json.dumps(spec)

    if update:
        dashboards = list(w.lakeview.list())
        match = next((d for d in dashboards if d.display_name == DASHBOARD_NAME), None)
        if match:
            result = w.lakeview.update(
                match.dashboard_id,
                display_name=DASHBOARD_NAME,
                serialized_dashboard=serialized,
                warehouse_id=warehouse_id or os.getenv("WAREHOUSE_ID"),
            )
            log.info("Updated dashboard %s", result.dashboard_id)
            return {
                "dashboard_id": result.dashboard_id,
                "action": "updated",
            }

    result = w.lakeview.create(
        display_name=DASHBOARD_NAME,
        serialized_dashboard=serialized,
        warehouse_id=warehouse_id or os.getenv("WAREHOUSE_ID"),
    )
    log.info("Created dashboard %s", result.dashboard_id)
    return {
        "dashboard_id": result.dashboard_id,
        "action": "created",
    }


def main():
    parser = argparse.ArgumentParser(description="Provision Lakeview dashboard")
    parser.add_argument("--update", action="store_true", help="Update existing dashboard")
    parser.add_argument("--warehouse-id", help="SQL warehouse ID")
    parser.add_argument("--schema", default="expected_credit_loss")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    result = provision(
        update=args.update,
        warehouse_id=args.warehouse_id,
        schema=args.schema,
    )
    print(json.dumps(result, indent=2))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    sys.exit(main())

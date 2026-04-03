import json as _json
import uuid
import logging
import pandas as pd

from db.pool import query_df, execute, _t, SCHEMA

log = logging.getLogger(__name__)


def ensure_markov_tables():
    try:
        query_df(f"SELECT model_name FROM {SCHEMA}.markov_transition_matrices LIMIT 1")
    except Exception:
        try:
            execute(f"DROP TABLE IF EXISTS {SCHEMA}.markov_forecasts CASCADE")
            execute(f"DROP TABLE IF EXISTS {SCHEMA}.markov_transition_matrices CASCADE")
            log.info("Dropped legacy markov tables for schema migration")
        except Exception:
            pass
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.markov_transition_matrices (
            matrix_id TEXT PRIMARY KEY,
            model_name TEXT,
            estimation_date DATE DEFAULT CURRENT_DATE,
            matrix_data JSONB,
            matrix_type TEXT DEFAULT 'annual',
            product_type TEXT,
            segment TEXT,
            methodology TEXT DEFAULT 'cohort',
            n_observations INT,
            computed_at TIMESTAMP DEFAULT NOW()
        )
    """)
    execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.markov_forecasts (
            forecast_id TEXT PRIMARY KEY,
            matrix_id TEXT NOT NULL,
            horizon_months INT,
            forecast_data JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    log.info("Ensured markov tables exist")


MARKOV_MATRIX_TABLE = f"{SCHEMA}.markov_transition_matrices"
MARKOV_FORECAST_TABLE = f"{SCHEMA}.markov_forecasts"

_MARKOV_STATES = ["Stage 1", "Stage 2", "Stage 3", "Default"]


def estimate_transition_matrix(product_type: str | None = None, segment: str | None = None) -> dict:
    """Estimate a Markov transition matrix from actual stage migration data."""
    conditions = []
    params = []
    if product_type:
        conditions.append("product_type = %s")
        params.append(product_type)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    mig_df = query_df(f"""
        SELECT original_stage, assessed_stage,
               SUM(loan_count) as loan_count
        FROM {_t('ifrs7_stage_migration')}
        {where}
        GROUP BY original_stage, assessed_stage
        ORDER BY original_stage, assessed_stage
    """, tuple(params) if params else None)

    n_states = 4  # Stage 1, Stage 2, Stage 3, Default
    matrix = [[0.0] * n_states for _ in range(n_states)]
    n_obs = 0

    if not mig_df.empty:
        for _, row in mig_df.iterrows():
            orig = int(row["original_stage"]) - 1
            dest = int(row["assessed_stage"]) - 1
            if 0 <= orig < 3 and 0 <= dest < 3:
                count = int(row["loan_count"])
                matrix[orig][dest] += count
                n_obs += count

    # Infer default transitions from historical defaults data
    try:
        cond_parts = []
        cond_params = []
        if product_type:
            cond_parts.append("product_type = %s")
            cond_params.append(product_type)

        extra_where = f"WHERE {' AND '.join(cond_parts)}" if cond_parts else ""

        # Estimate default rate from actual historical defaults vs Stage 3 population
        defaults_df = query_df(f"""
            SELECT COUNT(*) as default_count
            FROM {_t('historical_defaults')}
            {extra_where}
        """, tuple(cond_params) if cond_params else None)

        dpd_df = query_df(f"""
            SELECT assessed_stage, COUNT(*) as cnt
            FROM {_t('model_ready_loans')}
            {extra_where}
            GROUP BY assessed_stage
        """, tuple(cond_params) if cond_params else None)

        stage_counts = {}
        for _, row in dpd_df.iterrows():
            stage_counts[int(row["assessed_stage"])] = int(row["cnt"])

        total_s3 = stage_counts.get(3, 0)
        if total_s3 > 0:
            n_defaults = int(defaults_df.iloc[0]["default_count"]) if not defaults_df.empty else 0
            if n_defaults > 0 and total_s3 > 0:
                default_rate = min(n_defaults / total_s3, 0.95)
                log.info("Estimated Stage 3→Default rate from data: %.4f (%d defaults / %d Stage 3)",
                         default_rate, n_defaults, total_s3)
            else:
                default_rate = 0.15
                log.warning("Insufficient default data — using fallback Stage 3→Default rate: %.2f", default_rate)
            matrix[2][3] = total_s3 * default_rate
    except Exception as exc:
        log.warning("Could not estimate default transitions: %s", exc)

    # Default/write-off is absorbing
    matrix[3] = [0.0, 0.0, 0.0, 1.0]

    # Normalize rows
    for i in range(n_states):
        row_sum = sum(matrix[i])
        if row_sum > 0:
            matrix[i] = [v / row_sum for v in matrix[i]]
        else:
            matrix[i][i] = 1.0

    matrix_id = str(uuid.uuid4())
    model_name = f"TM-{product_type or 'All'}-{segment or 'All'}"

    matrix_data = {
        "states": _MARKOV_STATES,
        "matrix": [[round(v, 6) for v in row] for row in matrix],
    }

    execute(f"""
        INSERT INTO {MARKOV_MATRIX_TABLE}
            (matrix_id, model_name, matrix_data, matrix_type, product_type, segment, methodology, n_observations)
        VALUES (%s, %s, %s, 'annual', %s, %s, 'cohort', %s)
    """, (matrix_id, model_name, _json.dumps(matrix_data), product_type, segment, n_obs))

    return get_transition_matrix(matrix_id)


def get_transition_matrix(matrix_id: str) -> dict | None:
    df = query_df(f"SELECT * FROM {MARKOV_MATRIX_TABLE} WHERE matrix_id = %s", (matrix_id,))
    if df.empty:
        return None
    row = df.iloc[0].to_dict()
    for col in ("matrix_data",):
        v = row.get(col)
        if isinstance(v, str):
            try:
                row[col] = _json.loads(v)
            except Exception:
                pass
    return row


def list_transition_matrices(product_type: str | None = None) -> list[dict]:
    if product_type:
        df = query_df(f"""
            SELECT matrix_id, model_name, estimation_date, matrix_type, product_type,
                   segment, methodology, n_observations, computed_at
            FROM {MARKOV_MATRIX_TABLE}
            WHERE product_type = %s
            ORDER BY computed_at DESC
        """, (product_type,))
    else:
        df = query_df(f"""
            SELECT matrix_id, model_name, estimation_date, matrix_type, product_type,
                   segment, methodology, n_observations, computed_at
            FROM {MARKOV_MATRIX_TABLE}
            ORDER BY computed_at DESC
        """)
    if df.empty:
        return []
    return df.to_dict("records")


def _mat_mult(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    """Multiply two NxN matrices."""
    n = len(a)
    result = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result[i][j] += a[i][k] * b[k][j]
    return result


def _mat_power(m: list[list[float]], power: int) -> list[list[float]]:
    """Compute matrix exponentiation via repeated squaring."""
    n = len(m)
    result = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    base = [row[:] for row in m]
    p = power
    while p > 0:
        if p % 2 == 1:
            result = _mat_mult(result, base)
        base = _mat_mult(base, base)
        p //= 2
    return result


def forecast_stage_distribution(matrix_id: str, initial_distribution: list[float],
                                 horizon_months: int) -> dict:
    """Project future stage distribution using matrix exponentiation."""
    mat_record = get_transition_matrix(matrix_id)
    if not mat_record:
        raise ValueError(f"Matrix {matrix_id} not found")

    matrix_data = mat_record["matrix_data"]
    matrix = matrix_data["matrix"]
    states = matrix_data["states"]
    n = len(states)

    if len(initial_distribution) < n:
        initial_distribution = initial_distribution + [0.0] * (n - len(initial_distribution))
    dist_sum = sum(initial_distribution[:n])
    if dist_sum > 0:
        initial_distribution = [v / dist_sum for v in initial_distribution[:n]]

    forecast_points = []
    for month in range(0, horizon_months + 1):
        p_n = _mat_power(matrix, month)
        dist = [0.0] * n
        for j in range(n):
            for i in range(n):
                dist[j] += initial_distribution[i] * p_n[i][j]
        forecast_points.append({
            "month": month,
            **{states[k]: round(dist[k] * 100, 4) for k in range(n)},
        })

    forecast_id = str(uuid.uuid4())
    forecast_data = {
        "initial_distribution": initial_distribution,
        "horizon_months": horizon_months,
        "points": forecast_points,
    }

    execute(f"""
        INSERT INTO {MARKOV_FORECAST_TABLE}
            (forecast_id, matrix_id, horizon_months, forecast_data)
        VALUES (%s, %s, %s, %s)
    """, (forecast_id, matrix_id, horizon_months, _json.dumps(forecast_data)))

    return {
        "forecast_id": forecast_id,
        "matrix_id": matrix_id,
        "horizon_months": horizon_months,
        "forecast_data": forecast_data,
    }


def compute_lifetime_pd(matrix_id: str, max_months: int = 60) -> dict:
    """Compute cumulative lifetime PD from the transition matrix."""
    mat_record = get_transition_matrix(matrix_id)
    if not mat_record:
        raise ValueError(f"Matrix {matrix_id} not found")

    matrix_data = mat_record["matrix_data"]
    matrix = matrix_data["matrix"]
    states = matrix_data["states"]
    n = len(states)
    default_idx = n - 1

    pd_curves = {}
    for start_stage in range(min(3, n)):
        initial = [0.0] * n
        initial[start_stage] = 1.0
        curve = []
        for month in range(0, max_months + 1):
            p_n = _mat_power(matrix, month)
            cum_pd = 0.0
            for i in range(n):
                cum_pd += initial[i] * p_n[i][default_idx]
            curve.append({
                "month": month,
                "cumulative_pd": round(cum_pd * 100, 4),
            })
        pd_curves[states[start_stage]] = curve

    return {
        "matrix_id": matrix_id,
        "max_months": max_months,
        "pd_curves": pd_curves,
    }


def compare_matrices(matrix_ids: list[str]) -> list[dict]:
    """Side-by-side comparison of multiple transition matrices."""
    results = []
    for mid in matrix_ids:
        mat = get_transition_matrix(mid)
        if mat:
            results.append(mat)
    return results

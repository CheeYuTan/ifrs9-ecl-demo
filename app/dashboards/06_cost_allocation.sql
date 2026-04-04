-- Dashboard: Cost Allocation
-- Sources: pg_total_relation_size() (system), pipeline_runs
-- Metrics: storage by table, compute estimates by job type

-- ── Storage by Table (Lakebase schema) ───────────────────────────────────────
SELECT
    t.tablename                                         AS table_name,
    pg_total_relation_size(
        quote_ident('{schema}') || '.' || quote_ident(t.tablename)
    )                                                   AS total_bytes,
    pg_size_pretty(
        pg_total_relation_size(
            quote_ident('{schema}') || '.' || quote_ident(t.tablename)
        )
    )                                                   AS total_size,
    COALESCE(
        (SELECT reltuples::BIGINT
         FROM pg_class c
         JOIN pg_namespace n ON n.oid = c.relnamespace
         WHERE n.nspname = '{schema}' AND c.relname = t.tablename),
        0
    )                                                   AS approx_row_count
FROM pg_tables t
WHERE t.schemaname = '{schema}'
ORDER BY total_bytes DESC;

-- ── Total Schema Storage ─────────────────────────────────────────────────────
SELECT
    '{schema}'                                          AS schema_name,
    pg_size_pretty(
        SUM(
            pg_total_relation_size(
                quote_ident('{schema}') || '.' || quote_ident(t.tablename)
            )
        )
    )                                                   AS total_schema_size,
    COUNT(*)                                            AS table_count
FROM pg_tables t
WHERE t.schemaname = '{schema}';

-- ── Compute Estimates by Job Type (pipeline duration as proxy) ───────────────
SELECT
    COALESCE(pr.triggered_by, 'system')                 AS job_type,
    COUNT(*)                                            AS run_count,
    COALESCE(ROUND(SUM(pr.duration_seconds)::NUMERIC, 2), 0) AS total_compute_seconds,
    COALESCE(ROUND(AVG(pr.duration_seconds)::NUMERIC, 2), 0) AS avg_duration_s
FROM {schema}.pipeline_runs pr
WHERE pr.duration_seconds IS NOT NULL
  AND pr.started_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY COALESCE(pr.triggered_by, 'system')
ORDER BY total_compute_seconds DESC;

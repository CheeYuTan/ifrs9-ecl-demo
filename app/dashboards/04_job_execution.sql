-- Dashboard: Job Execution
-- Source: pipeline_runs
-- Metrics: pipeline run counts, success/failure rates, durations

-- ── Pipeline Runs Over Time ──────────────────────────────────────────────────
SELECT
    DATE_TRUNC('day', pr.started_at)::DATE AS run_date,
    COUNT(*)                               AS total_runs,
    COUNT(*) FILTER (WHERE pr.status = 'completed') AS completed,
    COUNT(*) FILTER (WHERE pr.status = 'failed')    AS failed,
    COUNT(*) FILTER (WHERE pr.status = 'running')   AS running
FROM {schema}.pipeline_runs pr
WHERE pr.started_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', pr.started_at)
ORDER BY run_date;

-- ── Success / Failure Rate ───────────────────────────────────────────────────
SELECT
    COALESCE(pr.status, 'unknown') AS run_status,
    COUNT(*)                       AS run_count,
    COALESCE(
        ROUND(
            100.0 * COUNT(*)
            / NULLIF((SELECT COUNT(*) FROM {schema}.pipeline_runs), 0),
            1
        ), 0
    )                              AS pct_of_total
FROM {schema}.pipeline_runs pr
GROUP BY COALESCE(pr.status, 'unknown')
ORDER BY run_count DESC;

-- ── Average Pipeline Duration (seconds, by status) ──────────────────────────
SELECT
    COALESCE(pr.status, 'unknown')                        AS run_status,
    COUNT(*)                                              AS run_count,
    COALESCE(ROUND(AVG(pr.duration_seconds)::NUMERIC, 2), 0)  AS avg_duration_s,
    COALESCE(ROUND(MIN(pr.duration_seconds)::NUMERIC, 2), 0)  AS min_duration_s,
    COALESCE(ROUND(MAX(pr.duration_seconds)::NUMERIC, 2), 0)  AS max_duration_s
FROM {schema}.pipeline_runs pr
WHERE pr.duration_seconds IS NOT NULL
GROUP BY COALESCE(pr.status, 'unknown')
ORDER BY avg_duration_s DESC;

-- ── Recent Pipeline Runs ─────────────────────────────────────────────────────
SELECT
    pr.run_id,
    pr.project_id,
    pr.status,
    pr.started_at,
    pr.completed_at,
    COALESCE(ROUND(pr.duration_seconds::NUMERIC, 2), 0) AS duration_s,
    pr.triggered_by,
    pr.error_message
FROM {schema}.pipeline_runs pr
ORDER BY pr.started_at DESC
LIMIT 20;

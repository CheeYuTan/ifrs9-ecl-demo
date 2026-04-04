-- Dashboard: System Health
-- Source: app_usage_analytics
-- Metrics: error rate trends, latency trends, requests per minute

-- ── Hourly Error Rate Trend (last 7 days) ────────────────────────────────────
SELECT
    DATE_TRUNC('hour', a.timestamp)                     AS hour_bucket,
    COUNT(*)                                            AS total_requests,
    COUNT(*) FILTER (WHERE a.status_code >= 400)        AS error_count,
    COALESCE(
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE a.status_code >= 400)
            / NULLIF(COUNT(*), 0),
            2
        ), 0
    )                                                   AS error_rate_pct
FROM {schema}.app_usage_analytics a
WHERE a.timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', a.timestamp)
ORDER BY hour_bucket;

-- ── Hourly Latency Trend (p50, p95, last 7 days) ────────────────────────────
SELECT
    DATE_TRUNC('hour', a.timestamp)                     AS hour_bucket,
    COALESCE(ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY a.duration_ms)::NUMERIC, 2), 0) AS p50_ms,
    COALESCE(ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY a.duration_ms)::NUMERIC, 2), 0) AS p95_ms,
    COALESCE(ROUND(AVG(a.duration_ms)::NUMERIC, 2), 0)  AS avg_ms
FROM {schema}.app_usage_analytics a
WHERE a.timestamp >= CURRENT_DATE - INTERVAL '7 days'
  AND a.duration_ms IS NOT NULL
GROUP BY DATE_TRUNC('hour', a.timestamp)
ORDER BY hour_bucket;

-- ── Requests per Minute (last 1 hour) ────────────────────────────────────────
SELECT
    DATE_TRUNC('minute', a.timestamp)  AS minute_bucket,
    COUNT(*)                           AS requests_per_minute
FROM {schema}.app_usage_analytics a
WHERE a.timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY DATE_TRUNC('minute', a.timestamp)
ORDER BY minute_bucket;

-- ── Status Code Distribution (last 7 days) ──────────────────────────────────
SELECT
    a.status_code,
    COUNT(*)                                            AS request_count,
    COALESCE(
        ROUND(
            100.0 * COUNT(*)
            / NULLIF(
                (SELECT COUNT(*) FROM {schema}.app_usage_analytics
                 WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'), 0
            ),
            2
        ), 0
    )                                                   AS pct_of_total
FROM {schema}.app_usage_analytics a
WHERE a.timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY a.status_code
ORDER BY request_count DESC;

-- Dashboard: API Usage
-- Source: app_usage_analytics
-- Metrics: endpoint popularity, p50/p95 latency, error rates

-- ── Endpoint Popularity (last 30 days) ───────────────────────────────────────
SELECT
    a.endpoint,
    a.method,
    COUNT(*)                                           AS request_count,
    COUNT(DISTINCT a.user_id)                          AS unique_users,
    COALESCE(ROUND(AVG(a.duration_ms)::NUMERIC, 2), 0) AS avg_ms
FROM {schema}.app_usage_analytics a
WHERE a.timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY a.endpoint, a.method
ORDER BY request_count DESC
LIMIT 50;

-- ── Latency Percentiles by Endpoint (p50, p95, p99) ─────────────────────────
SELECT
    a.endpoint,
    COUNT(*)                                                            AS requests,
    COALESCE(ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY a.duration_ms)::NUMERIC, 2), 0) AS p50_ms,
    COALESCE(ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY a.duration_ms)::NUMERIC, 2), 0) AS p95_ms,
    COALESCE(ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY a.duration_ms)::NUMERIC, 2), 0) AS p99_ms
FROM {schema}.app_usage_analytics a
WHERE a.timestamp >= CURRENT_DATE - INTERVAL '30 days'
  AND a.duration_ms IS NOT NULL
GROUP BY a.endpoint
HAVING COUNT(*) >= 5
ORDER BY p95_ms DESC;

-- ── Error Rate by Endpoint (last 30 days) ────────────────────────────────────
SELECT
    a.endpoint,
    COUNT(*)                                              AS total_requests,
    COUNT(*) FILTER (WHERE a.status_code >= 400)          AS error_count,
    COALESCE(
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE a.status_code >= 400)
            / NULLIF(COUNT(*), 0),
            2
        ), 0
    )                                                     AS error_rate_pct
FROM {schema}.app_usage_analytics a
WHERE a.timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY a.endpoint
ORDER BY error_rate_pct DESC;

-- ── Hourly Request Volume (last 7 days) ──────────────────────────────────────
SELECT
    DATE_TRUNC('hour', a.timestamp)  AS request_hour,
    COUNT(*)                         AS request_count,
    COUNT(*) FILTER (WHERE a.status_code >= 400) AS error_count
FROM {schema}.app_usage_analytics a
WHERE a.timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', a.timestamp)
ORDER BY request_hour;

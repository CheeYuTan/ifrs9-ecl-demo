-- Dashboard: User Activity
-- Sources: audit_trail, app_usage_analytics
-- Metrics: DAU, actions per user, login frequency, top users

-- ── Daily Active Users (last 30 days) ────────────────────────────────────────
SELECT
    DATE_TRUNC('day', a.timestamp)::DATE  AS activity_date,
    COUNT(DISTINCT a.user_id)             AS daily_active_users,
    COUNT(*)                              AS total_requests
FROM {schema}.app_usage_analytics a
WHERE a.timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', a.timestamp)
ORDER BY activity_date;

-- ── Actions per User (last 30 days) ──────────────────────────────────────────
SELECT
    COALESCE(a.user_id, 'anonymous')       AS user_id,
    COUNT(*)                               AS request_count,
    COALESCE(ROUND(AVG(a.duration_ms)::NUMERIC, 2), 0) AS avg_duration_ms,
    COUNT(DISTINCT DATE_TRUNC('day', a.timestamp)) AS active_days
FROM {schema}.app_usage_analytics a
WHERE a.timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY COALESCE(a.user_id, 'anonymous')
ORDER BY request_count DESC
LIMIT 50;

-- ── Audit Trail Activity by Event Type (last 30 days) ────────────────────────
SELECT
    DATE_TRUNC('day', at.created_at)::DATE AS activity_date,
    at.event_type,
    COUNT(*)                               AS event_count
FROM {schema}.audit_trail at
WHERE at.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', at.created_at), at.event_type
ORDER BY activity_date, event_count DESC;

-- ── Login Frequency (distinct users per day, last 30 days) ───────────────────
SELECT
    DATE_TRUNC('day', a.timestamp)::DATE  AS login_date,
    COUNT(DISTINCT a.user_id)             AS unique_users
FROM {schema}.app_usage_analytics a
WHERE a.timestamp >= CURRENT_DATE - INTERVAL '30 days'
  AND a.user_id IS NOT NULL
  AND a.user_id != ''
GROUP BY DATE_TRUNC('day', a.timestamp)
ORDER BY login_date;

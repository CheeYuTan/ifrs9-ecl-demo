-- Dashboard: Project Analytics
-- Source: ecl_workflow
-- Metrics: projects over time, status distribution, completion rates

-- ── Projects Created Over Time ───────────────────────────────────────────────
SELECT
    DATE_TRUNC('month', w.created_at)::DATE AS created_month,
    COUNT(*)                                AS projects_created
FROM {schema}.ecl_workflow w
GROUP BY DATE_TRUNC('month', w.created_at)
ORDER BY created_month;

-- ── Project Status Distribution ──────────────────────────────────────────────
SELECT
    COALESCE(w.step_status, 'unknown')    AS status,
    COUNT(*)                              AS project_count,
    ROUND(
        100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM {schema}.ecl_workflow), 0),
        1
    )                                     AS pct_of_total
FROM {schema}.ecl_workflow w
GROUP BY COALESCE(w.step_status, 'unknown')
ORDER BY project_count DESC;

-- ── Completion Rate (projects that reached sign-off) ─────────────────────────
SELECT
    COUNT(*) FILTER (WHERE w.signed_off_at IS NOT NULL) AS completed_projects,
    COUNT(*)                                            AS total_projects,
    COALESCE(
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE w.signed_off_at IS NOT NULL)
            / NULLIF(COUNT(*), 0),
            1
        ), 0
    )                                                   AS completion_rate_pct
FROM {schema}.ecl_workflow w;

-- ── Project Type Distribution ────────────────────────────────────────────────
SELECT
    COALESCE(w.project_type, 'unspecified') AS project_type,
    COUNT(*)                                AS project_count
FROM {schema}.ecl_workflow w
GROUP BY COALESCE(w.project_type, 'unspecified')
ORDER BY project_count DESC;

-- ── Average Time to Completion (days) ────────────────────────────────────────
SELECT
    COALESCE(
        ROUND(
            AVG(
                EXTRACT(EPOCH FROM (w.signed_off_at - w.created_at)) / 86400.0
            )::NUMERIC, 1
        ), 0
    ) AS avg_days_to_completion
FROM {schema}.ecl_workflow w
WHERE w.signed_off_at IS NOT NULL;

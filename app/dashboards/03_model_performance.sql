-- Dashboard: Model Performance
-- Sources: backtest_metrics, model_registry
-- Metrics: AUC/Gini/KS trends, model registry status

-- ── Model Discrimination Metrics Over Time ───────────────────────────────────
SELECT
    DATE_TRUNC('month', bm.created_at)::DATE AS metric_month,
    bm.model_name,
    COALESCE(ROUND(AVG(bm.auc)::NUMERIC, 4), 0)  AS avg_auc,
    COALESCE(ROUND(AVG(bm.gini)::NUMERIC, 4), 0)  AS avg_gini,
    COALESCE(ROUND(AVG(bm.ks)::NUMERIC, 4), 0)    AS avg_ks,
    COUNT(*)                                        AS backtest_count
FROM {schema}.backtest_metrics bm
GROUP BY DATE_TRUNC('month', bm.created_at), bm.model_name
ORDER BY metric_month, bm.model_name;

-- ── Latest Metrics per Model ─────────────────────────────────────────────────
SELECT DISTINCT ON (bm.model_name)
    bm.model_name,
    COALESCE(ROUND(bm.auc::NUMERIC, 4), 0) AS latest_auc,
    COALESCE(ROUND(bm.gini::NUMERIC, 4), 0) AS latest_gini,
    COALESCE(ROUND(bm.ks::NUMERIC, 4), 0)   AS latest_ks,
    bm.created_at                            AS last_backtest_at
FROM {schema}.backtest_metrics bm
ORDER BY bm.model_name, bm.created_at DESC;

-- ── Model Registry Status Distribution ───────────────────────────────────────
SELECT
    COALESCE(mr.status, 'unknown') AS model_status,
    COUNT(*)                       AS model_count
FROM {schema}.model_registry mr
GROUP BY COALESCE(mr.status, 'unknown')
ORDER BY model_count DESC;

-- ── Champion Models ──────────────────────────────────────────────────────────
SELECT
    mr.model_id,
    mr.model_name,
    mr.model_type,
    mr.algorithm,
    mr.version,
    mr.status,
    mr.created_at,
    mr.promoted_at
FROM {schema}.model_registry mr
WHERE mr.is_champion = TRUE
ORDER BY mr.promoted_at DESC NULLS LAST;

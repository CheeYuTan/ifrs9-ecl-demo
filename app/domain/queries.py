import pandas as pd
from db.pool import _t, query_df
from utils.cache import cached

DATA_TTL = 30  # seconds — dashboard read-heavy queries


@cached(ttl=DATA_TTL, prefix="queries:portfolio_summary")
def get_portfolio_summary() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND((AVG(effective_interest_rate) * 100)::numeric, 2) as avg_eir_pct,
               ROUND(AVG(days_past_due)::numeric, 1) as avg_dpd,
               ROUND((AVG(current_lifetime_pd) * 100)::numeric, 2) as avg_pd_pct,
               SUM(CASE WHEN assessed_stage = 1 THEN 1 ELSE 0 END) as stage_1_count,
               SUM(CASE WHEN assessed_stage = 2 THEN 1 ELSE 0 END) as stage_2_count,
               SUM(CASE WHEN assessed_stage = 3 THEN 1 ELSE 0 END) as stage_3_count
        FROM {_t("model_ready_loans")}
        GROUP BY product_type
        ORDER BY total_gca DESC
    """)


@cached(ttl=DATA_TTL, prefix="queries:stage_distribution")
def get_stage_distribution() -> pd.DataFrame:
    return query_df(f"""
        SELECT assessed_stage,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca
        FROM {_t("model_ready_loans")}
        GROUP BY assessed_stage
        ORDER BY assessed_stage
    """)


@cached(ttl=DATA_TTL, prefix="queries:borrower_segments")
def get_borrower_segment_stats() -> pd.DataFrame:
    return query_df(f"""
        SELECT segment,
               COUNT(DISTINCT borrower_id) as borrower_count,
               ROUND(AVG(credit_score)::numeric, 1) as avg_alt_score,
               ROUND(AVG(annual_income)::numeric, 2) as avg_monthly_income,
               ROUND(AVG(age)::numeric, 1) as avg_age
        FROM {_t("borrower_master")}
        GROUP BY segment
    """)


@cached(ttl=DATA_TTL, prefix="queries:vintage_analysis")
def get_vintage_analysis() -> pd.DataFrame:
    return query_df(f"""
        SELECT vintage_cohort,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND((AVG(current_lifetime_pd) * 100)::numeric, 2) as avg_pd_pct,
               SUM(CASE WHEN assessed_stage >= 2 THEN 1 ELSE 0 END) as stage_2_3_count
        FROM {_t("model_ready_loans")}
        GROUP BY vintage_cohort
        ORDER BY vintage_cohort
    """)


@cached(ttl=DATA_TTL, prefix="queries:dpd_distribution")
def get_dpd_distribution() -> pd.DataFrame:
    return query_df(f"""
        SELECT dpd_bucket, loan_count, total_gca FROM (
            SELECT
                CASE
                    WHEN days_past_due = 0 THEN 'Current'
                    WHEN days_past_due BETWEEN 1 AND 30 THEN '1-30 DPD'
                    WHEN days_past_due BETWEEN 31 AND 60 THEN '31-60 DPD'
                    WHEN days_past_due BETWEEN 61 AND 90 THEN '61-90 DPD'
                    ELSE '90+ DPD'
                END as dpd_bucket,
                CASE
                    WHEN days_past_due = 0 THEN 1
                    WHEN days_past_due BETWEEN 1 AND 30 THEN 2
                    WHEN days_past_due BETWEEN 31 AND 60 THEN 3
                    WHEN days_past_due BETWEEN 61 AND 90 THEN 4
                    ELSE 5
                END as sort_order,
                COUNT(*) as loan_count,
                ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca
            FROM {_t("model_ready_loans")}
            GROUP BY 1, 2
        ) sub
        ORDER BY sort_order
    """)


@cached(ttl=DATA_TTL, prefix="queries:stage_by_product")
def get_stage_by_product() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, assessed_stage,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca
        FROM {_t("model_ready_loans")}
        GROUP BY product_type, assessed_stage
        ORDER BY product_type, assessed_stage
    """)


@cached(ttl=DATA_TTL, prefix="queries:pd_distribution")
def get_pd_distribution() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type,
               ROUND((AVG(current_lifetime_pd) * 100)::numeric, 2) as avg_pd_pct,
               ROUND((MIN(current_lifetime_pd) * 100)::numeric, 2) as min_pd_pct,
               ROUND((MAX(current_lifetime_pd) * 100)::numeric, 2) as max_pd_pct,
               ROUND((PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY current_lifetime_pd) * 100)::numeric, 2) as p25_pd_pct,
               ROUND((PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY current_lifetime_pd) * 100)::numeric, 2) as p75_pd_pct
        FROM {_t("model_ready_loans")}
        GROUP BY product_type
        ORDER BY avg_pd_pct DESC
    """)


@cached(ttl=DATA_TTL, prefix="queries:dq_results")
def get_dq_results() -> pd.DataFrame:
    return query_df(f"""
        SELECT check_id, category, description, severity,
               failures, total_records, failure_pct, passed
        FROM {_t("dq_results")}
        ORDER BY passed ASC, severity DESC
    """)


@cached(ttl=DATA_TTL, prefix="queries:dq_summary")
def get_dq_summary() -> pd.DataFrame:
    return query_df(f"""
        SELECT category,
               COUNT(*) as total_checks,
               SUM(CASE WHEN passed THEN 1 ELSE 0 END) as passed_count,
               SUM(CASE WHEN NOT passed THEN 1 ELSE 0 END) as failed_count
        FROM {_t("dq_results")}
        GROUP BY category
        ORDER BY failed_count DESC
    """)


@cached(ttl=DATA_TTL, prefix="queries:gl_reconciliation")
def get_gl_reconciliation() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, gl_balance, loan_tape_balance,
               variance, variance_pct, status
        FROM {_t("gl_reconciliation")}
    """)


@cached(ttl=DATA_TTL, prefix="queries:ecl_summary")
def get_ecl_summary() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, assessed_stage,
               loan_count, total_gca, total_ecl, coverage_ratio
        FROM {_t("portfolio_ecl_summary")}
        ORDER BY product_type, assessed_stage
    """)


@cached(ttl=DATA_TTL, prefix="queries:ecl_by_product")
def get_ecl_by_product() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type,
               SUM(loan_count) as loan_count,
               ROUND(SUM(total_gca)::numeric, 2) as total_gca,
               ROUND(SUM(total_ecl)::numeric, 2) as total_ecl,
               ROUND((SUM(total_ecl) / NULLIF(SUM(total_gca), 0) * 100)::numeric, 2) as coverage_ratio
        FROM {_t("portfolio_ecl_summary")}
        GROUP BY product_type
        ORDER BY total_ecl DESC
    """)


@cached(ttl=DATA_TTL, prefix="queries:scenario_summary")
def get_scenario_summary() -> pd.DataFrame:
    return query_df(f"""
        SELECT scenario, weight, total_ecl,
               COALESCE(total_ecl_p95, total_ecl) as total_ecl_p95,
               COALESCE(total_ecl_p99, total_ecl) as total_ecl_p99,
               weighted_contribution as weighted
        FROM {_t("scenario_ecl_summary")}
        ORDER BY weight DESC
    """)


@cached(ttl=DATA_TTL, prefix="queries:mc_distribution")
def get_mc_distribution() -> pd.DataFrame:
    return query_df(f"""
        SELECT scenario, weight, ecl_mean, ecl_p50, ecl_p75, ecl_p95, ecl_p99, n_simulations
        FROM {_t("mc_ecl_distribution")}
        ORDER BY weight DESC
    """)


@cached(ttl=DATA_TTL, prefix="queries:ecl_by_scenario_product")
def get_ecl_by_scenario_product() -> pd.DataFrame:
    return query_df(f"""
        SELECT scenario, product_type,
               ROUND(SUM(ecl_amount)::numeric, 2) as total_ecl,
               COUNT(*) as loan_count
        FROM {_t("loan_level_ecl")}
        GROUP BY scenario, product_type
        ORDER BY scenario, product_type
    """)


@cached(ttl=DATA_TTL, prefix="queries:ecl_concentration")
def get_ecl_concentration() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, assessed_stage,
               COUNT(*) as loan_count,
               ROUND(SUM(weighted_ecl)::numeric, 2) as total_ecl,
               ROUND(AVG(weighted_ecl)::numeric, 2) as avg_ecl,
               ROUND(MAX(weighted_ecl)::numeric, 2) as max_ecl
        FROM {_t("loan_ecl_weighted")}
        GROUP BY product_type, assessed_stage
        ORDER BY total_ecl DESC
    """)


@cached(ttl=DATA_TTL, prefix="queries:stage_migration")
def get_stage_migration() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, original_stage, assessed_stage,
               loan_count, ROUND(total_gca::numeric, 2) as total_gca
        FROM {_t("ifrs7_stage_migration")}
        ORDER BY product_type, original_stage, assessed_stage
    """)


@cached(ttl=DATA_TTL, prefix="queries:credit_risk_exposure")
def get_credit_risk_exposure() -> pd.DataFrame:
    return query_df(f"""
        SELECT product_type, assessed_stage, credit_risk_grade,
               loan_count, ROUND(total_gca::numeric, 2) as total_gca
        FROM {_t("ifrs7_credit_risk_exposure")}
        ORDER BY product_type, assessed_stage, credit_risk_grade
    """)


@cached(ttl=DATA_TTL, prefix="queries:loss_allowance_by_stage")
def get_loss_allowance_by_stage() -> pd.DataFrame:
    return query_df(f"""
        SELECT assessed_stage,
               SUM(loan_count) as loan_count,
               ROUND(SUM(total_gca)::numeric, 2) as total_gca,
               ROUND(SUM(total_ecl)::numeric, 2) as total_ecl,
               ROUND((SUM(total_ecl) / NULLIF(SUM(total_gca), 0) * 100)::numeric, 2) as coverage_pct
        FROM {_t("portfolio_ecl_summary")}
        GROUP BY assessed_stage
        ORDER BY assessed_stage
    """)


@cached(ttl=DATA_TTL, prefix="queries:ecl_by_stage_product")
def get_ecl_by_stage_product(stage: int) -> pd.DataFrame:
    return query_df(
        f"""
        SELECT product_type,
               SUM(loan_count) as loan_count,
               ROUND(SUM(total_gca)::numeric, 2) as total_gca,
               ROUND(SUM(total_ecl)::numeric, 2) as total_ecl,
               ROUND((SUM(total_ecl) / NULLIF(SUM(total_gca), 0) * 100)::numeric, 2) as coverage_pct
        FROM {_t("portfolio_ecl_summary")}
        WHERE assessed_stage = %s
        GROUP BY product_type
        ORDER BY total_ecl DESC
    """,
        (stage,),
    )


@cached(ttl=DATA_TTL, prefix="queries:ecl_by_scenario_product_detail")
def get_ecl_by_scenario_product_detail(scenario: str) -> pd.DataFrame:
    return query_df(
        f"""
        SELECT product_type,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(SUM(ecl_amount)::numeric, 2) as total_ecl,
               ROUND(AVG(ecl_amount)::numeric, 2) as avg_ecl
        FROM {_t("loan_level_ecl")}
        WHERE scenario = %s
        GROUP BY product_type
        ORDER BY total_ecl DESC
    """,
        (scenario,),
    )


@cached(ttl=DATA_TTL, prefix="queries:top_exposures")
def get_top_exposures(limit: int = 20) -> pd.DataFrame:
    return query_df(
        f"""
        SELECT l.loan_id, l.product_type, l.assessed_stage,
               ROUND(l.gross_carrying_amount::numeric, 2) as gca,
               ROUND(e.weighted_ecl::numeric, 2) as ecl,
               ROUND((e.weighted_ecl / NULLIF(l.gross_carrying_amount, 0) * 100)::numeric, 2) as coverage_pct,
               l.days_past_due, l.segment,
               ROUND((l.current_lifetime_pd * 100)::numeric, 2) as pd_pct
        FROM {_t("model_ready_loans")} l
        JOIN {_t("loan_ecl_weighted")} e ON l.loan_id = e.loan_id
        ORDER BY e.weighted_ecl DESC
        LIMIT %s
    """,
        (limit,),
    )


@cached(ttl=DATA_TTL, prefix="queries:loans_by_product")
def get_loans_by_product(product_type: str) -> pd.DataFrame:
    return query_df(
        f"""
        SELECT l.loan_id, l.assessed_stage,
               ROUND(l.gross_carrying_amount::numeric, 2) as gca,
               l.days_past_due,
               ROUND((l.current_lifetime_pd * 100)::numeric, 2) as pd_pct,
               ROUND(e.weighted_ecl::numeric, 2) as ecl,
               l.segment
        FROM {_t("model_ready_loans")} l
        JOIN {_t("loan_ecl_weighted")} e ON l.loan_id = e.loan_id
        WHERE l.product_type = %s
        ORDER BY e.weighted_ecl DESC
        LIMIT 50
    """,
        (product_type,),
    )


@cached(ttl=DATA_TTL, prefix="queries:loans_by_stage")
def get_loans_by_stage(stage: int) -> pd.DataFrame:
    return query_df(
        f"""
        SELECT l.loan_id, l.product_type, l.assessed_stage,
               ROUND(l.gross_carrying_amount::numeric, 2) as gca,
               l.days_past_due,
               ROUND((l.current_lifetime_pd * 100)::numeric, 2) as pd_pct,
               ROUND(e.weighted_ecl::numeric, 2) as ecl,
               l.segment
        FROM {_t("model_ready_loans")} l
        JOIN {_t("loan_ecl_weighted")} e ON l.loan_id = e.loan_id
        WHERE l.assessed_stage = %s
        ORDER BY e.weighted_ecl DESC
        LIMIT 50
    """,
        (stage,),
    )


@cached(ttl=DATA_TTL, prefix="queries:scenario_ecl_by_product")
def get_scenario_ecl_by_product(scenario: str) -> pd.DataFrame:
    return query_df(
        f"""
        SELECT product_type,
               COUNT(*) as loan_count,
               ROUND(SUM(ecl_amount)::numeric, 2) as total_ecl,
               ROUND(AVG(ecl_amount)::numeric, 2) as avg_ecl
        FROM {_t("loan_level_ecl")}
        WHERE scenario = %s
        GROUP BY product_type
        ORDER BY total_ecl DESC
    """,
        (scenario,),
    )


@cached(ttl=DATA_TTL, prefix="queries:sensitivity_data")
def get_sensitivity_data() -> pd.DataFrame:
    """Get base ECL data per product for client-side sensitivity simulation."""
    return query_df(f"""
        SELECT l.product_type,
               COUNT(*) as loan_count,
               ROUND(SUM(l.gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(AVG(l.current_lifetime_pd)::numeric, 6) as avg_pd,
               ROUND(AVG(e.weighted_ecl / NULLIF(l.gross_carrying_amount * l.current_lifetime_pd, 0))::numeric, 6) as implied_lgd,
               ROUND(SUM(e.weighted_ecl)::numeric, 2) as base_ecl
        FROM {_t("model_ready_loans")} l
        JOIN {_t("loan_ecl_weighted")} e ON l.loan_id = e.loan_id
        GROUP BY l.product_type
        ORDER BY base_ecl DESC
    """)


@cached(ttl=DATA_TTL, prefix="queries:scenario_comparison")
def get_scenario_comparison() -> pd.DataFrame:
    """Get ECL by scenario and product for comparison."""
    return query_df(f"""
        SELECT scenario, product_type,
               COUNT(*) as loan_count,
               ROUND(SUM(ecl_amount)::numeric, 2) as total_ecl
        FROM {_t("loan_level_ecl")}
        GROUP BY scenario, product_type
        ORDER BY scenario, total_ecl DESC
    """)


@cached(ttl=DATA_TTL, prefix="queries:stress_by_stage")
def get_stress_by_stage() -> pd.DataFrame:
    """Get ECL and PD by stage for stress testing."""
    return query_df(f"""
        SELECT l.assessed_stage,
               COUNT(*) as loan_count,
               ROUND(SUM(l.gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(AVG(l.current_lifetime_pd)::numeric, 6) as avg_pd,
               ROUND(SUM(e.weighted_ecl)::numeric, 2) as base_ecl
        FROM {_t("model_ready_loans")} l
        JOIN {_t("loan_ecl_weighted")} e ON l.loan_id = e.loan_id
        GROUP BY l.assessed_stage
        ORDER BY l.assessed_stage
    """)


@cached(ttl=DATA_TTL, prefix="queries:vintage_performance")
def get_vintage_performance() -> pd.DataFrame:
    """Get vintage cohort performance with delinquency rates."""
    return query_df(f"""
        SELECT vintage_cohort,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND((AVG(current_lifetime_pd) * 100)::numeric, 2) as avg_pd_pct,
               ROUND((SUM(CASE WHEN days_past_due > 0 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100)::numeric, 2) as delinquency_rate,
               ROUND((SUM(CASE WHEN days_past_due > 30 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100)::numeric, 2) as dpd30_rate,
               ROUND((SUM(CASE WHEN days_past_due > 60 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100)::numeric, 2) as dpd60_rate,
               ROUND((SUM(CASE WHEN days_past_due > 90 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100)::numeric, 2) as dpd90_rate,
               SUM(CASE WHEN assessed_stage = 1 THEN 1 ELSE 0 END) as stage1,
               SUM(CASE WHEN assessed_stage = 2 THEN 1 ELSE 0 END) as stage2,
               SUM(CASE WHEN assessed_stage = 3 THEN 1 ELSE 0 END) as stage3
        FROM {_t("model_ready_loans")}
        GROUP BY vintage_cohort
        ORDER BY vintage_cohort
    """)


@cached(ttl=DATA_TTL, prefix="queries:vintage_by_product")
def get_vintage_by_product() -> pd.DataFrame:
    """Get vintage performance broken down by product."""
    return query_df(f"""
        SELECT vintage_cohort, product_type,
               COUNT(*) as loan_count,
               ROUND(SUM(gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND((AVG(current_lifetime_pd) * 100)::numeric, 2) as avg_pd_pct,
               ROUND((SUM(CASE WHEN days_past_due > 30 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100)::numeric, 2) as dpd30_rate
        FROM {_t("model_ready_loans")}
        GROUP BY vintage_cohort, product_type
        ORDER BY vintage_cohort, product_type
    """)


@cached(ttl=DATA_TTL, prefix="queries:concentration_by_segment")
def get_concentration_by_segment() -> pd.DataFrame:
    """Get ECL concentration by borrower segment."""
    return query_df(f"""
        SELECT l.segment,
               COUNT(*) as loan_count,
               ROUND(SUM(l.gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(SUM(e.weighted_ecl)::numeric, 2) as total_ecl,
               ROUND((SUM(e.weighted_ecl) / NULLIF(SUM(l.gross_carrying_amount), 0) * 100)::numeric, 2) as coverage_pct,
               ROUND(MAX(e.weighted_ecl)::numeric, 2) as max_single_ecl
        FROM {_t("model_ready_loans")} l
        JOIN {_t("loan_ecl_weighted")} e ON l.loan_id = e.loan_id
        GROUP BY l.segment
        ORDER BY total_ecl DESC
    """)


@cached(ttl=DATA_TTL, prefix="queries:concentration_by_product_stage")
def get_concentration_by_product_stage() -> pd.DataFrame:
    """Get ECL concentration heatmap data: product x stage."""
    return query_df(f"""
        SELECT l.product_type, l.assessed_stage,
               COUNT(*) as loan_count,
               ROUND(SUM(l.gross_carrying_amount)::numeric, 2) as total_gca,
               ROUND(SUM(e.weighted_ecl)::numeric, 2) as total_ecl,
               ROUND((SUM(e.weighted_ecl) / NULLIF(SUM(l.gross_carrying_amount), 0) * 100)::numeric, 2) as coverage_pct
        FROM {_t("model_ready_loans")} l
        JOIN {_t("loan_ecl_weighted")} e ON l.loan_id = e.loan_id
        GROUP BY l.product_type, l.assessed_stage
        ORDER BY l.product_type, l.assessed_stage
    """)


@cached(ttl=DATA_TTL, prefix="queries:top_concentration_risk")
def get_top_concentration_risk() -> pd.DataFrame:
    """Get top single-name concentration risks."""
    return query_df(f"""
        SELECT l.loan_id, l.product_type, l.segment, l.assessed_stage,
               ROUND(l.gross_carrying_amount::numeric, 2) as gca,
               ROUND(e.weighted_ecl::numeric, 2) as ecl,
               ROUND((e.weighted_ecl / NULLIF(l.gross_carrying_amount, 0) * 100)::numeric, 2) as coverage_pct,
               l.days_past_due,
               ROUND((l.current_lifetime_pd * 100)::numeric, 2) as pd_pct
        FROM {_t("model_ready_loans")} l
        JOIN {_t("loan_ecl_weighted")} e ON l.loan_id = e.loan_id
        ORDER BY e.weighted_ecl DESC
        LIMIT 25
    """)

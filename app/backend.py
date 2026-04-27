"""
Lakebase-powered backend for IFRS 9 ECL Application — Compatibility Shim.

This module re-exports all public symbols from the modularized sub-packages
so that existing code using `import backend` continues to work unchanged.

Actual implementations live in:
  - db.pool          — Connection pool, query_df, execute
  - domain.workflow   — Project CRUD, workflow state
  - domain.queries    — Read-only portfolio/ECL queries
  - domain.model_runs — Model run history, satellite queries
  - domain.attribution — ECL waterfall decomposition
  - domain.model_registry — Model governance lifecycle
  - domain.backtesting — Backtest engine, metrics
  - domain.markov     — Transition matrices, forecasting
  - domain.hazard     — Hazard models, survival curves
  - domain.advanced   — Cure rates, CCF, collateral
  - reporting.gl_journals — GL chart, journal generation
  - reporting.reports  — Regulatory report generation
  - governance.rbac   — Users, permissions, approvals
"""

import logging

log = logging.getLogger(__name__)

# ── DB / Pool ──────────────────────────────────────────────────────────────
from db.pool import (  # noqa: F401
    PREFIX,
    SCHEMA,
    TOKEN_REFRESH_INTERVAL,
    _config_loaded,
    _force_reinit,
    _init_pool_via_sdk,
    _is_auth_error,
    _pool,
    _pool_lock,
    _refresh_stop,
    _refresh_thread,
    _reinit_pool,
    _t,
    _token_refresh_loop,
    execute,
    init_pool,
    load_schema_from_config,
    query_df,
)

# ── Workflow / Projects ────────────────────────────────────────────────────
from domain.workflow import (  # noqa: F401
    STEPS,
    WF_TABLE,
    advance_step,
    create_project,
    ensure_workflow_table,
    get_project,
    list_projects,
    reset_project,
    save_overlays,
    save_scenario_weights,
    sign_off_project,
)

# Alias used by routes/setup.py seed endpoint
ensure_tables = ensure_workflow_table

# ── Read-Only Queries ──────────────────────────────────────────────────────
# ── Advanced Features ──────────────────────────────────────────────────────
from domain.advanced import (  # noqa: F401
    CCF_TABLE,
    COLLATERAL_TABLE,
    CURE_RATE_TABLE,
    compute_ccf,
    compute_collateral_haircuts,
    compute_cure_rates,
    ensure_advanced_tables,
    get_ccf_analysis,
    get_collateral_analysis,
    get_cure_analysis,
    list_ccf_analyses,
    list_collateral_analyses,
    list_cure_analyses,
)

# ── Attribution / Waterfall ────────────────────────────────────────────────
from domain.attribution import (  # noqa: F401
    ATTRIBUTION_TABLE,
    MATERIALITY_THRESHOLD,
    _build_waterfall,
    _estimate_opening_ecl,
    _get_prior_attribution,
    _safe_query,
    _stage_dict,
    _stage_val,
    _unavailable,
    compute_attribution,
    ensure_attribution_table,
    get_attribution,
    get_attribution_history,
)

# ── Backtesting ────────────────────────────────────────────────────────────
from domain.backtesting import (  # noqa: F401
    BACKTEST_COHORT_TABLE,
    BACKTEST_METRICS_TABLE,
    BACKTEST_TABLE,
    METRIC_THRESHOLDS,
    MIN_DEFAULTS_FOR_LGD,
    MIN_SAMPLE_SIZE,
    _binomial_test,
    _compute_auc_gini_ks,
    _compute_brier,
    _compute_lgd_backtest,
    _compute_psi,
    _hosmer_lemeshow_test,
    _jeffreys_test,
    _overall_traffic_light,
    _spiegelhalter_test,
    _traffic_light,
    ensure_backtesting_table,
    get_backtest,
    get_backtest_trend,
    list_backtests,
    run_backtest,
)

# ── Hazard Models ──────────────────────────────────────────────────────────
from domain.hazard import (  # noqa: F401
    HAZARD_CURVE_TABLE,
    HAZARD_MODEL_TABLE,
    _build_segment_curves,
    _estimate_cox_ph,
    _estimate_discrete_time,
    _estimate_kaplan_meier,
    _get_portfolio_hazard_data,
    compare_hazard_models,
    compute_survival_curve,
    compute_term_structure_pd,
    ensure_hazard_tables,
    estimate_hazard_model,
    get_hazard_model,
    list_hazard_models,
)

# ── Markov Chains ──────────────────────────────────────────────────────────
from domain.markov import (  # noqa: F401
    _MARKOV_STATES,
    MARKOV_FORECAST_TABLE,
    MARKOV_MATRIX_TABLE,
    _mat_mult,
    _mat_power,
    compare_matrices,
    compute_lifetime_pd,
    ensure_markov_tables,
    estimate_transition_matrix,
    forecast_stage_distribution,
    get_transition_matrix,
    list_transition_matrices,
)

# ── Model Registry ─────────────────────────────────────────────────────────
from domain.model_registry import (  # noqa: F401
    MODEL_REGISTRY_AUDIT_TABLE,
    MODEL_REGISTRY_TABLE,
    VALID_MODEL_STATUSES,
    VALID_MODEL_TYPES,
    VALID_STATUS_TRANSITIONS,
    _log_model_audit,
    _migrate_model_registry_columns,
    _parse_model_rows,
    check_recalibration_due,
    compare_models,
    compute_sensitivity,
    ensure_model_registry_table,
    generate_model_card,
    get_model,
    get_model_audit_trail,
    list_models,
    promote_champion,
    register_model,
    update_model_status,
)

# ── Model Runs / Satellite / Cohort ───────────────────────────────────────
from domain.model_runs import (  # noqa: F401
    MODEL_RUNS_TABLE,
    _detect_available_dimensions,
    ensure_model_runs_table,
    get_active_run_id,
    get_cohort_summary,
    get_cohort_summary_by_product,
    get_drill_down_dimensions,
    get_ecl_by_cohort,
    get_ecl_by_product_drilldown,
    get_model_run,
    get_portfolio_by_cohort,
    get_portfolio_by_dimension,
    get_satellite_model_comparison,
    get_satellite_model_selected,
    get_stage_by_cohort,
    list_model_runs,
    save_model_run,
)

# ── Period-End Close ──────────────────────────────────────────────────────
from domain.period_close import (  # noqa: F401
    PIPELINE_STEPS,
    PIPELINE_TABLE,
    complete_pipeline,
    ensure_pipeline_table,
    execute_step,
    get_pipeline_health,
    get_pipeline_run,
    start_pipeline,
)
from domain.queries import (  # noqa: F401
    get_borrower_segment_stats,
    get_concentration_by_product_stage,
    get_concentration_by_segment,
    get_credit_risk_exposure,
    get_dpd_distribution,
    get_dq_results,
    get_dq_summary,
    get_ecl_by_product,
    get_ecl_by_scenario_product,
    get_ecl_by_scenario_product_detail,
    get_ecl_by_stage_product,
    get_ecl_concentration,
    get_ecl_summary,
    get_gl_reconciliation,
    get_loans_by_product,
    get_loans_by_stage,
    get_loss_allowance_by_stage,
    get_mc_distribution,
    get_pd_distribution,
    get_portfolio_summary,
    get_scenario_comparison,
    get_scenario_ecl_by_product,
    get_scenario_summary,
    get_sensitivity_data,
    get_stage_by_product,
    get_stage_distribution,
    get_stage_migration,
    get_stress_by_stage,
    get_top_concentration_risk,
    get_top_exposures,
    get_vintage_analysis,
    get_vintage_by_product,
    get_vintage_performance,
)

# ── Usage Analytics ────────────────────────────────────────────────────────
from domain.usage_analytics import (  # noqa: F401
    USAGE_TABLE,
    ensure_usage_table,
    get_recent_requests,
    get_usage_stats,
    record_request,
)

# ── Advanced Features ──────────────────────────────────────────────────────
# ── Validation Rules ───────────────────────────────────────────────────────
from domain.validation_rules import (  # noqa: F401
    ValidationResult,
    check_adverse_exceeds_baseline,
    check_convergence_cv,
    check_coverage_monotonic,
    check_data_quality_gate,
    check_ecl_period_change,
    check_eir_positive,
    check_gca_positive,
    check_lgd_range,
    check_overlay_cap,
    check_overlay_has_required_fields,
    check_pd_range,
    check_remaining_months,
    check_scenario_concentration,
    check_scenario_weight_constraints,
    check_scenario_weights_sum,
    check_segregation_of_duties,
    has_critical_failures,
    run_all_post_calculation_checks,
    run_all_pre_calculation_checks,
)

# ── Project Permissions (Layer 2) ─────────────────────────────────────────
from governance.project_permissions import (  # noqa: F401
    PROJECT_MEMBERS_TABLE,
    ROLE_HIERARCHY,
    VALID_PROJECT_ROLES,
    add_project_member,
    check_project_access,
    ensure_project_members_table,
    get_effective_role,
    get_project_member,
    list_project_members,
    remove_project_member,
    role_level,
    transfer_ownership,
)

# ── RBAC & Approvals ──────────────────────────────────────────────────────
from governance.rbac import (  # noqa: F401
    RBAC_APPROVALS_TABLE,
    RBAC_USERS_TABLE,
    ROLE_PERMISSIONS,
    SEED_USERS,
    approve_request,
    check_permission,
    create_approval_request,
    ensure_rbac_tables,
    get_approval_history,
    get_approval_request,
    get_user,
    list_approval_requests,
    list_users,
    reject_request,
)

# ── Auth Middleware ─────────────────────────────────────────────────────────
from middleware.auth import (  # noqa: F401
    ANONYMOUS_USER,
    compute_ecl_hash,
    get_current_user,
    require_permission,
    require_project_not_locked,
    verify_ecl_hash,
)

# ── GL Journals ────────────────────────────────────────────────────────────
from reporting.gl_journals import (  # noqa: F401
    _ECL_EXPENSE_ACCOUNT,
    _GL_SEED_ACCOUNTS,
    _OVERLAY_EXPENSE_ACCOUNT,
    _OVERLAY_PROVISION_ACCOUNT,
    _STAGE_PROVISION_ACCOUNT,
    _WRITEOFF_EXPENSE_ACCOUNT,
    GL_CHART_TABLE,
    GL_JOURNAL_TABLE,
    GL_LINE_TABLE,
    _migrate_gl_tables,
    _seed_gl_chart,
    ensure_gl_tables,
    generate_ecl_journals,
    get_gl_chart,
    get_gl_trial_balance,
    get_journal,
    list_journals,
    post_journal,
    reverse_journal,
)

# ── Regulatory Reports ─────────────────────────────────────────────────────
from reporting.reports import (  # noqa: F401
    REPORT_TABLE,
    _report_id,
    ensure_report_tables,
    export_report_csv,
    finalize_report,
    generate_concentration_report,
    generate_ecl_movement_report,
    generate_ifrs7_disclosure,
    generate_sensitivity_report,
    generate_stage_migration_report,
    get_report,
    list_reports,
)

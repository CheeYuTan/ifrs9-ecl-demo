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
    SCHEMA, PREFIX,
    TOKEN_REFRESH_INTERVAL,
    _pool, _pool_lock, _refresh_thread, _refresh_stop, _config_loaded,
    load_schema_from_config,
    init_pool, _init_pool_via_sdk, _is_auth_error,
    _token_refresh_loop, _force_reinit, _reinit_pool,
    query_df, execute, _t,
)

# ── Workflow / Projects ────────────────────────────────────────────────────
from domain.workflow import (  # noqa: F401
    STEPS, WF_TABLE,
    ensure_workflow_table,
    get_project, list_projects, create_project,
    advance_step, save_overlays, save_scenario_weights,
    reset_project, sign_off_project,
)

# Alias used by routes/setup.py seed endpoint
ensure_tables = ensure_workflow_table

# ── Read-Only Queries ──────────────────────────────────────────────────────
from domain.queries import (  # noqa: F401
    get_portfolio_summary, get_stage_distribution,
    get_borrower_segment_stats, get_vintage_analysis,
    get_dpd_distribution, get_stage_by_product, get_pd_distribution,
    get_dq_results, get_dq_summary, get_gl_reconciliation,
    get_ecl_summary, get_ecl_by_product, get_scenario_summary,
    get_mc_distribution, get_ecl_by_scenario_product,
    get_ecl_concentration, get_stage_migration,
    get_credit_risk_exposure, get_loss_allowance_by_stage,
    get_ecl_by_stage_product, get_ecl_by_scenario_product_detail,
    get_top_exposures, get_loans_by_product, get_loans_by_stage,
    get_scenario_ecl_by_product,
    get_sensitivity_data, get_scenario_comparison, get_stress_by_stage,
    get_vintage_performance, get_vintage_by_product,
    get_concentration_by_segment, get_concentration_by_product_stage,
    get_top_concentration_risk,
)

# ── Model Runs / Satellite / Cohort ───────────────────────────────────────
from domain.model_runs import (  # noqa: F401
    MODEL_RUNS_TABLE,
    ensure_model_runs_table,
    save_model_run, get_model_run, list_model_runs, get_active_run_id,
    get_satellite_model_comparison, get_satellite_model_selected,
    get_cohort_summary, get_cohort_summary_by_product,
    get_ecl_by_cohort, get_stage_by_cohort, get_portfolio_by_cohort,
    _detect_available_dimensions, get_drill_down_dimensions,
    get_portfolio_by_dimension, get_ecl_by_product_drilldown,
)

# ── Attribution / Waterfall ────────────────────────────────────────────────
from domain.attribution import (  # noqa: F401
    ATTRIBUTION_TABLE, MATERIALITY_THRESHOLD,
    ensure_attribution_table,
    _stage_val, _stage_dict, _unavailable, _safe_query,
    compute_attribution, _estimate_opening_ecl,
    _get_prior_attribution, _build_waterfall,
    get_attribution, get_attribution_history,
)

# ── Model Registry ─────────────────────────────────────────────────────────
from domain.model_registry import (  # noqa: F401
    MODEL_REGISTRY_TABLE, MODEL_REGISTRY_AUDIT_TABLE,
    VALID_MODEL_STATUSES, VALID_STATUS_TRANSITIONS, VALID_MODEL_TYPES,
    ensure_model_registry_table, _migrate_model_registry_columns,
    register_model, list_models, get_model,
    update_model_status, promote_champion,
    compare_models, get_model_audit_trail,
    _log_model_audit, _parse_model_rows,
    generate_model_card, compute_sensitivity, check_recalibration_due,
)

# ── Backtesting ────────────────────────────────────────────────────────────
from domain.backtesting import (  # noqa: F401
    BACKTEST_TABLE, BACKTEST_METRICS_TABLE, BACKTEST_COHORT_TABLE,
    METRIC_THRESHOLDS, MIN_SAMPLE_SIZE, MIN_DEFAULTS_FOR_LGD,
    ensure_backtesting_table,
    _traffic_light, _overall_traffic_light,
    _compute_auc_gini_ks, _compute_psi, _compute_brier,
    _binomial_test, _jeffreys_test, _hosmer_lemeshow_test,
    _spiegelhalter_test, _compute_lgd_backtest,
    run_backtest, list_backtests, get_backtest, get_backtest_trend,
)

# ── GL Journals ────────────────────────────────────────────────────────────
from reporting.gl_journals import (  # noqa: F401
    GL_CHART_TABLE, GL_JOURNAL_TABLE, GL_LINE_TABLE,
    _GL_SEED_ACCOUNTS, _STAGE_PROVISION_ACCOUNT,
    _ECL_EXPENSE_ACCOUNT, _OVERLAY_PROVISION_ACCOUNT,
    _OVERLAY_EXPENSE_ACCOUNT, _WRITEOFF_EXPENSE_ACCOUNT,
    _migrate_gl_tables, ensure_gl_tables, _seed_gl_chart,
    get_gl_chart, generate_ecl_journals,
    list_journals, get_journal, post_journal,
    reverse_journal, get_gl_trial_balance,
)

# ── Markov Chains ──────────────────────────────────────────────────────────
from domain.markov import (  # noqa: F401
    MARKOV_MATRIX_TABLE, MARKOV_FORECAST_TABLE, _MARKOV_STATES,
    ensure_markov_tables,
    estimate_transition_matrix, get_transition_matrix,
    list_transition_matrices,
    _mat_mult, _mat_power,
    forecast_stage_distribution, compute_lifetime_pd,
    compare_matrices,
)

# ── Hazard Models ──────────────────────────────────────────────────────────
from domain.hazard import (  # noqa: F401
    HAZARD_MODEL_TABLE, HAZARD_CURVE_TABLE,
    ensure_hazard_tables,
    _get_portfolio_hazard_data,
    estimate_hazard_model,
    _estimate_cox_ph, _estimate_discrete_time, _estimate_kaplan_meier,
    _build_segment_curves,
    get_hazard_model, list_hazard_models,
    compute_survival_curve, compute_term_structure_pd,
    compare_hazard_models,
)

# ── Regulatory Reports ─────────────────────────────────────────────────────
from reporting.reports import (  # noqa: F401
    REPORT_TABLE,
    ensure_report_tables, _report_id,
    generate_ifrs7_disclosure, generate_ecl_movement_report,
    generate_stage_migration_report, generate_sensitivity_report,
    generate_concentration_report,
    list_reports, get_report, finalize_report, export_report_csv,
)

# ── RBAC & Approvals ──────────────────────────────────────────────────────
from governance.rbac import (  # noqa: F401
    RBAC_USERS_TABLE, RBAC_APPROVALS_TABLE,
    ROLE_PERMISSIONS, SEED_USERS,
    ensure_rbac_tables,
    list_users, get_user, check_permission,
    create_approval_request, get_approval_request,
    list_approval_requests,
    approve_request, reject_request, get_approval_history,
)

# ── Project Permissions (Layer 2) ─────────────────────────────────────────
from governance.project_permissions import (  # noqa: F401
    PROJECT_MEMBERS_TABLE, VALID_PROJECT_ROLES, ROLE_HIERARCHY,
    role_level,
    ensure_project_members_table,
    get_effective_role, check_project_access,
    get_project_member, list_project_members,
    add_project_member, remove_project_member,
    transfer_ownership,
)

# ── Advanced Features ──────────────────────────────────────────────────────
# ── Validation Rules ───────────────────────────────────────────────────────
from domain.validation_rules import (  # noqa: F401
    ValidationResult,
    check_scenario_weights_sum, check_pd_range, check_lgd_range,
    check_eir_positive, check_remaining_months, check_gca_positive,
    check_coverage_monotonic, check_ecl_period_change, check_convergence_cv,
    check_scenario_concentration, check_adverse_exceeds_baseline,
    check_scenario_weight_constraints,
    check_segregation_of_duties, check_overlay_has_required_fields,
    check_data_quality_gate, check_overlay_cap,
    run_all_pre_calculation_checks, run_all_post_calculation_checks,
    has_critical_failures,
)

# ── Auth Middleware ─────────────────────────────────────────────────────────
from middleware.auth import (  # noqa: F401
    get_current_user, require_permission, require_project_not_locked,
    compute_ecl_hash, verify_ecl_hash,
    ANONYMOUS_USER,
)

# ── Advanced Features ──────────────────────────────────────────────────────
from domain.advanced import (  # noqa: F401
    CURE_RATE_TABLE, CCF_TABLE, COLLATERAL_TABLE,
    ensure_advanced_tables,
    compute_cure_rates, get_cure_analysis, list_cure_analyses,
    compute_ccf, get_ccf_analysis, list_ccf_analyses,
    compute_collateral_haircuts, get_collateral_analysis,
    list_collateral_analyses,
)

# ── Usage Analytics ────────────────────────────────────────────────────────
from domain.usage_analytics import (  # noqa: F401
    USAGE_TABLE,
    ensure_usage_table,
    record_request,
    get_usage_stats,
    get_recent_requests,
)

# ── Period-End Close ──────────────────────────────────────────────────────
from domain.period_close import (  # noqa: F401
    PIPELINE_TABLE, PIPELINE_STEPS,
    ensure_pipeline_table,
    start_pipeline, execute_step, complete_pipeline,
    get_pipeline_run, get_pipeline_health,
)

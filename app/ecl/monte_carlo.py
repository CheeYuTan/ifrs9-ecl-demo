"""
ECL Engine -- low-level Monte Carlo batch loop and data preparation.
"""

import numpy as np
import pandas as pd


def prepare_loan_columns(loans_df: pd.DataFrame, base_lgd: dict) -> pd.DataFrame:
    """Add derived columns needed by the simulation loop."""
    loans_df = loans_df.dropna(subset=["assessed_stage", "remaining_months", "gross_carrying_amount"]).copy()
    loans_df["stage"] = loans_df["assessed_stage"].fillna(1).astype(int)
    loans_df["gca"] = loans_df["gross_carrying_amount"].astype(float)
    eir_raw = loans_df["effective_interest_rate"].fillna(0.0).astype(float)
    loans_df["eir"] = eir_raw.clip(lower=0.001)
    assert (loans_df["eir"] >= 0.001).all(), "EIR floor violation after clip"
    # NOTE: Despite the column name "current_lifetime_pd", this is an ANNUALISED
    # point-in-time PD.  Converted to quarterly PD via 1-(1-PD)^0.25 below.
    loans_df["base_pd"] = loans_df["current_lifetime_pd"].fillna(0.0).astype(float).clip(lower=0.0, upper=1.0)
    loans_df["rem_q"] = (loans_df["remaining_months"].fillna(1).astype(int) // 3).clip(lower=1)
    loans_df["rem_months_f"] = loans_df["remaining_months"].fillna(1).astype(float).clip(lower=1)
    loans_df["base_lgd"] = loans_df["product_type"].map(base_lgd).fillna(0.50)
    return loans_df


def run_scenario_sims(
    *,
    rng,
    n_loans,
    n_sims,
    batch_size,
    rho_1d,
    base_pd,
    base_lgd_arr,
    pd_mult,
    lgd_mult,
    pd_vol,
    lgd_vol,
    pd_floor,
    pd_cap,
    lgd_floor,
    lgd_cap,
    aging_factor,
    is_stage_23_1d,
    max_horizon,
    global_max_q,
    quarterly_prepay,
    rem_months_f,
    is_bullet,
    gca,
    eir,
    products,
    unique_products,
    product_sim_ecls,
    w,
):
    """Run batched Monte Carlo sims for a single scenario, return accumulators."""
    loan_ecl_accum = np.zeros(n_loans)
    portfolio_path_ecls = np.zeros(n_sims)
    sims_done = 0

    while sims_done < n_sims:
        batch = min(batch_size, n_sims - sims_done)

        z_pd = rng.standard_normal((n_loans, batch))
        z_lgd_indep = rng.standard_normal((n_loans, batch))

        rho = rho_1d[:, np.newaxis]
        z_lgd = rho * z_pd + np.sqrt(1 - rho**2) * z_lgd_indep

        pd_shocks = np.exp(z_pd * pd_vol - 0.5 * pd_vol**2)
        lgd_shocks = np.exp(z_lgd * lgd_vol - 0.5 * lgd_vol**2)

        stressed_pd = np.clip(base_pd[:, np.newaxis] * pd_mult * pd_shocks, pd_floor, pd_cap)
        stressed_lgd = np.clip(base_lgd_arr[:, np.newaxis] * lgd_mult * lgd_shocks, lgd_floor, lgd_cap)

        ecl_batch = np.zeros((n_loans, batch))
        survival = np.ones((n_loans, batch))

        for q in range(1, global_max_q + 1):
            active = max_horizon >= q
            if not active.any():
                break

            quarterly_base_pd = 1.0 - (1.0 - stressed_pd) ** 0.25
            is_s23 = is_stage_23_1d[:, np.newaxis]
            aging = np.where(is_s23, 1.0 + aging_factor * (q - 1), 1.0)
            q_pd = np.clip(quarterly_base_pd * aging, 0, 0.99)

            default_this_q = survival * q_pd
            prepay_surv = (1.0 - quarterly_prepay[:, np.newaxis]) ** q
            amort = np.maximum(0.0, 1.0 - (q * 3) / rem_months_f[:, np.newaxis])
            ead_q = np.where(
                is_bullet[:, np.newaxis],
                gca[:, np.newaxis],
                gca[:, np.newaxis] * amort * prepay_surv,
            )
            discount = 1.0 / ((1.0 + eir[:, np.newaxis] / 4.0) ** q)

            contribution = default_this_q * stressed_lgd * ead_q * discount
            contribution[~active] = 0.0
            ecl_batch += contribution
            survival *= 1.0 - q_pd

        np.nan_to_num(ecl_batch, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
        np.nan_to_num(survival, copy=False, nan=0.0, posinf=1.0, neginf=0.0)
        loan_ecl_accum += ecl_batch.sum(axis=1)
        portfolio_path_ecls[sims_done : sims_done + batch] = ecl_batch.sum(axis=0)
        for prod in unique_products:
            pmask = products == prod
            product_sim_ecls[prod][sims_done : sims_done + batch] += ecl_batch[pmask].sum(axis=0) * w
        sims_done += batch

    return loan_ecl_accum, portfolio_path_ecls

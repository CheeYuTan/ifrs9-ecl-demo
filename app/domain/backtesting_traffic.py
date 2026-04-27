"""
Traffic light / zone classification for IFRS 9 backtesting metrics.

Implements the EBA/GL/2017/16 traffic light system for PD and LGD backtesting.
Green = acceptable, Amber = borderline, Red = failing.
"""

METRIC_THRESHOLDS = {
    "AUC": {"green": 0.70, "amber": 0.60, "direction": "higher_better"},
    "Gini": {"green": 0.40, "amber": 0.20, "direction": "higher_better"},
    "KS": {"green": 0.30, "amber": 0.15, "direction": "higher_better"},
    "PSI": {"green": 0.10, "amber": 0.25, "direction": "lower_better"},
    "Brier": {"green": 0.15, "amber": 0.25, "direction": "lower_better"},
    "Hosmer_Lemeshow_pvalue": {"green": 0.05, "amber": 0.01, "direction": "higher_better"},
    "Binomial_pass_rate": {"green": 0.80, "amber": 0.60, "direction": "higher_better"},
    "MAE": {"green": 0.10, "amber": 0.20, "direction": "lower_better"},
    "RMSE": {"green": 0.15, "amber": 0.25, "direction": "lower_better"},
    "Mean_Bias": {"green": 0.05, "amber": 0.10, "direction": "lower_better"},
    "Median_Bias": {"green": 0.05, "amber": 0.10, "direction": "lower_better"},
}


def _traffic_light(metric_name: str, value: float) -> str:
    """Classify a single metric value as Green, Amber, or Red."""
    t = METRIC_THRESHOLDS.get(metric_name)
    if not t:
        return "Green"
    if t["direction"] == "higher_better":
        if value >= t["green"]:
            return "Green"
        elif value >= t["amber"]:
            return "Amber"
        return "Red"
    else:
        if value <= t["green"]:
            return "Green"
        elif value <= t["amber"]:
            return "Amber"
        return "Red"


def _overall_traffic_light(lights: list[str]) -> str:
    """Aggregate a list of traffic light results into an overall rating."""
    if "Red" in lights:
        return "Red"
    if "Amber" in lights:
        return "Amber"
    return "Green"

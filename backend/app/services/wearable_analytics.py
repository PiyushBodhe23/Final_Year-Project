"""Trends, anomalies, and the Layer B wearable behaviour score.

Targets are the screening cut-offs in config. A higher sub-score means more
concern, from 0 (at the healthy target) to 100 (at the concern cut-off).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from backend.app.core.config import (
    ACTIVE_MIN_WEEK_CONCERN,
    ACTIVE_MIN_WEEK_HEALTHY,
    ANOMALY_CONSECUTIVE_DAYS,
    ANOMALY_Z,
    HRV_DEFICIT_CONCERN,
    HRV_REF_AT_AGE_25,
    HRV_REF_DROP_PER_YEAR,
    HRV_REF_FLOOR,
    PERSONAL_BASELINE_DAYS,
    RHR_CONCERN_MIN,
    RHR_HEALTHY_MAX,
    RHR_SLOPE_CONCERN_BPM_PER_MONTH,
    SLEEP_EFFICIENCY_CONCERN,
    SLEEP_EFFICIENCY_HEALTHY,
    SLEEP_HOURS_CONCERN,
    SLEEP_HOURS_LOW,
    SPO2_NIGHTS_CONCERN,
    SPO2_THRESHOLD,
    STEPS_CONCERN,
    STEPS_HEALTHY,
    WEARABLE_WEIGHTS,
    WEARABLE_WINDOW_DAYS,
)


@dataclass
class MetricTrend:
    """One metric over the scoring window."""

    metric: str
    mean_30: float
    mean_7: float
    slope_per_day: float
    trend: str
    anomaly_dates: list[date]


def concern_linear(value: float, healthy: float, concern: float) -> float:
    """Map a metric onto 0-100 concern.

    If `concern` is above `healthy`, higher readings are worse (resting HR).
    If `concern` is below `healthy`, lower readings are worse (steps, HRV).
    """
    if concern == healthy:
        return 0.0
    if concern > healthy:
        if value <= healthy:
            return 0.0
        if value >= concern:
            return 100.0
        return (value - healthy) / (concern - healthy) * 100.0
    if value >= healthy:
        return 0.0
    if value <= concern:
        return 100.0
    return (healthy - value) / (healthy - concern) * 100.0


def _slope_per_day(values: np.ndarray) -> float:
    """Ordinary least-squares slope. A flat or single-day window has slope 0."""
    if len(values) < 2:
        return 0.0
    return float(np.polyfit(np.arange(len(values)), values, 1)[0])


def _trend(mean_7: float, mean_30: float) -> str:
    """7-day mean versus the 30-day mean. Three percent is the flat band."""
    if mean_30 == 0:
        return "flat"
    if mean_7 > mean_30 * 1.03:
        return "up"
    if mean_7 < mean_30 * 0.97:
        return "down"
    return "flat"


def anomaly_dates(frame: pd.DataFrame, metric: str) -> list[date]:
    """Days where |z| > 2 versus the early-series baseline, in runs of 3 or more.

    The baseline is the median and spread of the first 60 days, so a person
    who has always slept poorly is not flagged every night.
    """
    if metric not in frame.columns or frame.empty:
        return []
    baseline = frame.iloc[: min(PERSONAL_BASELINE_DAYS, len(frame))]
    center = float(baseline[metric].median())
    spread = float(baseline[metric].std(ddof=0))
    if spread < 1e-6:
        return []
    z = (frame[metric].to_numpy(dtype=float) - center) / spread
    hot = np.abs(z) > ANOMALY_Z
    dates = list(frame["date"])
    runs: list[date] = []
    start: int | None = None
    for index, flagged in enumerate(hot):
        if flagged and start is None:
            start = index
        if not flagged and start is not None:
            if index - start >= ANOMALY_CONSECUTIVE_DAYS:
                runs.extend(dates[start:index])
            start = None
    if start is not None and len(hot) - start >= ANOMALY_CONSECUTIVE_DAYS:
        runs.extend(dates[start:])
    return runs


def summarize_metrics(frame: pd.DataFrame, metrics: list[str]) -> list[MetricTrend]:
    """30-day mean, 7-day mean, slope, trend arrow, and anomaly dates."""
    recent = frame.tail(WEARABLE_WINDOW_DAYS)
    trends: list[MetricTrend] = []
    for metric in metrics:
        if metric not in frame.columns or recent.empty:
            continue
        values = recent[metric].to_numpy(dtype=float)
        mean_30 = float(np.nanmean(values))
        mean_7 = float(np.nanmean(values[-7:]))
        trends.append(
            MetricTrend(
                metric=metric,
                mean_30=mean_30,
                mean_7=mean_7,
                slope_per_day=_slope_per_day(values),
                trend=_trend(mean_7, mean_30),
                anomaly_dates=anomaly_dates(frame, metric),
            )
        )
    return trends


def age_adjusted_hrv(age: int) -> float:
    """Rough adult RMSSD reference. About 50 ms at age 25, lower with age."""
    return max(HRV_REF_FLOOR, HRV_REF_AT_AGE_25 - HRV_REF_DROP_PER_YEAR * (age - 25))


def wearable_subscores(frame: pd.DataFrame, age: int) -> dict[str, float]:
    """Five concern sub-scores from the last 30 days.

    Cardio and sleep use the worse of their two inputs because the rule reaches
    100 if either input is past its concern cut-off. Activity averages steps
    and active minutes so both have to be poor to approach 100.
    """
    recent = frame.tail(WEARABLE_WINDOW_DAYS)
    if recent.empty:
        return {name: 0.0 for name in WEARABLE_WEIGHTS}
    steps = float(recent["steps"].mean())
    active_week = float(recent["active_min"].sum()) / max(len(recent), 1) * 7.0
    activity = (
        concern_linear(steps, STEPS_HEALTHY, STEPS_CONCERN)
        + concern_linear(active_week, ACTIVE_MIN_WEEK_HEALTHY, ACTIVE_MIN_WEEK_CONCERN)
    ) / 2.0

    rhr = recent["rhr"].to_numpy(dtype=float)
    rhr_level = concern_linear(float(np.mean(rhr)), RHR_HEALTHY_MAX, RHR_CONCERN_MIN)
    bpm_month = _slope_per_day(rhr) * 30.0
    rhr_slope = concern_linear(max(bpm_month, 0.0), 0.0, RHR_SLOPE_CONCERN_BPM_PER_MONTH)
    cardio = max(rhr_level, rhr_slope)

    early = frame.iloc[: min(PERSONAL_BASELINE_DAYS, len(frame))]
    personal = float(early["hrv_rmssd"].median())
    current_hrv = float(recent["hrv_rmssd"].mean())
    personal_floor = personal * (1.0 - HRV_DEFICIT_CONCERN)
    versus_self = concern_linear(current_hrv, personal, personal_floor)
    reference = age_adjusted_hrv(age)
    versus_age = concern_linear(current_hrv, reference, reference * (1.0 - HRV_DEFICIT_CONCERN))
    recovery = max(versus_self, versus_age)

    sleep_hours = concern_linear(float(recent["sleep_hours"].mean()), SLEEP_HOURS_LOW, SLEEP_HOURS_CONCERN)
    efficiency = concern_linear(
        float(recent["sleep_efficiency"].mean()),
        SLEEP_EFFICIENCY_HEALTHY,
        SLEEP_EFFICIENCY_CONCERN,
    )
    sleep = max(sleep_hours, efficiency)

    low_nights = float((recent["spo2_min"] < SPO2_THRESHOLD).mean())
    oxygen = concern_linear(low_nights, 0.0, SPO2_NIGHTS_CONCERN)
    return {
        "activity": activity,
        "cardio": cardio,
        "sleep": sleep,
        "recovery": recovery,
        "oxygen": oxygen,
    }


def wearable_score(subscores: dict[str, float]) -> float:
    """Weighted sum of the five sub-scores. Weights are the config heuristics."""
    return float(sum(WEARABLE_WEIGHTS[name] * subscores.get(name, 0.0) for name in WEARABLE_WEIGHTS))

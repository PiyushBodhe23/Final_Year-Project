"""The three viva personas must keep the wearable story the plan describes."""

import numpy as np

from ml.generate_synthetic import demo_personas, generate_series


def test_priya_is_active_and_sleeps_enough() -> None:
    priya = demo_personas()[0]
    series = generate_series(priya)
    assert series["steps"].mean() >= 8000
    assert 7 <= series["sleep_hours"].mean() <= 9
    assert (series["spo2_min"] < 94).mean() < 0.08


def test_rahul_resting_hr_rises_over_the_last_month() -> None:
    rahul = demo_personas()[1]
    series = generate_series(rahul)
    last = series["rhr"].iloc[-30:].to_numpy()
    slope_per_day = float(np.polyfit(np.arange(30), last, 1)[0])
    assert slope_per_day * 30 > 3.5
    assert series["steps"].mean() < 5000
    assert series["sleep_hours"].mean() < 6.5


def test_suresh_has_repeated_low_spo2_nights() -> None:
    suresh = demo_personas()[2]
    series = generate_series(suresh)
    assert (series["spo2_min"] < 94).mean() >= 0.20
    assert series["hrv_rmssd"].mean() < 25


def test_series_is_deterministic() -> None:
    priya = demo_personas()[0]
    first = generate_series(priya)
    second = generate_series(priya)
    assert first["steps"].tolist() == second["steps"].tolist()

"""Domain cleaning: impossible zeros must not stay in the feature matrix."""

import pandas as pd

from ml.training import mark_impossible_zeros


def test_glucose_zero_becomes_missing_and_pregnancy_zero_stays() -> None:
    frame = pd.DataFrame({"Glucose": [0, 88], "Pregnancies": [0, 2]})
    cleaned = mark_impossible_zeros(frame, ["Glucose"])
    assert pd.isna(cleaned.loc[0, "Glucose"])
    assert cleaned.loc[1, "Glucose"] == 88
    assert cleaned.loc[0, "Pregnancies"] == 0

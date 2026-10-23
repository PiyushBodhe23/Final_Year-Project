"""Turn score parts into the short factor lines shown on the dashboard.

Points are on the composite 0-100 scale. Positive points raise the displayed
risk. The split of the ML portion follows logistic log-odds, then rescales so
those lines add up to the ML share of the composite.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV

from backend.app.core.config import TOP_FACTORS

FEATURE_LABELS: dict[str, str] = {
    "Pregnancies": "Pregnancies",
    "Glucose": "Fasting glucose",
    "BloodPressure": "Diastolic blood pressure",
    "SkinThickness": "Skin thickness",
    "Insulin": "Insulin",
    "BMI": "BMI",
    "DiabetesPedigreeFunction": "Diabetes pedigree",
    "Age": "Age",
    "male": "Male sex",
    "age": "Age",
    "currentSmoker": "Current smoking",
    "cigsPerDay": "Cigarettes per day",
    "BPMeds": "Blood pressure medication",
    "prevalentStroke": "Prior stroke",
    "prevalentHyp": "Existing hypertension",
    "diabetes": "Existing diabetes",
    "totChol": "Total cholesterol",
    "sysBP": "Systolic blood pressure",
    "diaBP": "Diastolic blood pressure",
    "heartRate": "Resting heart rate",
    "glucose": "Fasting glucose",
}


@dataclass
class Factor:
    """One signed contribution."""

    name: str
    detail: str
    points: float


def top_factors(factors: list[Factor], limit: int = TOP_FACTORS) -> list[Factor]:
    """Keep the largest absolute contributions."""
    ranked = sorted(factors, key=lambda item: abs(item.points), reverse=True)
    return [item for item in ranked if abs(item.points) >= 0.4][:limit] or ranked[:limit]


def logistic_contributions(
    model: CalibratedClassifierCV,
    row: pd.DataFrame,
    target_points: float,
) -> list[Factor]:
    """Attribute the ML share across input features.

    Each calibrated fold has its own scaler. Contributions are averaged across
    folds, then scaled so they sum to `target_points`.
    """
    folds = model.calibrated_classifiers_
    names = list(row.columns)
    accumulated = np.zeros(len(names))
    for fold in folds:
        if not hasattr(fold.estimator.named_steps["clf"], "coef_"):
            return []
        pipeline = fold.estimator
        matrix = pipeline.named_steps["imputer"].transform(row)
        if "scaler" in pipeline.named_steps:
            matrix = pipeline.named_steps["scaler"].transform(matrix)
        coef = pipeline.named_steps["clf"].coef_.ravel()
        accumulated += coef * matrix.ravel()
    accumulated /= max(len(folds), 1)
    magnitude = float(np.abs(accumulated).sum())
    if magnitude < 1e-8:
        return []
    factors: list[Factor] = []
    raw = row.iloc[0]
    for name, log_odds in zip(names, accumulated, strict=True):
        if not hasattr(folds[0].estimator.named_steps["clf"], "coef_"):
            return []
        points = float(log_odds) / magnitude * target_points
        value = raw[name]
        if pd.isna(value):
            detail = f"{FEATURE_LABELS.get(name, name)} was missing and imputed"
        else:
            detail = f"{FEATURE_LABELS.get(name, name)} {float(value):.1f}"
        factors.append(Factor(FEATURE_LABELS.get(name, name), detail, points))
    return factors

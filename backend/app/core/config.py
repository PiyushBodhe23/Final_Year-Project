"""PreventVital settings, score weights, and clinical thresholds.

Every formula constant used by the risk engine lives here so the methodology
page and the scoring code cannot drift apart.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
DATA_DIR: Path = PROJECT_ROOT / "data"
SQLITE_PATH: Path = DATA_DIR / "preventvital.db"
ML_MODELS_DIR: Path = PROJECT_ROOT / "ml" / "models"
FIGURES_DIR: Path = PROJECT_ROOT / "docs" / "figures"
GUIDELINES_DIR: Path = PROJECT_ROOT / "docs" / "guidelines"
RAG_TOP_K: int = 4
PIMA_CSV: Path = DATA_DIR / "raw" / "pima_diabetes.csv"
FRAMINGHAM_CSV: Path = DATA_DIR / "raw" / "framingham.csv"
METRICS_PATH: Path = ML_MODELS_DIR / "metrics.json"
DIABETES_MODEL_PATH: Path = ML_MODELS_DIR / "diabetes.joblib"
CARDIAC_MODEL_PATH: Path = ML_MODELS_DIR / "cardiac.joblib"

DISCLAIMER: str = (
    "PreventVital is an academic risk-screening prototype trained on public "
    "and synthetic data. It is not a diagnostic device and it is not clinically "
    "validated. Discuss results with a qualified clinician."
)

# Layer A — clinical baseline blend.
# IDRS is an interpretable India-specific score; the ML probability adds lab sensitivity.
DIABETES_IDRS_WEIGHT: float = 0.5
DIABETES_ML_WEIGHT: float = 0.5
# Cardiac baseline blends the calibrated 10-year probability with a simplified
# point cross-check. A 30% ten-year risk is clinically high but only 30 on a
# 0-100 scale, so the point score keeps that baseline comparable to IDRS.
CARDIAC_ML_WEIGHT: float = 0.70
CARDIAC_POINT_SCORE_WEIGHT: float = 0.30

# Indian Diabetes Risk Score (Mohan et al., JAPI 2005, MDRF). Points, not probabilities.
IDRS_CITATION: str = "Mohan V, et al. Indian Diabetes Risk Score. J Assoc Physicians India. 2005."
IDRS_AGE_BANDS: list[dict[str, float]] = [
    {"min_age": 50, "points": 30},
    {"min_age": 35, "points": 20},
]
IDRS_WAIST_MALE: list[dict[str, float]] = [
    {"min_cm": 100, "points": 20},
    {"min_cm": 90, "points": 10},
]
IDRS_WAIST_FEMALE: list[dict[str, float]] = [
    {"min_cm": 90, "points": 20},
    {"min_cm": 80, "points": 10},
]
# Original activity items are 0 / 20 / 30. Our three labels map onto those items.
IDRS_ACTIVITY_POINTS: dict[str, int] = {"regular": 0, "moderate": 20, "sedentary": 30}
IDRS_FAMILY_POINTS: dict[str, int] = {"none": 0, "one parent": 10, "both": 20}

# Simplified teaching cross-check. Not the official Framingham worksheet.
CARDIAC_POINT_AGE: list[dict[str, float]] = [
    {"min_age": 60, "points": 25},
    {"min_age": 50, "points": 18},
    {"min_age": 40, "points": 10},
]
CARDIAC_POINT_MALE: int = 8
CARDIAC_POINT_SMOKER: dict[str, int] = {"current": 16, "former": 6, "never": 0}
CARDIAC_POINT_SBP: list[dict[str, float]] = [
    {"min_mmhg": 160, "points": 20},
    {"min_mmhg": 140, "points": 14},
    {"min_mmhg": 130, "points": 8},
]
CARDIAC_POINT_CHOL: list[dict[str, float]] = [
    {"min_mg_dl": 240, "points": 12},
    {"min_mg_dl": 200, "points": 6},
]
CARDIAC_POINT_HDL: list[dict[str, float]] = [
    {"max_mg_dl": 40, "points": 10},
    {"max_mg_dl": 50, "points": 5},
]
CARDIAC_POINT_DIABETES: int = 12
CARDIAC_POINT_BP_MEDS: int = 4

# Age-adjusted RMSSD reference used beside the personal baseline.
HRV_REF_AT_AGE_25: float = 50.0
HRV_REF_DROP_PER_YEAR: float = 0.45
HRV_REF_FLOOR: float = 18.0

# Uncertainty draws: wearable sub-score noise plus logit noise on the ML probability.
# This is a sensitivity interval, not 100 refitted training models.
WEARABLE_SUBSCORE_NOISE_SD: float = 6.0
ML_LOGIT_NOISE_SD: float = 0.30
TOP_FACTORS: int = 5

# Layer B — wearable behaviour score. Expert-informed heuristics, not validated weights.
WEARABLE_WEIGHTS: dict[str, float] = {
    "activity": 0.30,
    "cardio": 0.25,
    "sleep": 0.20,
    "recovery": 0.15,
    "oxygen": 0.10,
}

# Layer C — composite. Clinical baseline dominates; wearables adjust it.
BASELINE_WEIGHT: float = 0.70
WEARABLE_WEIGHT: float = 0.30

# Risk bands on the 0-100 composite.
BAND_LOW_MAX: float = 29.0
BAND_MODERATE_MAX: float = 59.0

# Uncertainty: report this percentile span of a bootstrap ensemble.
CI_LOW_PERCENTILE: float = 10.0
CI_HIGH_PERCENTILE: float = 90.0
BOOTSTRAP_MODELS: int = 100

# Data-quality gates.
MIN_WEARABLE_DAYS: int = 14
WEARABLE_WINDOW_DAYS: int = 30

# Activity targets (WHO-style 150 min/week moderate-vigorous; 8,000 steps as a practical daily goal).
STEPS_HEALTHY: float = 8000.0
STEPS_CONCERN: float = 3000.0
ACTIVE_MIN_WEEK_HEALTHY: float = 150.0
ACTIVE_MIN_WEEK_CONCERN: float = 50.0

# Resting heart rate.
RHR_HEALTHY_MAX: float = 65.0
RHR_CONCERN_MIN: float = 90.0
RHR_SLOPE_CONCERN_BPM_PER_MONTH: float = 5.0

# Recovery: concern when RMSSD is this far below the personal baseline.
HRV_DEFICIT_CONCERN: float = 0.30

# Sleep.
SLEEP_HOURS_LOW: float = 7.0
SLEEP_HOURS_HIGH: float = 9.0
SLEEP_HOURS_CONCERN: float = 5.0
SLEEP_EFFICIENCY_HEALTHY: float = 85.0
SLEEP_EFFICIENCY_CONCERN: float = 70.0

# Oxygen: share of nights with SpO2 under the threshold.
SPO2_THRESHOLD: float = 94.0
SPO2_NIGHTS_CONCERN: float = 0.20

# Anomaly rule: rolling z-score beyond this for this many consecutive days.
ANOMALY_Z: float = 2.0
ANOMALY_CONSECUTIVE_DAYS: int = 3
PERSONAL_BASELINE_DAYS: int = 60

# Synthetic wearable series. A fixed end date keeps the demo charts stable.
SYNTHETIC_SEED: int = 19
SYNTHETIC_DAYS: int = 180
SYNTHETIC_END: date = date(2026, 10, 18)
COHORT_SIZE: int = 97
SYNTHETIC_DIR: Path = DATA_DIR / "synthetic"

# Display reference ranges (not diagnostic cut-offs).
REFERENCE_RANGES: dict[str, dict[str, float | str]] = {
    "sys_bp": {"high": 120, "unit": "mmHg", "label": "Systolic BP"},
    "dia_bp": {"high": 80, "unit": "mmHg", "label": "Diastolic BP"},
    "fasting_glucose": {"low": 70, "high": 99, "unit": "mg/dL", "label": "Fasting glucose"},
    "hba1c": {"high": 5.7, "unit": "%", "label": "HbA1c"},
    "total_chol": {"high": 200, "unit": "mg/dL", "label": "Total cholesterol"},
    "ldl": {"high": 100, "unit": "mg/dL", "label": "LDL"},
    "triglycerides": {"high": 150, "unit": "mg/dL", "label": "Triglycerides"},
}


def database_url() -> str:
    """Return the SQLAlchemy URL. SQLite is the zero-setup default."""
    override = os.environ.get("DATABASE_URL", "").strip()
    if override:
        return override
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{SQLITE_PATH.as_posix()}"

"""Layer A-C risk scores for diabetes and cardiovascular disease.

The number is a screening composite for the demo, not a diagnosis and not a
validated clinical probability. IDRS points follow Mohan et al. 2005. The ML
half is the calibrated model in ml/models. Wearable points use the config targets.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.core.config import (
    BAND_LOW_MAX,
    BAND_MODERATE_MAX,
    BASELINE_WEIGHT,
    BOOTSTRAP_MODELS,
    CARDIAC_ML_WEIGHT,
    CARDIAC_MODEL_PATH,
    CARDIAC_POINT_AGE,
    CARDIAC_POINT_BP_MEDS,
    CARDIAC_POINT_CHOL,
    CARDIAC_POINT_DIABETES,
    CARDIAC_POINT_HDL,
    CARDIAC_POINT_MALE,
    CARDIAC_POINT_SBP,
    CARDIAC_POINT_SCORE_WEIGHT,
    CARDIAC_POINT_SMOKER,
    CI_HIGH_PERCENTILE,
    CI_LOW_PERCENTILE,
    DIABETES_IDRS_WEIGHT,
    DIABETES_ML_WEIGHT,
    DIABETES_MODEL_PATH,
    DISCLAIMER,
    IDRS_ACTIVITY_POINTS,
    IDRS_AGE_BANDS,
    IDRS_CITATION,
    IDRS_FAMILY_POINTS,
    IDRS_WAIST_FEMALE,
    IDRS_WAIST_MALE,
    MIN_WEARABLE_DAYS,
    ML_LOGIT_NOISE_SD,
    WEARABLE_SUBSCORE_NOISE_SD,
    WEARABLE_WEIGHT,
    WEARABLE_WEIGHTS,
    WEARABLE_WINDOW_DAYS,
)
from backend.app.models.tables import ClinicalRecord, Patient, RiskReport, WearableDaily
from backend.app.services.explainability import Factor, logistic_contributions, top_factors
from backend.app.services.wearable_analytics import wearable_score, wearable_subscores

SUMMARY_METRICS: list[str] = ["rhr", "hrv_rmssd", "steps", "sleep_hours", "spo2_min"]


@dataclass
class ScoreResult:
    """One disease composite, ready to store and return from the API."""

    disease: str
    baseline: float
    wearable_score: float
    subscores: dict[str, float]
    composite: float
    ci_low: float
    ci_high: float
    band: str
    borderline: bool
    confidence: str
    warnings: list[str]
    factors: list[dict[str, str | float]]
    model_version: str
    idrs: float | None
    point_score: float | None
    ml_probability: float | None
    disclaimer: str = DISCLAIMER


def band_for(score: float) -> str:
    """Map a 0-100 composite onto Low, Moderate, or High."""
    if score <= BAND_LOW_MAX:
        return "Low"
    if score <= BAND_MODERATE_MAX:
        return "Moderate"
    return "High"


def _clamp(value: float) -> float:
    return float(min(100.0, max(0.0, value)))


def _points_at_least(value: float, bands: list[dict[str, float]], key: str) -> float:
    """First matching band when bands are ordered from the highest cut-off."""
    for band in bands:
        if value >= band[key]:
            return float(band["points"])
    return 0.0


def idrs_parts(age: int, sex: str, waist_cm: float | None, activity: str, family: str) -> dict[str, float]:
    """Indian Diabetes Risk Score parts. Missing waist scores 0, which lowers concern."""
    age_points = _points_at_least(age, IDRS_AGE_BANDS, "min_age")
    waist_table = IDRS_WAIST_MALE if sex.upper().startswith("M") else IDRS_WAIST_FEMALE
    waist_points = _points_at_least(waist_cm or 0.0, waist_table, "min_cm") if waist_cm else 0.0
    activity_points = float(IDRS_ACTIVITY_POINTS.get(activity, IDRS_ACTIVITY_POINTS["moderate"]))
    family_points = float(IDRS_FAMILY_POINTS.get(family, 0))
    return {
        "IDRS age": age_points,
        "IDRS waist": waist_points,
        "IDRS activity": activity_points,
        "IDRS family history": family_points,
    }


def cardiac_point_parts(patient: Patient, clinical: ClinicalRecord | None) -> dict[str, float]:
    """Simplified cardiac point cross-check. Capped later at 100."""
    labs = clinical
    parts = {
        "Point score age": _points_at_least(patient.age, CARDIAC_POINT_AGE, "min_age"),
        "Point score sex": float(CARDIAC_POINT_MALE if patient.sex.upper().startswith("M") else 0),
        "Point score smoking": float(CARDIAC_POINT_SMOKER.get(patient.smoking, 0)),
    }
    if labs and labs.sys_bp is not None:
        parts["Point score systolic BP"] = _points_at_least(labs.sys_bp, CARDIAC_POINT_SBP, "min_mmhg")
    if labs and labs.total_chol is not None:
        parts["Point score cholesterol"] = _points_at_least(labs.total_chol, CARDIAC_POINT_CHOL, "min_mg_dl")
    if labs and labs.hdl is not None:
        hdl_points = 0.0
        for band in CARDIAC_POINT_HDL:
            if labs.hdl <= band["max_mg_dl"]:
                hdl_points = float(band["points"])
                break
        parts["Point score HDL"] = hdl_points
    if patient.existing_diabetes:
        parts["Point score diabetes"] = float(CARDIAC_POINT_DIABETES)
    if patient.bp_meds:
        parts["Point score BP medication"] = float(CARDIAC_POINT_BP_MEDS)
    return parts


def _bmi(patient: Patient) -> float | None:
    if not patient.height_cm or not patient.weight_kg:
        return None
    meters = patient.height_cm / 100.0
    return float(patient.weight_kg / (meters * meters))


@lru_cache(maxsize=2)
def _load_model(path: str) -> dict | None:
    """Load a joblib artifact once. None means the heuristic fallback is used."""
    if not Path(path).exists():
        return None
    return joblib.load(path)


def _probability(path: str, row: pd.DataFrame) -> tuple[float, object | None, str, pd.DataFrame]:
    """Calibrated probability. Falls back to a documented heuristic if weights are missing."""
    try:
        artifact = _load_model(path)
    except Exception:
        artifact = None
    if artifact is None:
        return _heuristic_probability(path, row), None, "heuristic", row
    model = artifact["model"]
    ordered = row.reindex(columns=artifact["features"])
    probability = float(model.predict_proba(ordered)[0, 1])
    return probability, model, str(artifact.get("version", "unknown")), ordered


def _heuristic_probability(path: str, row: pd.DataFrame) -> float:
    """Used only when the joblib file cannot be read. Not the trained model."""
    if "Glucose" in row.columns:
        glucose = float(row["Glucose"].iloc[0]) if pd.notna(row["Glucose"].iloc[0]) else 100.0
        bmi = float(row["BMI"].iloc[0]) if pd.notna(row["BMI"].iloc[0]) else 25.0
        age = float(row["Age"].iloc[0]) if pd.notna(row["Age"].iloc[0]) else 40.0
        logit = -3.2 + 0.03 * (glucose - 100) + 0.08 * (bmi - 25) + 0.02 * (age - 40)
        return float(1.0 / (1.0 + np.exp(-logit)))
    return 0.15


def _diabetes_row(patient: Patient, clinical: ClinicalRecord | None) -> pd.DataFrame:
    """Pima feature row. Labs we do not collect stay missing so the imputer fills them."""
    glucose = clinical.fasting_glucose if clinical else None
    diastolic = clinical.dia_bp if clinical else None
    return pd.DataFrame(
        [
            {
                "Pregnancies": np.nan,
                "Glucose": glucose if glucose is not None else np.nan,
                "BloodPressure": diastolic if diastolic is not None else np.nan,
                "SkinThickness": np.nan,
                "Insulin": np.nan,
                "BMI": _bmi(patient) if _bmi(patient) is not None else np.nan,
                "DiabetesPedigreeFunction": np.nan,
                "Age": patient.age,
            }
        ]
    )


def _cardiac_row(patient: Patient, clinical: ClinicalRecord | None, resting_hr: float | None) -> pd.DataFrame:
    """Framingham feature row. Resting HR comes from the wearable window when present."""
    labs = clinical
    return pd.DataFrame(
        [
            {
                "male": 1 if patient.sex.upper().startswith("M") else 0,
                "age": patient.age,
                "currentSmoker": 1 if patient.smoking == "current" else 0,
                "cigsPerDay": patient.cigs_per_day or 0.0,
                "BPMeds": 1 if patient.bp_meds else 0,
                "prevalentStroke": 1 if patient.prior_stroke else 0,
                "prevalentHyp": 1 if patient.existing_hypertension else 0,
                "diabetes": 1 if patient.existing_diabetes else 0,
                "totChol": labs.total_chol if labs and labs.total_chol is not None else np.nan,
                "sysBP": labs.sys_bp if labs and labs.sys_bp is not None else np.nan,
                "diaBP": labs.dia_bp if labs and labs.dia_bp is not None else np.nan,
                "BMI": _bmi(patient) if _bmi(patient) is not None else np.nan,
                "heartRate": resting_hr if resting_hr is not None else np.nan,
                "glucose": labs.fasting_glucose if labs and labs.fasting_glucose is not None else np.nan,
            }
        ]
    )


def _perturb_probability(probability: float, rng: np.random.Generator) -> float:
    """Move a probability on the logit scale and bring it back to (0, 1)."""
    clipped = min(max(probability, 1e-4), 1.0 - 1e-4)
    logit = np.log(clipped / (1.0 - clipped))
    drawn = logit + float(rng.normal(0.0, ML_LOGIT_NOISE_SD))
    return float(1.0 / (1.0 + np.exp(-drawn)))


def _interval(
    baseline_builder,
    subscores: dict[str, float],
    rng: np.random.Generator,
) -> tuple[float, float]:
    """10th-90th percentile of the composite under sub-score and probability noise."""
    draws = np.empty(BOOTSTRAP_MODELS)
    names = list(WEARABLE_WEIGHTS)
    for index in range(BOOTSTRAP_MODELS):
        noisy = {
            name: _clamp(subscores[name] + float(rng.normal(0.0, WEARABLE_SUBSCORE_NOISE_SD)))
            for name in names
        }
        draws[index] = _clamp(baseline_builder(rng) * BASELINE_WEIGHT + wearable_score(noisy) * WEARABLE_WEIGHT)
    return float(np.percentile(draws, CI_LOW_PERCENTILE)), float(np.percentile(draws, CI_HIGH_PERCENTILE))


def _factor_from_parts(parts: dict[str, float], scale: float) -> list[Factor]:
    factors: list[Factor] = []
    for name, points in parts.items():
        scaled = points * scale
        if scaled == 0:
            continue
        factors.append(Factor(name, f"{name}: {points:.0f} raw points", scaled))
    return factors


def _wearable_factors(subscores: dict[str, float]) -> list[Factor]:
    factors: list[Factor] = []
    for name, weight in WEARABLE_WEIGHTS.items():
        points = subscores.get(name, 0.0) * weight * WEARABLE_WEIGHT
        factors.append(Factor(f"Wearable {name}", f"{name} concern {subscores.get(name, 0.0):.0f}/100", points))
    return factors


def _quality(patient: Patient, clinical: ClinicalRecord | None, n_days: int) -> tuple[str, list[str]]:
    """Low confidence when the wearable window is short or a key lab is absent."""
    warnings: list[str] = []
    if n_days < MIN_WEARABLE_DAYS:
        warnings.append(f"Only {n_days} wearable days. At least {MIN_WEARABLE_DAYS} are needed for a stable score.")
    if clinical is None or clinical.fasting_glucose is None:
        warnings.append("Fasting glucose is missing. The model used the training median.")
    if clinical is None or clinical.sys_bp is None:
        warnings.append("Blood pressure is missing. The cardiac score is less reliable.")
    if not patient.height_cm or not patient.weight_kg:
        warnings.append("Height or weight is missing, so BMI was imputed.")
    confidence = "low" if warnings else "high" if n_days >= WEARABLE_WINDOW_DAYS else "medium"
    return confidence, warnings


def _wearable_frame(rows: list[WearableDaily]) -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "date": row.date,
                "steps": row.steps,
                "active_min": row.active_min,
                "rhr": row.rhr,
                "hrv_rmssd": row.hrv_rmssd,
                "spo2_min": row.spo2_min,
                "sleep_hours": row.sleep_hours,
                "sleep_efficiency": row.sleep_efficiency,
            }
            for row in rows
        ]
    )
    if frame.empty:
        return frame
    return frame.sort_values("date")


def calculate_risk(
    session: Session,
    patient_id: int,
    *,
    persist: bool = True,
    fasting_glucose: float | None = None,
    steps: float | None = None,
    sleep_hours: float | None = None,
) -> list[ScoreResult]:
    """Score diabetes and cardiovascular risk.

    Stored reports are written only when `persist` is true. What-if sliders pass
    lab or wearable overrides and leave the saved report unchanged.
    """
    patient = session.get(Patient, patient_id)
    if patient is None:
        raise LookupError(f"No patient {patient_id}")
    clinical = (
        session.query(ClinicalRecord)
        .filter(ClinicalRecord.patient_id == patient_id)
        .order_by(ClinicalRecord.recorded_at.desc())
        .first()
    )
    if fasting_glucose is not None and clinical is not None:
        clinical.fasting_glucose = float(fasting_glucose)
    wearables = (
        session.query(WearableDaily)
        .filter(WearableDaily.patient_id == patient_id)
        .order_by(WearableDaily.date)
        .all()
    )
    frame = _wearable_frame(wearables)
    if not frame.empty:
        recent_index = frame.index[-WEARABLE_WINDOW_DAYS:]
        if steps is not None:
            frame.loc[recent_index, "steps"] = float(steps)
        if sleep_hours is not None:
            frame.loc[recent_index, "sleep_hours"] = float(sleep_hours)
    subscores = wearable_subscores(frame, patient.age) if not frame.empty else {name: 0.0 for name in WEARABLE_WEIGHTS}
    behaviour = wearable_score(subscores)
    confidence, warnings = _quality(patient, clinical, len(frame))
    resting = float(frame.tail(WEARABLE_WINDOW_DAYS)["rhr"].mean()) if not frame.empty else None
    rng = np.random.default_rng(patient_id)

    idrs = idrs_parts(
        patient.age,
        patient.sex,
        patient.waist_cm,
        patient.activity_level,
        patient.family_hx_diabetes,
    )
    idrs_total = float(sum(idrs.values()))
    diabetes_row = _diabetes_row(patient, clinical)
    diabetes_p, diabetes_model, diabetes_version, diabetes_row = _probability(str(DIABETES_MODEL_PATH), diabetes_row)
    diabetes_baseline = _clamp(DIABETES_IDRS_WEIGHT * idrs_total + DIABETES_ML_WEIGHT * diabetes_p * 100.0)

    points = cardiac_point_parts(patient, clinical)
    point_total = float(min(100.0, sum(points.values())))
    cardiac_row = _cardiac_row(patient, clinical, resting)
    cardiac_p, cardiac_model, cardiac_version, cardiac_row = _probability(str(CARDIAC_MODEL_PATH), cardiac_row)
    cardiac_baseline = _clamp(
        CARDIAC_ML_WEIGHT * cardiac_p * 100.0 + CARDIAC_POINT_SCORE_WEIGHT * point_total
    )

    results: list[ScoreResult] = []
    specs = [
        (
            "diabetes",
            diabetes_baseline,
            diabetes_p,
            diabetes_model,
            diabetes_row,
            diabetes_version,
            idrs_total,
            None,
            _factor_from_parts(idrs, DIABETES_IDRS_WEIGHT * BASELINE_WEIGHT),
            DIABETES_ML_WEIGHT * BASELINE_WEIGHT * 100.0,
            lambda draw, prob=diabetes_p: _clamp(
                DIABETES_IDRS_WEIGHT * idrs_total + DIABETES_ML_WEIGHT * _perturb_probability(prob, draw) * 100.0
            ),
        ),
        (
            "cardiac",
            cardiac_baseline,
            cardiac_p,
            cardiac_model,
            cardiac_row,
            cardiac_version,
            None,
            point_total,
            _factor_from_parts(points, CARDIAC_POINT_SCORE_WEIGHT * BASELINE_WEIGHT),
            CARDIAC_ML_WEIGHT * BASELINE_WEIGHT * 100.0,
            lambda draw, prob=cardiac_p, pts=point_total: _clamp(
                CARDIAC_ML_WEIGHT * _perturb_probability(prob, draw) * 100.0 + CARDIAC_POINT_SCORE_WEIGHT * pts
            ),
        ),
    ]
    generated = datetime.now(timezone.utc)
    for disease, baseline, probability, model, row, version, idrs_value, point_value, rule_factors, ml_scale, builder in specs:
        composite = _clamp(baseline * BASELINE_WEIGHT + behaviour * WEARABLE_WEIGHT)
        low, high = _interval(builder, subscores, rng)
        ml_factors: list[Factor] = []
        if model is not None:
            ml_factors = logistic_contributions(model, row, probability * ml_scale)
        factors = top_factors(rule_factors + ml_factors + _wearable_factors(subscores))
        result = ScoreResult(
            disease=disease,
            baseline=round(baseline, 1),
            wearable_score=round(behaviour, 1),
            subscores={name: round(value, 1) for name, value in subscores.items()},
            composite=round(composite, 1),
            ci_low=round(low, 1),
            ci_high=round(high, 1),
            band=band_for(composite),
            borderline=band_for(low) != band_for(high),
            confidence=confidence,
            warnings=warnings,
            factors=[{"name": item.name, "detail": item.detail, "points": round(item.points, 1)} for item in factors],
            model_version=version,
            idrs=idrs_value,
            point_score=point_value,
            ml_probability=round(probability, 4),
        )
        if persist:
            session.add(
            RiskReport(
                patient_id=patient_id,
                generated_at=generated,
                disease=disease,
                baseline=result.baseline,
                wearable_score=result.wearable_score,
                composite=result.composite,
                ci_low=result.ci_low,
                ci_high=result.ci_high,
                band=result.band,
                top_factors_json={
                    "factors": result.factors,
                    "subscores": result.subscores,
                    "idrs": result.idrs,
                    "point_score": result.point_score,
                    "ml_probability": result.ml_probability,
                    "borderline": result.borderline,
                    "confidence": result.confidence,
                    "warnings": result.warnings,
                },
                model_version=version,
            )
        )
        results.append(result)
    if persist:
        session.commit()
    else:
        session.rollback()
    return results


def methodology_payload() -> dict:
    """Formulas and weights for the How it works page. Read from config only."""
    return {
        "disclaimer": DISCLAIMER,
        "idrs_citation": IDRS_CITATION,
        "idrs": {
            "age": IDRS_AGE_BANDS,
            "waist_male": IDRS_WAIST_MALE,
            "waist_female": IDRS_WAIST_FEMALE,
            "activity": IDRS_ACTIVITY_POINTS,
            "family_history": IDRS_FAMILY_POINTS,
        },
        "diabetes_baseline": f"{DIABETES_IDRS_WEIGHT} * IDRS + {DIABETES_ML_WEIGHT} * ML_probability * 100",
        "cardiac_baseline": (
            f"{CARDIAC_ML_WEIGHT} * ML_probability * 100 + {CARDIAC_POINT_SCORE_WEIGHT} * point_score"
        ),
        "cardiac_points": {
            "age": CARDIAC_POINT_AGE,
            "male": CARDIAC_POINT_MALE,
            "smoking": CARDIAC_POINT_SMOKER,
            "systolic_bp": CARDIAC_POINT_SBP,
            "cholesterol": CARDIAC_POINT_CHOL,
            "hdl_at_or_below": CARDIAC_POINT_HDL,
            "diabetes": CARDIAC_POINT_DIABETES,
            "bp_medication": CARDIAC_POINT_BP_MEDS,
            "note": "Simplified teaching cross-check, not the official Framingham worksheet.",
        },
        "wearable_weights": WEARABLE_WEIGHTS,
        "composite": f"{BASELINE_WEIGHT} * baseline + {WEARABLE_WEIGHT} * wearable_score",
        "bands": {"low_max": BAND_LOW_MAX, "moderate_max": BAND_MODERATE_MAX, "high_min": BAND_MODERATE_MAX + 1},
        "uncertainty": (
            f"{int(CI_LOW_PERCENTILE)}th-{int(CI_HIGH_PERCENTILE)}th percentile of {BOOTSTRAP_MODELS} draws. "
            "Each draw perturbs wearable sub-scores and the ML probability. It does not refit the training set."
        ),
    }


def report_to_result(report: RiskReport) -> dict:
    """Rebuild an API payload from a stored report."""
    extra = report.top_factors_json or {}
    return {
        "disease": report.disease,
        "baseline": report.baseline,
        "wearable_score": report.wearable_score,
        "subscores": extra.get("subscores", {}),
        "composite": report.composite,
        "ci_low": report.ci_low,
        "ci_high": report.ci_high,
        "band": report.band,
        "borderline": bool(extra.get("borderline", band_for(report.ci_low) != band_for(report.ci_high))),
        "confidence": extra.get("confidence", "medium"),
        "warnings": extra.get("warnings", []),
        "factors": extra.get("factors", []),
        "model_version": report.model_version,
        "idrs": extra.get("idrs"),
        "point_score": extra.get("point_score"),
        "ml_probability": extra.get("ml_probability"),
        "generated_at": report.generated_at,
        "disclaimer": DISCLAIMER,
    }


def latest_results(session: Session, patient_id: int) -> list[dict]:
    """Newest stored report for each disease."""
    reports = (
        session.query(RiskReport)
        .filter(RiskReport.patient_id == patient_id)
        .order_by(RiskReport.generated_at.desc(), RiskReport.id.desc())
        .all()
    )
    seen: set[str] = set()
    chosen: list[dict] = []
    for report in reports:
        if report.disease in seen:
            continue
        seen.add(report.disease)
        chosen.append(report_to_result(report))
    return chosen

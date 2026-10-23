"""Per-patient history lookup and short-horizon future vital / HRI predictions."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from backend.config import FORECAST_HORIZON_HOURS, PATIENT_HISTORY_PATH, PATIENT_TRAINING_PATH
from backend.models.risk_engine import get_risk_engine
from backend.services.alert_system import band_from_hri


class ForecastPoint(BaseModel):
    hour_ahead: int
    heart_rate: float
    spo2: float
    respiratory_rate: float
    temperature: float
    blood_pressure_sys: float
    blood_pressure_dia: float
    predicted_hri: float
    risk_band: str


class PatientPrediction(BaseModel):
    patient_id: str
    horizon_hours: int
    method: str = "linear_trend_plus_hri"
    latest_vitals: dict[str, Any]
    latest_hri: float
    latest_risk_band: str
    history_hours: int
    trend_summary: str
    forecast: list[ForecastPoint]
    rising_risk: bool
    drivers: list[dict[str, Any]] = Field(default_factory=list)
    age_profile: str = "adult"
    age_profile_label: str = "Adult 40–64"
    risk_method: str = ""
    trend_note: str = ""
    disclaimer: str = (
        "Educational forecast only - not a clinical prediction or diagnosis."
    )


def _to_vitals(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    data = row.to_dict() if isinstance(row, pd.Series) else dict(row)
    return {
        "timestamp": str(data.get("timestamp", "")),
        "patient_id": str(data.get("patient_id", "")),
        "device_id": str(data.get("patient_id", "unknown")),
        "platform": "patient_history",
        "heart_rate": float(data.get("heart_rate", 0) or 0),
        "spo2": float(data.get("spo2_level", data.get("spo2", 0)) or 0),
        "oxygen_reading": float(data.get("oxygen_reading", 0) or 0),
        "respiratory_rate": float(data.get("respiratory_rate", 0) or 0),
        "temperature": float(data.get("temperature", 0) or 0),
        "blood_pressure_sys": float(data.get("blood_pressure_sys", 0) or 0),
        "blood_pressure_dia": float(data.get("blood_pressure_dia", 0) or 0),
        "steps": float(data.get("steps", 0) or 0),
        "activity": str(data.get("activity", "unknown")),
        "sepsis_label": int(data.get("sepsis_label", 0) or 0),
        "age": int(data.get("age", 0) or 0),
        "gender": str(data.get("gender", "")),
    }


@lru_cache(maxsize=1)
def _load_history_df() -> pd.DataFrame:
    if not PATIENT_HISTORY_PATH.exists():
        # Fallback: single-row excel expanded to a trivial history
        if PATIENT_TRAINING_PATH.exists():
            df = pd.read_excel(PATIENT_TRAINING_PATH)
            df["patient_id"] = df["patient_id"].astype(str)
            return df
        return pd.DataFrame()
    df = pd.read_csv(PATIENT_HISTORY_PATH)
    df["patient_id"] = df["patient_id"].astype(str)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values(["patient_id", "timestamp"])
    return df


def list_patient_ids() -> list[str]:
    from backend.services.user_store import DEMOGRAPHICS_PATH, list_users

    ids: list[str] = []
    df = _load_history_df()
    if not df.empty:
        ids.extend(df["patient_id"].astype(str).unique().tolist())
    if DEMOGRAPHICS_PATH.exists():
        demo = pd.read_csv(DEMOGRAPHICS_PATH, usecols=["patient_id"])
        ids.extend(demo["patient_id"].astype(str).unique().tolist())
    ids.extend(u["user_id"] for u in list_users())
    return sorted(set(ids), key=lambda x: (x[0], int("".join(ch for ch in x if ch.isdigit()) or 0)))


def get_patient_history(patient_id: str, limit: int | None = None) -> list[dict[str, Any]]:
    from backend.services.user_store import get_demographics

    df = _load_history_df()
    if df.empty:
        return []
    subset = df[df["patient_id"].astype(str) == str(patient_id)].copy()
    if subset.empty:
        return []
    if "timestamp" in subset.columns:
        subset = subset.sort_values("timestamp")
    if limit:
        subset = subset.tail(limit)
    demo = get_demographics(patient_id)
    rows = []
    for _, row in subset.iterrows():
        vitals = _to_vitals(row)
        vitals["age"] = demo["age"]
        vitals["gender"] = demo["gender"]
        rows.append(vitals)
    return rows


def append_synthetic_history(patient_id: str, hours: int = 24) -> list[dict[str, Any]]:
    """Append 24 hourly vital rows for a new patient into patient_history.csv."""
    import random
    from datetime import datetime, timedelta

    existing = get_patient_history(patient_id, limit=1)
    if existing:
        return get_patient_history(patient_id, limit=hours)

    rng = random.Random(hash(patient_id) % (2**32))
    now = datetime.now()
    rows = []
    hr0 = rng.gauss(76, 8)
    for i in range(hours):
        ts = now - timedelta(hours=hours - 1 - i)
        rows.append(
            {
                "patient_id": patient_id,
                "timestamp": ts.isoformat(timespec="seconds"),
                "hour_index": i,
                "heart_rate": int(max(50, min(140, hr0 + rng.gauss(0, 3)))),
                "spo2_level": round(max(90.0, min(100.0, rng.gauss(97.2, 0.6))), 1),
                "oxygen_reading": round(max(90.0, min(100.0, rng.gauss(97.0, 0.5))), 1),
                "respiratory_rate": round(max(12.0, min(28.0, rng.gauss(16, 1.2))), 1),
                "temperature": round(rng.gauss(36.7, 0.15), 1),
                "blood_pressure_sys": int(max(95, min(160, rng.gauss(118, 6)))),
                "blood_pressure_dia": int(max(60, min(100, rng.gauss(76, 5)))),
                "steps": int(max(0, rng.gauss(90, 40))),
                "activity": rng.choice(["resting", "walking", "sleep", "light_exercise"]),
                "sepsis_label": 0,
            }
        )
    extra = pd.DataFrame(rows)
    PATIENT_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if PATIENT_HISTORY_PATH.exists():
        extra.to_csv(PATIENT_HISTORY_PATH, mode="a", header=False, index=False)
    else:
        extra.to_csv(PATIENT_HISTORY_PATH, index=False)
    _load_history_df.cache_clear()
    return rows


def append_training_snapshot(patient_id: str, latest: dict[str, Any]) -> None:
    """Add one current-vitals row so the training workbook stays in sync."""
    row = {
        "patient_id": patient_id,
        "timestamp": latest.get("timestamp", ""),
        "heart_rate": latest.get("heart_rate"),
        "spo2_level": latest.get("spo2_level", latest.get("spo2")),
        "oxygen_reading": latest.get("oxygen_reading"),
        "respiratory_rate": latest.get("respiratory_rate"),
        "temperature": latest.get("temperature"),
        "blood_pressure_sys": latest.get("blood_pressure_sys"),
        "blood_pressure_dia": latest.get("blood_pressure_dia"),
        "steps": latest.get("steps"),
        "activity": latest.get("activity", "resting"),
        "sepsis_label": latest.get("sepsis_label", 0),
    }
    if PATIENT_TRAINING_PATH.exists():
        try:
            df = pd.read_excel(PATIENT_TRAINING_PATH)
        except Exception:
            df = pd.DataFrame()
        if not df.empty:
            df["patient_id"] = df["patient_id"].astype(str)
            if str(patient_id) in set(df["patient_id"].astype(str)):
                return
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_excel(PATIENT_TRAINING_PATH, index=False)
            return
    pd.DataFrame([row]).to_excel(PATIENT_TRAINING_PATH, index=False)


def enroll_patient(display_name: str, age: int, gender: str) -> dict[str, Any]:
    """Register demographics only - no synthetic vitals or fake past history."""
    from backend.services.user_store import create_user

    user = create_user(display_name, age=age, gender=gender)
    user["history_hours"] = 0
    user["is_new"] = True
    return user


def _empty_prediction(patient_id: str, horizon_hours: int) -> PatientPrediction:
    """Prediction payload for newly enrolled patients with no wearable data yet."""
    from backend.services.user_store import get_demographics

    demo = get_demographics(patient_id)
    return PatientPrediction(
        patient_id=str(patient_id),
        horizon_hours=horizon_hours,
        latest_vitals={
            "patient_id": str(patient_id),
            "age": demo.get("age"),
            "gender": demo.get("gender"),
        },
        latest_hri=0.0,
        latest_risk_band="low",
        history_hours=0,
        trend_summary="Newly enrolled patient - no wearable readings yet.",
        forecast=[],
        rising_risk=False,
    )


def _slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    y = np.asarray(values, dtype=float)
    x = np.arange(len(y), dtype=float)
    # simple least-squares slope
    x_mean = x.mean()
    y_mean = y.mean()
    denom = ((x - x_mean) ** 2).sum()
    if denom == 0:
        return 0.0
    return float(((x - x_mean) * (y - y_mean)).sum() / denom)


def _trend_summary(history: list[dict[str, Any]], latest_hri: float) -> str:
    if len(history) < 3:
        return f"Limited history available. Latest HRI is {latest_hri:.1f}."
    hr_s = _slope([h["heart_rate"] for h in history[-12:]])
    spo2_s = _slope([h["spo2"] for h in history[-12:]])
    bits = []
    bits.append("rising" if hr_s > 0.3 else "falling" if hr_s < -0.3 else "stable")
    bits.append(f"heart rate ({hr_s:+.2f}/hr)")
    bits.append("improving" if spo2_s > 0.05 else "declining" if spo2_s < -0.05 else "stable")
    bits.append(f"SpO2 ({spo2_s:+.3f}/hr)")
    return (
        f"Over recent hours: {bits[0]} {bits[1]}; {bits[2]} {bits[3]}. "
        f"Latest HRI {latest_hri:.1f}."
    )


def predict_patient_future(
    patient_id: str,
    horizon_hours: int | None = None,
    history_limit: int = 24,
) -> PatientPrediction:
    horizon = horizon_hours or FORECAST_HORIZON_HOURS
    history = get_patient_history(patient_id, limit=history_limit)
    if not history:
        return _empty_prediction(patient_id, horizon)

    from backend.services.user_store import get_demographics

    demo = get_demographics(patient_id)
    latest = dict(history[-1])
    latest["age"] = demo.get("age", latest.get("age"))
    latest["gender"] = demo.get("gender", latest.get("gender"))
    engine = get_risk_engine()
    latest_risk = engine.assess(latest, history=history)
    series_keys = [
        "heart_rate",
        "spo2",
        "respiratory_rate",
        "temperature",
        "blood_pressure_sys",
        "blood_pressure_dia",
    ]
    slopes = {k: _slope([float(h[k]) for h in history[-12:]]) for k in series_keys}

    forecast: list[ForecastPoint] = []
    for step in range(1, horizon + 1):
        projected = dict(latest)
        projected["age"] = latest.get("age")
        for k, slope in slopes.items():
            projected[k] = float(latest[k]) + slope * step
        # keep physiologically plausible clamps
        projected["heart_rate"] = float(np.clip(projected["heart_rate"], 40, 200))
        projected["spo2"] = float(np.clip(projected["spo2"], 80, 100))
        projected["respiratory_rate"] = float(np.clip(projected["respiratory_rate"], 6, 45))
        projected["temperature"] = float(np.clip(projected["temperature"], 34.5, 41.0))
        projected["blood_pressure_sys"] = float(np.clip(projected["blood_pressure_sys"], 70, 220))
        projected["blood_pressure_dia"] = float(np.clip(projected["blood_pressure_dia"], 35, 140))
        projected["steps"] = float(latest.get("steps", 0))
        risk = engine.assess(projected)
        forecast.append(
            ForecastPoint(
                hour_ahead=step,
                heart_rate=round(projected["heart_rate"], 1),
                spo2=round(projected["spo2"], 1),
                respiratory_rate=round(projected["respiratory_rate"], 1),
                temperature=round(projected["temperature"], 1),
                blood_pressure_sys=round(projected["blood_pressure_sys"], 1),
                blood_pressure_dia=round(projected["blood_pressure_dia"], 1),
                predicted_hri=round(risk.hri, 2),
                risk_band=risk.risk_band,
            )
        )

    future_hris = [p.predicted_hri for p in forecast]
    rising = bool(future_hris[-1] > latest_risk.hri + 3)

    return PatientPrediction(
        patient_id=str(patient_id),
        horizon_hours=horizon,
        latest_vitals=latest,
        latest_hri=round(latest_risk.hri, 2),
        latest_risk_band=latest_risk.risk_band,
        history_hours=len(history),
        trend_summary=_trend_summary(history, latest_risk.hri),
        forecast=forecast,
        rising_risk=rising,
        drivers=[item.model_dump() for item in latest_risk.drivers],
        age_profile=latest_risk.age_profile,
        age_profile_label=latest_risk.age_profile_label,
        risk_method=latest_risk.method,
        trend_note=latest_risk.trend_note,
    )


def build_agent_context(patient_id: str, horizon_hours: int | None = None) -> dict[str, Any]:
    """Bundle history + prediction text blocks for the LLM agent."""
    from backend.services.user_store import get_demographics

    history = get_patient_history(patient_id, limit=24)
    prediction = predict_patient_future(patient_id, horizon_hours=horizon_hours)
    demo = get_demographics(patient_id)
    is_new = len(history) == 0
    # Compact history for prompt (last 8 rows)
    hist_lines = []
    for h in history[-8:]:
        hist_lines.append(
            f"{h.get('timestamp')}: HR={h['heart_rate']}, SpO2={h['spo2']}, "
            f"RR={h['respiratory_rate']}, Temp={h['temperature']}, "
            f"BP={h['blood_pressure_sys']}/{h['blood_pressure_dia']}"
        )
    forecast_lines = [
        f"+{p.hour_ahead}h: HR={p.heart_rate}, SpO2={p.spo2}, HRI={p.predicted_hri} ({p.risk_band})"
        for p in prediction.forecast
    ]
    vitals = dict(prediction.latest_vitals or {})
    vitals["age"] = demo.get("age", vitals.get("age"))
    vitals["gender"] = demo.get("gender", vitals.get("gender"))
    return {
        "patient_id": patient_id,
        "history": history,
        "prediction": prediction.model_dump(),
        "history_text": (
            "Newly enrolled - no past readings."
            if is_new
            else ("\n".join(hist_lines) if hist_lines else "No history.")
        ),
        "forecast_text": (
            "No forecast - waiting for first wearable reading."
            if is_new
            else "\n".join(forecast_lines)
        ),
        "trend_summary": prediction.trend_summary,
        "vitals": vitals,
        "hri": None if is_new else prediction.latest_hri,
        "risk_band": None if is_new else prediction.latest_risk_band,
        "drivers": [] if is_new else prediction.drivers,
        "age_profile": prediction.age_profile,
        "age_profile_label": prediction.age_profile_label,
        "risk_method": prediction.risk_method,
        "trend_note": prediction.trend_note,
        "is_new": is_new,
        "demographics": {
            "age": demo.get("age"),
            "gender": demo.get("gender"),
            "display_name": demo.get("display_name"),
        },
    }

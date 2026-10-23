"""Health Risk Index (HRI) calculation — RF + LSTM ensemble with heuristic fallback."""

from __future__ import annotations

from typing import Any

import joblib
import numpy as np
from pydantic import BaseModel, Field

from backend.config import (
    AGE_PROFILE_LABELS,
    FEATURE_COLUMNS,
    HRI_THRESHOLDS,
    LSTM_MODEL_PATH,
    LSTM_SCALER_PATH,
    LSTM_SEQ_LEN,
    RF_MODEL_PATH,
    VITAL_LABELS,
    ranges_for_age,
)
from backend.services.alert_system import band_from_hri

HEURISTIC_WEIGHTS = {
    "heart_rate": 0.22,
    "spo2": 0.28,
    "respiratory_rate": 0.15,
    "temperature": 0.12,
    "blood_pressure_sys": 0.13,
    "blood_pressure_dia": 0.10,
}


class VitalDriver(BaseModel):
    key: str
    label: str
    value: float | None = None
    status: str
    points: float
    note: str


class RiskResult(BaseModel):
    hri: float = Field(..., ge=0, le=100)
    risk_band: str
    rf_score: float | None = None
    lstm_score: float | None = None
    method: str
    details: dict[str, Any] = Field(default_factory=dict)
    drivers: list[VitalDriver] = Field(default_factory=list)
    age_profile: str = "adult"
    age_profile_label: str = "Adult 40–64"
    trend_adjustment: float = 0
    trend_note: str = ""


def _clip_hri(value: float) -> float:
    return float(max(0.0, min(100.0, value)))


def _score_vital(val: float, rng: dict[str, float], weight: float) -> tuple[float, str, str]:
    lo, hi = rng.get("min", 0), rng.get("max", 1)
    clo, chi = rng.get("critical_low", lo), rng.get("critical_high", hi)
    full = 100 * weight
    if val < clo or val > chi:
        side = "low" if val < clo else "high"
        return full, "critical", f"outside critical {side} limit"
    if val < lo:
        span = max(lo - clo, 1e-6)
        points = full * min(1.0, (lo - val) / span)
        return points, "watch", "below the age-adjusted normal range"
    if val > hi:
        span = max(chi - hi, 1e-6)
        points = full * min(1.0, (val - hi) / span)
        return points, "watch", "above the age-adjusted normal range"
    return 0.0, "normal", "inside the age-adjusted normal range"


def explain_vitals(vitals: dict[str, Any]) -> tuple[float, list[VitalDriver], str, str]:
    """Score each vital and return (heuristic HRI, drivers, profile, profile label)."""
    profile, ranges = ranges_for_age(vitals.get("age"))
    drivers: list[VitalDriver] = []
    score = 0.0
    for key, weight in HEURISTIC_WEIGHTS.items():
        raw = vitals.get(key)
        if raw in (None, ""):
            continue
        try:
            val = float(raw)
        except (TypeError, ValueError):
            continue
        points, status, note = _score_vital(val, ranges.get(key, {}), weight)
        score += points
        drivers.append(
            VitalDriver(
                key=key,
                label=VITAL_LABELS.get(key, key),
                value=round(val, 2),
                status=status,
                points=round(points, 2),
                note=note,
            )
        )
    drivers.sort(key=lambda item: item.points, reverse=True)
    label = AGE_PROFILE_LABELS.get(profile, profile)
    return _clip_hri(score), drivers, profile, label


def heuristic_hri(vitals: dict[str, Any]) -> float:
    """Rule-based HRI when ML weights are unavailable."""
    score, _, _, _ = explain_vitals(vitals)
    return score


def trend_adjustment(history: list[dict[str, Any]] | None) -> tuple[float, str]:
    """Extra HRI when recent heart rate rises or SpO2 falls."""
    if not history or len(history) < 3:
        return 0.0, ""
    recent = history[-6:]

    def _nums(key: str) -> list[float]:
        out: list[float] = []
        for row in recent:
            raw = row.get(key)
            if raw in (None, ""):
                continue
            try:
                out.append(float(raw))
            except (TypeError, ValueError):
                continue
        return out

    notes: list[str] = []
    extra = 0.0
    hrs = _nums("heart_rate")
    spo2s = _nums("spo2")
    if len(hrs) >= 3:
        delta_hr = hrs[-1] - hrs[0]
        if delta_hr >= 8:
            extra += min(12.0, delta_hr * 0.6)
            notes.append(f"heart rate up {delta_hr:.0f} bpm across recent readings")
    if len(spo2s) >= 3:
        delta_spo2 = spo2s[-1] - spo2s[0]
        if delta_spo2 <= -1.5:
            extra += min(15.0, abs(delta_spo2) * 4)
            notes.append(f"SpO₂ down {abs(delta_spo2):.1f}% across recent readings")
    return min(20.0, extra), "; ".join(notes)


def _feature_vector(vitals: dict[str, Any]) -> np.ndarray:
    return np.array([[float(vitals.get(c, 0.0)) for c in FEATURE_COLUMNS]], dtype=np.float32)


class RiskEngine:
    """Loads RF + LSTM artifacts and computes ensemble HRI."""

    def __init__(self) -> None:
        self.rf = None
        self.lstm = None
        self.scaler = None
        self._history: list[list[float]] = []
        self.reload()

    def reload(self) -> None:
        self.rf = None
        self.lstm = None
        self.scaler = None
        if RF_MODEL_PATH.exists():
            try:
                self.rf = joblib.load(RF_MODEL_PATH)
            except Exception:
                self.rf = None
        if LSTM_SCALER_PATH.exists():
            try:
                self.scaler = joblib.load(LSTM_SCALER_PATH)
            except Exception:
                self.scaler = None
        if LSTM_MODEL_PATH.exists():
            try:
                # Lazy import keeps FastAPI boot light when TF is heavy
                from tensorflow import keras

                self.lstm = keras.models.load_model(LSTM_MODEL_PATH)
            except Exception:
                self.lstm = None

    def _rf_score(self, vitals: dict[str, Any]) -> float | None:
        if self.rf is None:
            return None
        x = _feature_vector(vitals)
        if hasattr(self.rf, "predict_proba"):
            proba = self.rf.predict_proba(x)[0]
            # Assume class 1 = elevated risk if binary; else weighted by class index
            if len(proba) == 2:
                return _clip_hri(float(proba[1]) * 100)
            classes = getattr(self.rf, "classes_", np.arange(len(proba)))
            weighted = float(np.dot(proba, np.asarray(classes, dtype=float)))
            return _clip_hri(weighted)
        pred = float(self.rf.predict(x)[0])
        return _clip_hri(pred)

    def _lstm_score(self, vitals: dict[str, Any]) -> float | None:
        if self.lstm is None or self.scaler is None:
            return None
        vec = [float(vitals.get(c, 0.0)) for c in FEATURE_COLUMNS]
        self._history.append(vec)
        if len(self._history) > LSTM_SEQ_LEN:
            self._history = self._history[-LSTM_SEQ_LEN:]
        if len(self._history) < LSTM_SEQ_LEN:
            # Pad with earliest observation
            pad = [self._history[0]] * (LSTM_SEQ_LEN - len(self._history))
            seq = pad + self._history
        else:
            seq = self._history
        arr = np.asarray(seq, dtype=np.float32)
        flat = arr.reshape(-1, arr.shape[-1])
        scaled = self.scaler.transform(flat).reshape(1, LSTM_SEQ_LEN, len(FEATURE_COLUMNS))
        pred = float(self.lstm.predict(scaled, verbose=0)[0][0])
        # Model trained to emit 0–1 risk probability
        if pred <= 1.5:
            pred *= 100.0
        return _clip_hri(pred)

    def snapshot_hri(self, vitals: dict[str, Any]) -> tuple[float, str]:
        """Point score for charts. Does not update the LSTM sequence."""
        rf_s = self._rf_score(vitals)
        heur, _, _, _ = explain_vitals(vitals)
        if rf_s is not None:
            hri = _clip_hri(0.45 * rf_s + 0.55 * heur)
        else:
            hri = heur
        if heur >= 75:
            hri = _clip_hri(max(hri, heur))
        hri = round(hri, 2)
        return hri, band_from_hri(hri)

    def assess(self, vitals: dict[str, Any], history: list[dict[str, Any]] | None = None) -> RiskResult:
        rf_s = self._rf_score(vitals)
        lstm_s = self._lstm_score(vitals)
        heur, drivers, profile, profile_label = explain_vitals(vitals)
        trend_pts, trend_note = trend_adjustment(history)

        if rf_s is not None and lstm_s is not None:
            ml = 0.55 * rf_s + 0.45 * lstm_s
            # Keep heuristic as a safety floor so elevated vitals are not missed
            hri = _clip_hri(0.55 * ml + 0.45 * heur)
            method = "rf_lstm_ensemble"
        elif rf_s is not None:
            hri = _clip_hri(0.45 * rf_s + 0.55 * heur)
            method = "random_forest"
        elif lstm_s is not None:
            hri = _clip_hri(0.45 * lstm_s + 0.55 * heur)
            method = "lstm"
        else:
            hri = heur
            method = "heuristic"

        # Extreme vitals must not be diluted by a weak ML score
        if heur >= 75:
            hri = _clip_hri(max(hri, heur))
            method = f"{method}+heuristic_floor"

        if trend_pts:
            hri = _clip_hri(hri + trend_pts)
            method = f"{method}+trend"

        band = band_from_hri(hri)
        return RiskResult(
            hri=round(hri, 2),
            risk_band=band,
            rf_score=None if rf_s is None else round(rf_s, 2),
            lstm_score=None if lstm_s is None else round(lstm_s, 2),
            method=method,
            details={"thresholds": HRI_THRESHOLDS, "heuristic": round(heur, 2)},
            drivers=drivers,
            age_profile=profile,
            age_profile_label=profile_label,
            trend_adjustment=round(trend_pts, 2),
            trend_note=trend_note,
        )


_engine: RiskEngine | None = None


def get_risk_engine() -> RiskEngine:
    global _engine
    if _engine is None:
        _engine = RiskEngine()
    return _engine

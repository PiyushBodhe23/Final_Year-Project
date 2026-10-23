"""Multi-platform wearable payload → unified vital schema."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class NormalizedVitals(BaseModel):
    """Canonical vital schema used across risk, alerts, and chat."""

    timestamp: str
    device_id: str = "unknown"
    platform: str = "unknown"
    heart_rate: float
    spo2: float
    respiratory_rate: float
    temperature: float
    blood_pressure_sys: float
    blood_pressure_dia: float
    steps: float = 0.0
    activity: str = "unknown"


# Field aliases commonly seen across Apple Health / Fitbit / Garmin exports
_ALIASES: dict[str, tuple[str, ...]] = {
    "heart_rate": ("heart_rate", "hr", "HeartRate", "beats_per_minute", "bpm"),
    "spo2": ("spo2", "SpO2", "oxygen_saturation", "oxygenSaturation", "o2_sat"),
    "respiratory_rate": (
        "respiratory_rate",
        "rr",
        "respiration_rate",
        "breathing_rate",
        "RespiratoryRate",
    ),
    "temperature": ("temperature", "temp", "body_temperature", "BodyTemperature"),
    "blood_pressure_sys": (
        "blood_pressure_sys",
        "systolic",
        "bp_sys",
        "SystolicBloodPressure",
        "sys",
    ),
    "blood_pressure_dia": (
        "blood_pressure_dia",
        "diastolic",
        "bp_dia",
        "DiastolicBloodPressure",
        "dia",
    ),
    "steps": ("steps", "step_count", "StepCount", "Steps"),
    "activity": ("activity", "activity_type", "ActivityType", "state"),
    "device_id": ("device_id", "deviceId", "DeviceId", "source_device"),
    "platform": ("platform", "source", "SourceName", "vendor"),
    "timestamp": ("timestamp", "time", "date", "Date", "recorded_at", "startDate"),
}


def _pick(payload: dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    # Nested vitals / metrics blocks
    for nest in ("vitals", "metrics", "data", "values"):
        block = payload.get(nest)
        if isinstance(block, dict):
            for key in keys:
                if key in block and block[key] is not None:
                    return block[key]
    return default


def detect_platform(payload: dict[str, Any]) -> str:
    explicit = _pick(payload, _ALIASES["platform"])
    if explicit:
        return str(explicit).lower()
    blob = " ".join(str(k) for k in payload.keys()).lower()
    if "apple" in blob or "hkquantity" in blob:
        return "apple"
    if "fitbit" in blob:
        return "fitbit"
    if "garmin" in blob:
        return "garmin"
    return "unknown"


def normalize_payload(payload: dict[str, Any]) -> NormalizedVitals:
    """Map a heterogeneous wearable payload into NormalizedVitals."""
    platform = detect_platform(payload)
    ts = _pick(payload, _ALIASES["timestamp"])
    if not ts:
        ts = datetime.now(timezone.utc).isoformat()
    else:
        ts = str(ts)

    return NormalizedVitals(
        timestamp=ts,
        device_id=str(_pick(payload, _ALIASES["device_id"], default="unknown")),
        platform=platform,
        heart_rate=float(_pick(payload, _ALIASES["heart_rate"], default=72)),
        spo2=float(_pick(payload, _ALIASES["spo2"], default=98)),
        respiratory_rate=float(_pick(payload, _ALIASES["respiratory_rate"], default=16)),
        temperature=float(_pick(payload, _ALIASES["temperature"], default=36.6)),
        blood_pressure_sys=float(_pick(payload, _ALIASES["blood_pressure_sys"], default=120)),
        blood_pressure_dia=float(_pick(payload, _ALIASES["blood_pressure_dia"], default=80)),
        steps=float(_pick(payload, _ALIASES["steps"], default=0)),
        activity=str(_pick(payload, _ALIASES["activity"], default="unknown")),
    )


class NormalizeRequest(BaseModel):
    payload: dict[str, Any] = Field(..., description="Raw multi-platform wearable payload")

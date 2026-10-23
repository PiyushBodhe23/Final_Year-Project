"""System thresholds, paths, and environment settings."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "synthetic_vitals.csv"
PATIENT_TRAINING_PATH = PROJECT_ROOT / "data" / "patient_vitals_training.xlsx"
PATIENT_HISTORY_PATH = PROJECT_ROOT / "data" / "patient_history.csv"
PATIENT_HISTORY_FIRST100_PATH = PROJECT_ROOT / "data" / "patient_history_first100.csv"
WEIGHTS_DIR = Path(__file__).resolve().parent / "models" / "weights"
FORECAST_HORIZON_HOURS = int(os.getenv("FORECAST_HORIZON_HOURS", "6"))
RF_MODEL_PATH = WEIGHTS_DIR / "rf_model.pkl"
LSTM_MODEL_PATH = WEIGHTS_DIR / "lstm_model.h5"
LSTM_SCALER_PATH = WEIGHTS_DIR / "lstm_scaler.pkl"

# Health Risk Index bands (0–100)
HRI_THRESHOLDS = {
    "low": (0, 25),
    "moderate": (25, 50),
    "high": (50, 75),
    "critical": (75, 100),
}

# Approximate adult vital ranges used by heuristic fallback & feature flags.
# These are educational bands for the demo, not clinical reference ranges.
VITAL_RANGES = {
    "heart_rate": {"min": 50, "max": 100, "critical_low": 40, "critical_high": 140},
    "spo2": {"min": 95, "max": 100, "critical_low": 90, "critical_high": 100},
    "respiratory_rate": {"min": 12, "max": 20, "critical_low": 8, "critical_high": 30},
    "temperature": {"min": 36.1, "max": 37.2, "critical_low": 35.0, "critical_high": 39.0},
    "blood_pressure_sys": {"min": 90, "max": 130, "critical_low": 80, "critical_high": 180},
    "blood_pressure_dia": {"min": 60, "max": 85, "critical_low": 50, "critical_high": 120},
}

VITAL_LABELS = {
    "heart_rate": "Heart rate",
    "spo2": "SpO₂",
    "respiratory_rate": "Respiratory rate",
    "temperature": "Temperature",
    "blood_pressure_sys": "Systolic BP",
    "blood_pressure_dia": "Diastolic BP",
}

# Same person, different expected resting ranges by age group.
AGE_PROFILE_LABELS = {
    "young_adult": "Under 40",
    "adult": "Adult 40–64",
    "older_adult": "65 and over",
}

ALERT_LOG_PATH = PROJECT_ROOT / "data" / "alert_log.json"
ALERT_COOLDOWN_MINUTES = int(os.getenv("ALERT_COOLDOWN_MINUTES", "10"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")
# Gemini for cloud AI health recommendations (optional — falls back to Ollama / band playbook)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "auto").strip().lower()  # auto | gemini | ollama | rules
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
STREAM_WINDOW = int(os.getenv("STREAM_WINDOW", "60"))

FEATURE_COLUMNS = [
    "heart_rate",
    "spo2",
    "respiratory_rate",
    "temperature",
    "blood_pressure_sys",
    "blood_pressure_dia",
    "steps",
]

LSTM_SEQ_LEN = 10


def age_profile_name(age: object) -> str:
    """Map a numeric age to an educational vital-range profile."""
    try:
        years = int(float(age))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "adult"
    if years <= 0:
        return "adult"
    if years < 40:
        return "young_adult"
    if years >= 65:
        return "older_adult"
    return "adult"


def ranges_for_age(age: object) -> tuple[str, dict[str, dict[str, float]]]:
    """Return (profile name, copied vital ranges) adjusted for age."""
    profile = age_profile_name(age)
    ranges = {key: dict(bounds) for key, bounds in VITAL_RANGES.items()}
    if profile == "young_adult":
        ranges["heart_rate"]["max"] = 110
        ranges["heart_rate"]["critical_high"] = 150
    elif profile == "older_adult":
        ranges["heart_rate"]["max"] = 90
        ranges["heart_rate"]["critical_high"] = 130
        ranges["blood_pressure_sys"]["min"] = 100
        ranges["blood_pressure_sys"]["max"] = 140
        ranges["blood_pressure_dia"]["max"] = 90
    return profile, ranges

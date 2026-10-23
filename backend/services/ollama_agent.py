"""Ollama integration with live vitals, patient history, and forecast injection."""

from __future__ import annotations

import re
from typing import Any

import requests
from pydantic import BaseModel, Field

from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL


DISCLAIMER = (
    "This assistant is for educational demonstration only and is not a medical diagnosis "
    "or substitute for professional clinical advice."
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    patient_id: str | None = None
    vitals: dict[str, Any] | None = None
    hri: float | None = None
    risk_band: str | None = None
    history_text: str | None = None
    forecast_text: str | None = None
    trend_summary: str | None = None
    prediction: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    reply: str
    model: str
    online: bool
    patient_id: str | None = None
    used_history: bool = False
    used_forecast: bool = False
    disclaimer: str = DISCLAIMER


def _compact(text: str | None, max_lines: int = 4) -> str:
    if not text:
        return "none"
    lines = [ln for ln in str(text).splitlines() if ln.strip()]
    return "\n".join(lines[-max_lines:])


def _demo_parts(vitals: dict[str, Any] | None) -> tuple[int | None, str | None]:
    if not vitals:
        return None, None
    age_raw = vitals.get("age")
    gender_raw = str(vitals.get("gender") or "").strip()
    try:
        age = int(age_raw) if age_raw not in (None, "", "nan") else None
    except (TypeError, ValueError):
        age = None
    if age is not None and age <= 0:
        age = None
    gender = gender_raw or None
    if gender and gender.lower() in {"nan", "none", "unknown", "not specified"}:
        gender = None
    return age, gender


def _demo_line(vitals: dict[str, Any] | None) -> str:
    age, gender = _demo_parts(vitals)
    if age is not None and gender:
        return f"Age {age}, gender {gender}."
    if age is not None:
        return f"Age {age}; gender not on file."
    if gender:
        return f"Age not on file; gender {gender}."
    return "Age and gender not on file."


def _patch_missing_demographics(reply: str, vitals: dict[str, Any] | None) -> str:
    """Replace LLM placeholder demographics with values from the patient file."""
    age, gender = _demo_parts(vitals)
    if not reply:
        return reply
    missing = r"(not specified|not mentioned|unknown|n/?a|none|—|-)"
    if age is not None:
        reply = re.sub(rf"(?i)(\bAge\b\s*[:\-]\s*){missing}", rf"\g<1>{age}", reply)
    if gender:
        reply = re.sub(rf"(?i)(\bGender\b\s*[:\-]\s*){missing}", rf"\g<1>{gender}", reply)
    return reply


def _build_system_prompt(
    vitals: dict[str, Any] | None,
    hri: float | None,
    risk_band: str | None,
    patient_id: str | None = None,
    history_text: str | None = None,
    forecast_text: str | None = None,
    trend_summary: str | None = None,
) -> str:
    keys = ("heart_rate", "spo2", "respiratory_rate", "temperature", "blood_pressure_sys", "blood_pressure_dia")
    vitals_block = "none"
    if vitals:
        vitals_block = ", ".join(f"{k}={vitals.get(k)}" for k in keys if k in vitals)
    age, gender = _demo_parts(vitals)
    if age is not None and gender:
        demo = (
            f"KNOWN DEMOGRAPHICS (required): {age}-year-old {gender}. "
            f"Open with that fact. Never write Age/Gender as not specified, unknown, or missing."
        )
        opener = f"Required first clause: This simulated patient is a {age}-year-old {gender}."
    else:
        demo = _demo_line(vitals)
        opener = "Do not invent age or gender."
    return (
        "Health demo assistant. Be brief (4-6 sentences). Not medical advice.\n"
        "Do not use a Patient Analysis / Demographics bullet template.\n"
        f"{opener}\n"
        f"Patient {patient_id or 'unknown'}; {demo} "
        f"HRI {hri if hri is not None else '?'} ({risk_band or '?'}).\n"
        f"Now: {vitals_block}\n"
        f"Trend: {trend_summary or 'n/a'}\n"
        f"Past:\n{_compact(history_text, 3)}\n"
        f"Forecast:\n{_compact(forecast_text, 3)}\n"
    )


def _offline_fallback(
    message: str,
    vitals: dict[str, Any] | None,
    hri: float | None,
    risk_band: str | None,
    patient_id: str | None,
    history_text: str | None,
    forecast_text: str | None,
    trend_summary: str | None,
) -> str:
    parts = [f"Ollama is offline, so here is a local fallback for {patient_id or 'the selected patient'}."]
    parts.append(_demo_line(vitals))
    if trend_summary:
        parts.append(f"Past trend: {trend_summary}")
    if hri is not None:
        parts.append(f"Current simulated HRI is {hri:.0f} ({risk_band or 'unknown'}).")
    if vitals:
        parts.append(
            f"Latest HR={vitals.get('heart_rate')}, SpO2={vitals.get('spo2')}, "
            f"Temp={vitals.get('temperature')}."
        )
    if history_text:
        parts.append("I can see recent past readings in memory for this patient.")
    if forecast_text:
        first = forecast_text.splitlines()[0] if forecast_text.splitlines() else forecast_text
        parts.append(f"Short-horizon forecast starts at: {first}")
    parts.append(f"You asked: {message}")
    parts.append("Rest, hydrate, and contact a clinician if symptoms feel severe.")
    parts.append(DISCLAIMER)
    return "\n\n".join(parts)


def ollama_available(timeout: float = 2.0) -> bool:
    try:
        r = requests.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=timeout)
        return r.ok
    except requests.RequestException:
        return False


def resolve_ollama_model(timeout: float = 3.0) -> str | None:
    """Pick the newest installed Llama model (3.2 > 3.1 > 3), else env default if present."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=timeout)
        r.raise_for_status()
        names = [m.get("name") or m.get("model") or "" for m in r.json().get("models", [])]
    except (requests.RequestException, ValueError, KeyError):
        return None
    if not names:
        return None
    preferred = (
        "llama3.2:1b",
        "llama3.2:3b",
        "llama3.2",
        "llama3.1",
        "llama3",
    )
    for stem in preferred:
        for n in names:
            if n == stem or n.startswith(stem + ":"):
                return n
    if OLLAMA_MODEL in names:
        return OLLAMA_MODEL
    return names[0]


def chat_with_ollama(
    message: str,
    vitals: dict[str, Any] | None = None,
    hri: float | None = None,
    risk_band: str | None = None,
    patient_id: str | None = None,
    history_text: str | None = None,
    forecast_text: str | None = None,
    trend_summary: str | None = None,
    timeout: float = 120.0,
) -> ChatResponse:
    """Call local Ollama with patient history + forecast context."""
    if patient_id:
        try:
            from backend.services.user_store import get_demographics

            demo = get_demographics(patient_id)
            vitals = dict(vitals or {})
            if demo.get("age"):
                vitals["age"] = demo["age"]
            if demo.get("gender"):
                vitals["gender"] = demo["gender"]
        except Exception:
            pass

    system = _build_system_prompt(
        vitals,
        hri,
        risk_band,
        patient_id=patient_id,
        history_text=history_text,
        forecast_text=forecast_text,
        trend_summary=trend_summary,
    )
    age, gender = _demo_parts(vitals)
    user_msg = message
    if age is not None and gender:
        user_msg = (
            f"[Authoritative patient record: {age}-year-old {gender}. "
            f"State these values; do not say they are unspecified.]\n{message}"
        )
    model = resolve_ollama_model() or OLLAMA_MODEL
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "keep_alive": "30m",
        "options": {
            "num_predict": 180,
            "temperature": 0.2,
            "num_ctx": 2048,
        },
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
    }
    used_history = bool(history_text)
    used_forecast = bool(forecast_text)

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        reply = data.get("message", {}).get("content") or data.get("response") or str(data)
        return ChatResponse(
            reply=_patch_missing_demographics(reply.strip(), vitals),
            model=model,
            online=True,
            patient_id=patient_id,
            used_history=used_history,
            used_forecast=used_forecast,
        )
    except (requests.RequestException, ValueError, KeyError):
        return ChatResponse(
            reply=_offline_fallback(
                message,
                vitals,
                hri,
                risk_band,
                patient_id,
                history_text,
                forecast_text,
                trend_summary,
            ),
            model=model,
            online=False,
            patient_id=patient_id,
            used_history=used_history,
            used_forecast=used_forecast,
        )

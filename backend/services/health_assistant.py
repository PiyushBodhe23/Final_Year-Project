"""Patient AI assistant — Gemini (preferred) with band-grounded recommendations.

Recommendations are strictly limited to the provided vitals and Health Risk Index
(HRI) band. This is an educational demo, not clinical advice.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from backend.config import CHAT_PROVIDER, GEMINI_API_KEY, GEMINI_MODEL
from backend.services.ollama_agent import (
    DISCLAIMER,
    ChatRequest,
    ChatResponse,
    _demo_line,
    _demo_parts,
    _patch_missing_demographics,
    chat_with_ollama,
    ollama_available,
)

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "DISCLAIMER",
    "chat_health_assistant",
    "gemini_available",
]


def gemini_available() -> bool:
    return bool((GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or "").strip())


def _normalize_band(risk_band: str | None, hri: float | None) -> str:
    band = (risk_band or "").strip().lower()
    if band in {"low", "moderate", "high", "critical"}:
        return band
    if hri is None:
        return "moderate"
    if hri < 25:
        return "low"
    if hri < 50:
        return "moderate"
    if hri < 75:
        return "high"
    return "critical"


def _vitals_summary(vitals: dict[str, Any] | None) -> str:
    if not vitals:
        return "No current vitals on file."
    keys = (
        ("heart_rate", "Heart rate", "bpm"),
        ("spo2", "SpO2", "%"),
        ("respiratory_rate", "Respiratory rate", "/min"),
        ("temperature", "Temperature", "°C"),
        ("blood_pressure_sys", "Systolic BP", "mmHg"),
        ("blood_pressure_dia", "Diastolic BP", "mmHg"),
        ("steps", "Steps", ""),
    )
    parts = []
    for key, label, unit in keys:
        if key in vitals and vitals.get(key) not in (None, ""):
            parts.append(f"{label}={vitals.get(key)}{(' ' + unit) if unit else ''}")
    age, gender = _demo_parts(vitals)
    if age is not None:
        parts.append(f"Age={age}")
    if gender:
        parts.append(f"Gender={gender}")
    return ", ".join(parts) if parts else "No current vitals on file."


def _band_guidance(band: str) -> dict[str, str]:
    """Crisp guidance by risk band — actions, diet, and when to seek care."""
    guides = {
        "low": {
            "actions": "Maintain routine monitoring. Light activity and regular sleep are fine.",
            "diet": "Balanced meals; adequate water; limit excess salt, sugar, and caffeine.",
            "medical": "No urgent care needed unless new symptoms appear.",
        },
        "moderate": {
            "actions": "Rest more today. Avoid heavy exercise. Recheck vitals in a few hours.",
            "diet": "Light, low-salt meals; hydrate well; avoid alcohol and excess caffeine.",
            "medical": "Contact a caregiver if dizzy, short of breath, or chest discomfort starts.",
        },
        "high": {
            "actions": "Rest immediately. No exertion. Caregiver should check on the patient.",
            "diet": "Small, bland, low-salt meals only if comfortable; sip water; skip stimulants.",
            "medical": "Seek clinical advice today if symptoms persist or worsen.",
        },
        "critical": {
            "actions": "Stop activity now. Rest. Activate caregiver and clinician alert channels.",
            "diet": "Do not force food. Clear fluids only if alert; nothing by mouth if very unwell.",
            "medical": "Seek urgent medical help now if unwell, SpO2 is low, or chest/breathing symptoms occur.",
        },
    }
    return guides.get(band, guides["moderate"])


def _band_playbook(band: str) -> str:
    g = _band_guidance(band)
    return f"Actions: {g['actions']} Diet: {g['diet']} Medical: {g['medical']}"


def _rule_based_reply(
    message: str,
    vitals: dict[str, Any] | None,
    hri: float | None,
    risk_band: str | None,
    patient_id: str | None,
    trend_summary: str | None,
) -> str:
    age, gender = _demo_parts(vitals)
    who = f"Patient {patient_id}" if patient_id else "Patient"
    if age is not None and gender:
        who = f"{who} | {age}y {gender}"

    has_vitals = bool(
        vitals
        and any(
            vitals.get(k) not in (None, "", 0, 0.0)
            for k in (
                "heart_rate",
                "spo2",
                "respiratory_rate",
                "temperature",
                "blood_pressure_sys",
                "blood_pressure_dia",
            )
        )
    )
    if not has_vitals or hri is None:
        lines = [
            f"{who} | Newly enrolled",
            "Status: No wearable readings yet. Past data and risk score are not available.",
            "Actions: Connect a wearable or add live vitals before risk-based advice applies.",
            "Diet: Follow general healthy habits until personal vitals are available.",
            "Medical help: Seek care based on symptoms; this profile has no monitored risk band yet.",
            "Educational demo only - not a diagnosis or prescription.",
        ]
        return "\n".join(lines)

    band = _normalize_band(risk_band, hri)
    g = _band_guidance(band)
    hri_txt = f"{hri:.0f}"
    lines = [
        f"{who} | HRI {hri_txt} | Risk: {band.upper()}",
        f"Vitals: {_vitals_summary(vitals)}",
    ]
    if trend_summary:
        lines.append(f"Trend: {trend_summary}")
    lines.extend(
        [
            f"Actions: {g['actions']}",
            f"Diet: {g['diet']}",
            f"Medical help: {g['medical']}",
            "Educational demo only - not a diagnosis or prescription.",
        ]
    )
    return "\n".join(lines)


def _build_gemini_prompt(
    message: str,
    vitals: dict[str, Any] | None,
    hri: float | None,
    risk_band: str | None,
    patient_id: str | None,
    history_text: str | None,
    forecast_text: str | None,
    trend_summary: str | None,
) -> str:
    band = _normalize_band(risk_band, hri)
    age, gender = _demo_parts(vitals)
    demo = _demo_line(vitals)
    g = _band_guidance(band)
    return f"""You are PulseVanguard AI — a professional clinical-education assistant for a wearable health demo.

STYLE: Crisp, professional, to the point. Short sentences. No fluff. No bullet-template dump unless useful.
OUTPUT FORMAT (always, in this order):
1) One status line: patient + HRI + risk band.
2) Actions: (1–2 sentences)
3) Diet: (1–2 sentences, practical food/hydration advice matching the risk band)
4) Medical help: (when to call caregiver / clinician / urgent care — match band urgency)
5) One-line disclaimer: educational demo only.

STRICT RULES:
- Ground ALL advice only in the vitals and risk band below.
- Do NOT diagnose, name diseases as confirmed, or prescribe drugs/doses.
- Ignore off-topic questions; redirect to vitals/risk advice.
- Use this band guidance: Actions={g['actions']} Diet={g['diet']} Medical={g['medical']}
- Demographics: {demo}

CONTEXT:
- Patient: {patient_id or "unknown"} | Age/gender: {age if age is not None else "n/a"} / {gender or "n/a"}
- HRI: {hri if hri is not None else "n/a"} | Band: {band}
- Vitals: {_vitals_summary(vitals)}
- Trend: {trend_summary or "n/a"}
- History: {(history_text or "none")[:400]}
- Forecast: {(forecast_text or "none")[:300]}

Question: {message}
"""


def _chat_with_gemini(
    message: str,
    vitals: dict[str, Any] | None,
    hri: float | None,
    risk_band: str | None,
    patient_id: str | None,
    history_text: str | None,
    forecast_text: str | None,
    trend_summary: str | None,
    timeout: float = 60.0,
) -> ChatResponse | None:
    key = (GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or "").strip()
    if not key:
        return None
    model = (GEMINI_MODEL or "gemini-2.0-flash").strip()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={key}"
    )
    prompt = _build_gemini_prompt(
        message,
        vitals,
        hri,
        risk_band,
        patient_id,
        history_text,
        forecast_text,
        trend_summary,
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 280,
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ],
    }
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        parts = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        )
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            return None
        text = _patch_missing_demographics(text, vitals)
        if DISCLAIMER.split(".")[0].lower() not in text.lower():
            text = f"{text}\n\n{DISCLAIMER}"
        return ChatResponse(
            reply=text,
            model=model,
            online=True,
            patient_id=patient_id,
            used_history=bool(history_text),
            used_forecast=bool(forecast_text),
        )
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None


def chat_health_assistant(
    message: str,
    vitals: dict[str, Any] | None = None,
    hri: float | None = None,
    risk_band: str | None = None,
    patient_id: str | None = None,
    history_text: str | None = None,
    forecast_text: str | None = None,
    trend_summary: str | None = None,
    timeout: float = 90.0,
) -> ChatResponse:
    """Prefer Gemini → Ollama → rule-based recommendations from vitals + risk band."""
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

    # 1) Gemini (cloud) — natural language, still locked to vitals + risk band
    gemini = _chat_with_gemini(
        message,
        vitals,
        hri,
        risk_band,
        patient_id,
        history_text,
        forecast_text,
        trend_summary,
        timeout=min(timeout, 60.0),
    )
    if gemini is not None:
        return gemini

    # 2) Optional Ollama only when explicitly requested
    provider = (CHAT_PROVIDER or "auto").strip().lower()
    if provider == "ollama" and ollama_available():
        band = _normalize_band(risk_band, hri)
        guided = (
            f"[You MUST give concrete self-care steps for risk band {band}. "
            f"Playbook: {_band_playbook(band)}. "
            f"Educational demo only. Base advice only on vitals + band.]\n{message}"
        )
        try:
            oll = chat_with_ollama(
                guided,
                vitals=vitals,
                hri=hri,
                risk_band=band,
                patient_id=patient_id,
                history_text=history_text,
                forecast_text=forecast_text,
                trend_summary=trend_summary,
                timeout=min(timeout, 45.0),
            )
            reply_l = (oll.reply or "").lower()
            refuses = any(
                s in reply_l
                for s in (
                    "cannot provide medical advice",
                    "i can't provide medical",
                    "i cannot provide",
                )
            )
            if oll.online and oll.reply and len(oll.reply) > 80 and not refuses:
                combined = (
                    f"{oll.reply.strip()}\n\n"
                    f"Risk-band checklist ({band}): {_band_playbook(band)}\n\n{DISCLAIMER}"
                )
                return ChatResponse(
                    reply=_patch_missing_demographics(combined, vitals),
                    model=oll.model,
                    online=True,
                    patient_id=patient_id,
                    used_history=bool(history_text),
                    used_forecast=bool(forecast_text),
                )
        except Exception:
            pass

    # 3) Deterministic recommendations from vitals + risk band (always works)
    return ChatResponse(
        reply=_rule_based_reply(message, vitals, hri, risk_band, patient_id, trend_summary),
        model="band-playbook",
        online=False,
        patient_id=patient_id,
        used_history=bool(history_text),
        used_forecast=bool(forecast_text),
    )

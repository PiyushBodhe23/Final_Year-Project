"""Streamlit chatbot wired to FastAPI /chat with patient history + forecast."""

from __future__ import annotations

from typing import Any

import requests
import streamlit as st


def render_chatbot(
    api_base: str,
    vitals: dict[str, Any] | None = None,
    hri: float | None = None,
    risk_band: str | None = None,
    patient_id: str | None = None,
    history_text: str | None = None,
    forecast_text: str | None = None,
    trend_summary: str | None = None,
) -> None:
    st.markdown(
        '<div class="section-head"><h2>Health assistant</h2>'
        "<p>Ask about this patient's past readings or upcoming risk forecast. Educational demo only.</p></div>",
        unsafe_allow_html=True,
    )

    if patient_id:
        st.caption(f"Context locked to patient **{patient_id}** (history + forecast injected).")

    chat_key = f"chat_messages_{patient_id or 'global'}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("meta"):
                st.caption(msg["meta"])

    placeholder = (
        f"Ask about {patient_id}'s past vitals or future risk…"
        if patient_id
        else "Ask about current vitals or wellness tips…"
    )
    prompt = st.chat_input(placeholder)
    if not prompt:
        return

    st.session_state[chat_key].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    reply = "Unable to reach the API."
    meta = ""
    payload = {
        "message": prompt,
        "patient_id": patient_id,
        "vitals": vitals,
        "hri": hri,
        "risk_band": risk_band,
        "history_text": history_text,
        "forecast_text": forecast_text,
        "trend_summary": trend_summary,
    }

    try:
        resp = requests.post(f"{api_base.rstrip('/')}/chat", json=payload, timeout=90)
        if resp.ok:
            data = resp.json()
            reply = data.get("reply", reply)
            online = data.get("online", False)
            model = data.get("model", "unknown")
            used_h = "history" if data.get("used_history") else "no-history"
            used_f = "forecast" if data.get("used_forecast") else "no-forecast"
            meta = f"Model: {model} · {'online' if online else 'offline fallback'} · {used_h} · {used_f}"
            disclaimer = data.get("disclaimer")
            if disclaimer:
                reply = f"{reply}\n\n_{disclaimer}_"
        else:
            # Local offline path if API is down but we already have context
            reply = _local_fallback(prompt, patient_id, vitals, hri, risk_band, history_text, forecast_text, trend_summary)
            meta = f"API error ({resp.status_code}) · local fallback"
    except requests.RequestException:
        reply = _local_fallback(prompt, patient_id, vitals, hri, risk_band, history_text, forecast_text, trend_summary)
        meta = "API unreachable · local fallback with history/forecast"

    st.session_state[chat_key].append({"role": "assistant", "content": reply, "meta": meta})
    with st.chat_message("assistant"):
        st.markdown(reply)
        if meta:
            st.caption(meta)


def _local_fallback(
    message: str,
    patient_id: str | None,
    vitals: dict[str, Any] | None,
    hri: float | None,
    risk_band: str | None,
    history_text: str | None,
    forecast_text: str | None,
    trend_summary: str | None,
) -> str:
    parts = [f"Local agent reply for **{patient_id or 'patient'}** (API/Ollama unavailable)."]
    if trend_summary:
        parts.append(f"**Past trend:** {trend_summary}")
    if history_text:
        parts.append("I reviewed this patient's recent past readings.")
    if forecast_text:
        first = forecast_text.splitlines()[0]
        parts.append(f"**Forecast peek:** {first}")
    if hri is not None:
        parts.append(f"Current HRI ≈ {hri:.1f} ({risk_band or 'unknown'}).")
    if vitals:
        parts.append(
            f"Latest vitals — HR {vitals.get('heart_rate')}, SpO₂ {vitals.get('spo2')}, "
            f"temp {vitals.get('temperature')}."
        )
    parts.append(f"You asked: {message}")
    parts.append("_Educational demo only — not medical advice._")
    return "\n\n".join(parts)

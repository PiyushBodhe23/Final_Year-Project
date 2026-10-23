"""Streamlit dashboard — per-patient history, forecast, and AI agent context."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.components.alerts_ui import render_alerts_panel
from frontend.components.chatbot import render_chatbot
from frontend.components.metrics import (
    render_history_and_forecast,
    render_trend_charts,
    render_vital_gauges,
)
from frontend.components.theme import band_color, inject_theme

API_DEFAULT = "http://127.0.0.1:8000"
CSV_PATH = ROOT / "data" / "synthetic_vitals.csv"
XLSX_PATH = ROOT / "data" / "patient_vitals_training.xlsx"
DATA_DIR = ROOT / "data"

st.set_page_config(
    page_title="VitaStream · Wearable Health",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _api_get(base: str, path: str, timeout: float = 8.0):
    return requests.get(f"{base.rstrip('/')}{path}", timeout=timeout)


def _api_post(base: str, path: str, payload: dict, timeout: float = 15.0):
    return requests.post(f"{base.rstrip('/')}{path}", json=payload, timeout=timeout)


@st.cache_data(show_spinner=False)
def load_patient_table() -> pd.DataFrame:
    if not XLSX_PATH.exists():
        return pd.DataFrame()
    df = pd.read_excel(XLSX_PATH)
    if "patient_id" in df.columns:
        df["patient_id"] = df["patient_id"].astype(str)
    return df


def row_to_vitals(row: pd.Series) -> dict:
    return {
        "timestamp": str(row.get("timestamp", "")),
        "device_id": str(row.get("patient_id", "unknown")),
        "platform": "training_excel",
        "patient_id": str(row.get("patient_id", "")),
        "heart_rate": float(row.get("heart_rate", 0) or 0),
        "spo2": float(row.get("spo2_level", row.get("spo2", 0)) or 0),
        "oxygen_reading": float(row.get("oxygen_reading", 0) or 0),
        "respiratory_rate": float(row.get("respiratory_rate", 0) or 0),
        "temperature": float(row.get("temperature", 0) or 0),
        "blood_pressure_sys": float(row.get("blood_pressure_sys", 0) or 0),
        "blood_pressure_dia": float(row.get("blood_pressure_dia", 0) or 0),
        "steps": float(row.get("steps", 0) or 0),
        "activity": str(row.get("activity", "unknown")),
        "sepsis_label": int(row.get("sepsis_label", 0) or 0),
    }


def assess_patient(vitals: dict) -> tuple[dict, list[dict]]:
    from backend.models.risk_engine import get_risk_engine
    from backend.services.alert_system import get_recent_alerts, trigger_alerts

    risk = get_risk_engine().assess(vitals).model_dump()
    trigger_alerts(risk["hri"], risk["risk_band"])
    alerts = [a.model_dump() for a in get_recent_alerts(20)]
    return risk, alerts


def load_patient_context(patient_id: str, horizon: int = 6) -> dict:
    from backend.services.patient_memory import build_agent_context

    return build_agent_context(patient_id, horizon_hours=horizon)


def _fallback_stream(limit: int = 60) -> tuple[dict, list[dict], dict]:
    from backend.models.risk_engine import get_risk_engine
    from backend.services.alert_system import get_recent_alerts, trigger_alerts

    df = pd.read_csv(CSV_PATH)
    window = df.tail(limit)
    engine = get_risk_engine()
    stream = []
    for _, row in window.iterrows():
        vitals = row.to_dict()
        risk = engine.assess(vitals)
        stream.append({"vitals": vitals, "risk": risk.model_dump()})
    latest = stream[-1]
    trigger_alerts(latest["risk"]["hri"], latest["risk"]["risk_band"])
    alerts = [a.model_dump() for a in get_recent_alerts(20)]
    return latest["vitals"], stream, {"risk": latest["risk"], "alerts": alerts, "source": "csv"}


def _data_inventory() -> list[tuple[str, str]]:
    files = [
        ("patient_vitals_training.xlsx", "500-patient snapshot Excel"),
        ("patient_history_first100.csv", "History for first 100 patients"),
        ("patient_history_first100.xlsx", "History first 100 (Excel)"),
        ("patient_history.csv", "24h history for all 500 patients"),
        ("synthetic_vitals.csv", "Live demo stream"),
        ("sepsis_dataset.csv", "PhysioNet sepsis training set"),
    ]
    rows = []
    for name, desc in files:
        path = DATA_DIR / name
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            size = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{path.stat().st_size / 1024:.0f} KB"
            rows.append((name, f"{desc} · {size}"))
        else:
            rows.append((name, f"{desc} · missing"))
    return rows


def main() -> None:
    inject_theme()
    patients_df = load_patient_table()

    with st.sidebar:
        st.markdown("### Patient lookup")
        mode = st.radio(
            "View mode",
            ["Select patient", "Live stream"],
            index=0,
            help="Select a patient to load past data + future forecast into the AI agent.",
        )
        horizon = st.slider("Forecast horizon (hours)", 1, 12, 6)

        selected_id = None
        if mode == "Select patient":
            if patients_df.empty:
                st.error("Training Excel missing. Expected `data/patient_vitals_training.xlsx`.")
            else:
                ids = patients_df["patient_id"].tolist()
                search = st.text_input("Search patient ID", placeholder="e.g. P042")
                choices = [pid for pid in ids if search.upper() in pid.upper()] if search.strip() else ids
                if not choices:
                    st.warning("No matching patient IDs.")
                    choices = ids
                selected_id = st.selectbox("Patient ID", choices, index=0)
                st.caption(f"{len(patients_df)} patients · 24h history each")

        st.markdown("---")
        st.markdown("### Controls")
        api_base = st.text_input("API base URL", value=API_DEFAULT)
        window = st.slider("Stream window", min_value=20, max_value=200, value=60, step=10)
        refresh = st.button("Refresh now", type="primary", use_container_width=True)
        st.markdown("---")
        st.markdown("### Data store")
        inventory = _data_inventory()
        lines = "".join(f"<div><code>{n}</code><br/>{d}</div><br/>" for n, d in inventory)
        st.markdown(f'<div class="data-panel">{lines}</div>', unsafe_allow_html=True)

    vitals: dict = {}
    stream: list[dict] = []
    risk: dict = {}
    alerts: list[dict] = []
    source = "patient"
    patient_row = None
    history: list[dict] = []
    prediction: dict | None = None
    history_text = None
    forecast_text = None
    trend_summary = None

    if mode == "Select patient" and selected_id and not patients_df.empty:
        match = patients_df[patients_df["patient_id"] == selected_id]
        if match.empty:
            st.error(f"No data for {selected_id}")
            return
        patient_row = match.iloc[0]
        try:
            ctx = load_patient_context(selected_id, horizon=horizon)
            vitals = ctx["vitals"]
            history = ctx["history"]
            prediction = ctx["prediction"]
            history_text = ctx["history_text"]
            forecast_text = ctx["forecast_text"]
            trend_summary = ctx["trend_summary"]
            risk = {
                "hri": ctx["hri"],
                "risk_band": ctx["risk_band"],
                "method": "history+forecast",
            }
            _, alerts = assess_patient(vitals)
        except Exception as exc:
            st.warning(f"History/forecast unavailable ({exc}); using Excel snapshot.")
            vitals = row_to_vitals(patient_row)
            risk, alerts = assess_patient(vitals)
        stream = [{"vitals": vitals, "risk": risk}]
        source = "patient"
        try:
            _api_post(api_base, "/risk/assess", {"vitals": vitals, "trigger_alert": True}, timeout=3)
        except requests.RequestException:
            pass
    else:
        api_ok = False
        try:
            health = _api_get(api_base, "/health", timeout=3)
            api_ok = health.ok
        except requests.RequestException:
            api_ok = False

        if api_ok:
            try:
                latest_resp = _api_get(api_base, "/vitals/latest")
                stream_resp = _api_get(api_base, f"/vitals/stream?limit={window}")
                latest_resp.raise_for_status()
                stream_resp.raise_for_status()
                data = latest_resp.json()
                vitals = data["vitals"]
                risk = data["risk"]
                stream = stream_resp.json().get("stream", [])
                _api_post(api_base, "/risk/assess", {"vitals": vitals, "trigger_alert": True})
                alerts = _api_get(api_base, "/alerts?limit=20").json()
                source = "api"
            except requests.RequestException as exc:
                st.warning(f"API error, falling back to CSV: {exc}")
                api_ok = False

        if not api_ok:
            try:
                vitals, stream, meta = _fallback_stream(window)
                risk = meta["risk"]
                alerts = meta["alerts"]
                source = "csv"
            except Exception as exc:
                st.error(f"Failed to load vitals: {exc}")
                return

    band = risk.get("risk_band", "unknown")
    hri = float(risk.get("hri", 0) or 0)
    chip_class = "ok" if source in {"api", "patient"} else "warn"
    source_label = {
        "patient": f"Patient {vitals.get('patient_id', selected_id or '—')}",
        "api": "API connected",
        "csv": "CSV fallback",
    }.get(source, source)
    color = band_color(str(band))

    st.markdown(
        f"""
        <div class="hero">
          <p class="brand">Vita<span>Stream</span></p>
          <p class="tagline">Select a patient to review past readings, forecast future risk, and ask the AI agent about that person.</p>
          <div class="status-row">
            <span class="chip {chip_class}">{source_label}</span>
            <span class="chip">{vitals.get('platform', 'device')} · {vitals.get('device_id', '—')}</span>
            <span class="chip">method · {risk.get('method', '—')}</span>
          </div>
        </div>
        <div class="kpi-strip">
          <div class="kpi"><div class="label">Health Risk Index</div><div class="value" style="color:{color}">{hri:.1f}</div><div class="sub">0–100 scale</div></div>
          <div class="kpi"><div class="label">Risk band</div><div class="value" style="color:{color}">{str(band).title()}</div><div class="sub">alert routing</div></div>
          <div class="kpi"><div class="label">Heart rate</div><div class="value">{vitals.get('heart_rate', '—')}</div><div class="sub">bpm</div></div>
          <div class="kpi"><div class="label">SpO₂</div><div class="value">{vitals.get('spo2', '—')}</div><div class="sub">oxygen saturation</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if patient_row is not None:
        st.markdown(
            '<div class="section-head"><h2>Patient snapshot</h2><p>Latest Excel row for this person.</p></div>',
            unsafe_allow_html=True,
        )
        st.dataframe(pd.DataFrame([patient_row]), use_container_width=True, hide_index=True)

    render_vital_gauges(vitals, hri=hri, risk_band=str(band))

    if mode == "Select patient":
        render_history_and_forecast(history, prediction)
    else:
        render_trend_charts(stream)

    left, right = st.columns([1.1, 1], gap="large")
    with left:
        render_alerts_panel(alerts)
    with right:
        render_chatbot(
            api_base,
            vitals=vitals,
            hri=hri,
            risk_band=band,
            patient_id=selected_id if mode == "Select patient" else None,
            history_text=history_text,
            forecast_text=forecast_text,
            trend_summary=trend_summary,
        )

    with st.expander("Browse all patients", expanded=False):
        st.caption("500-patient Excel. Use sidebar to inspect one person's history + forecast.")
        if patients_df.empty:
            st.warning("Training Excel not found in data/.")
        else:
            filter_text = st.text_input("Filter table by patient ID", key="table_filter", placeholder="P0")
            view = patients_df
            if filter_text.strip():
                view = patients_df[patients_df["patient_id"].str.contains(filter_text.strip(), case=False, na=False)]
            st.dataframe(view, use_container_width=True, hide_index=True)

    _ = refresh
    st.markdown(
        '<div class="footer-note">Educational demonstration with synthetic / open research data only. Not for clinical use.</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

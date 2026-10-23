"""Notification panel for simulated 3-way alerts (Patient / Caregiver / Clinician)."""

from __future__ import annotations

from typing import Any

import streamlit as st

CHANNEL_LABELS = {
    "patient": "Patient",
    "caregiver": "Caregiver",
    "clinician": "Clinician",
}

SEVERITY_COLORS = {
    "info": "#1F6F8B",
    "warning": "#C45C26",
    "urgent": "#B33A3A",
    "critical": "#7A1F1F",
}


def render_alerts_panel(alerts: list[dict[str, Any]]) -> None:
    st.markdown(
        '<div class="section-head"><h2>Alert channels</h2>'
        "<p>Simulated Patient / Caregiver / Clinician notifications — nothing is sent externally.</p></div>",
        unsafe_allow_html=True,
    )

    if not alerts:
        st.info("No alerts yet. Refresh vitals to generate notifications.")
        return

    tabs = st.tabs(["All", "Patient", "Caregiver", "Clinician"])
    channels = [None, "patient", "caregiver", "clinician"]

    for tab, channel in zip(tabs, channels):
        with tab:
            filtered = alerts if channel is None else [a for a in alerts if a.get("channel") == channel]
            if not filtered:
                st.write("No alerts for this channel.")
                continue
            for alert in filtered[:12]:
                severity = str(alert.get("severity", "info")).lower()
                color = SEVERITY_COLORS.get(severity, "#14323F")
                ch = CHANNEL_LABELS.get(str(alert.get("channel", "")), alert.get("channel"))
                st.markdown(
                    f"""
                    <div class="alert-item" style="border-left-color:{color};">
                      <div class="alert-meta">{ch} · {severity} · HRI {alert.get('hri', '—')}</div>
                      <div class="alert-title">{alert.get('title', 'Alert')}</div>
                      <div class="alert-body">{alert.get('message', '')}</div>
                      <div class="alert-time">{alert.get('timestamp', '')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

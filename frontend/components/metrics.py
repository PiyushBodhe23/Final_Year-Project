"""Real-time vital gauges and line charts (Plotly)."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

INK = "#14323F"
MUTED = "#5A7380"
ACCENT = "#0F7A6B"
ACCENT2 = "#1F6F8B"
WARM = "#C45C26"
PAPER = "rgba(0,0,0,0)"
PLOT_BG = "rgba(255,255,255,0.35)"
FONT = "Manrope, sans-serif"


def _base_layout(fig: go.Figure, title: str, height: int = 260) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(family="Fraunces, serif", size=18, color=INK), x=0, xanchor="left"),
        height=height,
        margin=dict(l=12, r=12, t=48, b=16),
        paper_bgcolor=PAPER,
        plot_bgcolor=PLOT_BG,
        font=dict(family=FONT, color=INK),
        hovermode="x unified",
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, color=MUTED)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(20,50,63,0.08)", zeroline=False, color=MUTED)
    return fig


def _gauge(title: str, value: float, vmin: float, vmax: float, suffix: str = "", color: str = ACCENT) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": suffix, "font": {"family": "Fraunces, serif", "size": 28, "color": INK}},
            title={"text": title, "font": {"size": 14, "color": MUTED, "family": FONT}},
            gauge={
                "axis": {"range": [vmin, vmax], "tickcolor": MUTED, "tickfont": {"size": 10}},
                "bar": {"color": color, "thickness": 0.28},
                "bgcolor": "rgba(255,255,255,0.55)",
                "borderwidth": 0,
                "steps": [
                    {"range": [vmin, vmin + (vmax - vmin) * 0.55], "color": "rgba(15,122,107,0.08)"},
                    {"range": [vmin + (vmax - vmin) * 0.55, vmax], "color": "rgba(31,111,139,0.10)"},
                ],
            },
        )
    )
    fig.update_layout(height=210, margin=dict(l=14, r=14, t=36, b=8), paper_bgcolor=PAPER, font=dict(family=FONT))
    return fig


def render_vital_gauges(vitals: dict[str, Any], hri: float | None = None, risk_band: str | None = None) -> None:
    st.markdown(
        '<div class="section-head"><h2>Live vitals</h2><p>Current wearable readings from the active stream.</p></div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    specs = [
        ("Heart Rate", float(vitals.get("heart_rate", 0) or 0), 40, 180, " bpm", WARM),
        ("SpO₂", float(vitals.get("spo2", 0) or 0), 85, 100, "%", ACCENT2),
        ("Resp. Rate", float(vitals.get("respiratory_rate", 0) or 0), 8, 35, " /min", ACCENT),
        ("Temperature", float(vitals.get("temperature", 0) or 0), 35, 40, " °C", "#8B5E3C"),
    ]
    for col, (title, val, vmin, vmax, suffix, color) in zip(cols, specs):
        with col:
            st.plotly_chart(_gauge(title, val, vmin, vmax, suffix, color), use_container_width=True)

    if hri is not None:
        band = (risk_band or "low").lower()
        hri_color = {
            "low": ACCENT,
            "moderate": ACCENT2,
            "high": WARM,
            "critical": "#9B2C2C",
        }.get(band, ACCENT)
        st.plotly_chart(
            _gauge("Health Risk Index", float(hri), 0, 100, "", hri_color),
            use_container_width=True,
        )


def render_trend_charts(stream: list[dict[str, Any]]) -> None:
    st.markdown(
        '<div class="section-head"><h2>Trends</h2><p>Recent movement across heart rate, oxygen, and risk.</p></div>',
        unsafe_allow_html=True,
    )
    if not stream:
        st.info("No stream data yet.")
        return

    rows = []
    for item in stream:
        v = item.get("vitals", item)
        risk = item.get("risk", {})
        rows.append(
            {
                "timestamp": v.get("timestamp"),
                "heart_rate": v.get("heart_rate"),
                "spo2": v.get("spo2"),
                "respiratory_rate": v.get("respiratory_rate"),
                "hri": risk.get("hri"),
            }
        )
    df = pd.DataFrame(rows)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    c1, c2 = st.columns(2)
    with c1:
        fig_hr = go.Figure()
        fig_hr.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["heart_rate"],
                mode="lines",
                line=dict(color=WARM, width=2.5),
                fill="tozeroy",
                fillcolor="rgba(196,92,38,0.10)",
            )
        )
        st.plotly_chart(_base_layout(fig_hr, "Heart rate"), use_container_width=True)
    with c2:
        fig_o2 = go.Figure()
        fig_o2.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["spo2"],
                mode="lines",
                line=dict(color=ACCENT2, width=2.5),
                fill="tozeroy",
                fillcolor="rgba(31,111,139,0.10)",
            )
        )
        st.plotly_chart(_base_layout(fig_o2, "SpO₂"), use_container_width=True)

    if df["hri"].notna().any():
        fig_hri = go.Figure()
        fig_hri.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["hri"],
                mode="lines",
                line=dict(color=ACCENT, width=3),
                fill="tozeroy",
                fillcolor="rgba(15,122,107,0.12)",
            )
        )
        st.plotly_chart(_base_layout(fig_hri, "Health Risk Index", height=240), use_container_width=True)


def render_history_and_forecast(
    history: list[dict[str, Any]],
    prediction: dict[str, Any] | None,
) -> None:
    """Show past vitals + dashed future HRI forecast for one patient."""
    st.markdown(
        '<div class="section-head"><h2>Past data & future forecast</h2>'
        "<p>History from this patient's readings, plus a short-horizon risk projection.</p></div>",
        unsafe_allow_html=True,
    )
    if not history:
        st.info("No history for this patient yet.")
        return

    hist_df = pd.DataFrame(history)
    hist_df["timestamp"] = pd.to_datetime(hist_df.get("timestamp"), errors="coerce")

    c1, c2 = st.columns(2)
    with c1:
        fig_hr = go.Figure()
        fig_hr.add_trace(
            go.Scatter(
                x=hist_df["timestamp"],
                y=hist_df["heart_rate"],
                mode="lines+markers",
                name="Past HR",
                line=dict(color=WARM, width=2.5),
            )
        )
        st.plotly_chart(_base_layout(fig_hr, "Heart rate history"), use_container_width=True)
    with c2:
        fig_o2 = go.Figure()
        fig_o2.add_trace(
            go.Scatter(
                x=hist_df["timestamp"],
                y=hist_df["spo2"],
                mode="lines+markers",
                name="Past SpO2",
                line=dict(color=ACCENT2, width=2.5),
            )
        )
        st.plotly_chart(_base_layout(fig_o2, "SpO₂ history"), use_container_width=True)

    if not prediction:
        return

    st.info(prediction.get("trend_summary", ""))
    forecast = prediction.get("forecast") or []
    if not forecast:
        return

    last_ts = hist_df["timestamp"].dropna().iloc[-1] if hist_df["timestamp"].notna().any() else pd.Timestamp.utcnow()
    f_df = pd.DataFrame(forecast)
    f_df["timestamp"] = [last_ts + pd.Timedelta(hours=int(h)) for h in f_df["hour_ahead"]]

    fig = go.Figure()
    # past HRI via engine already in prediction latest; plot forecast only + marker for now
    fig.add_trace(
        go.Scatter(
            x=[last_ts],
            y=[prediction.get("latest_hri")],
            mode="markers",
            name="Now",
            marker=dict(size=10, color=ACCENT),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=f_df["timestamp"],
            y=f_df["predicted_hri"],
            mode="lines+markers",
            name="Forecast HRI",
            line=dict(color=ACCENT, width=3, dash="dash"),
        )
    )
    fig.update_layout(showlegend=True)
    st.plotly_chart(_base_layout(fig, f"HRI forecast (next {prediction.get('horizon_hours', 6)}h)", height=280), use_container_width=True)

    rising = prediction.get("rising_risk")
    if rising:
        st.warning("Forecast suggests rising risk over the next hours (demo estimate).")
    st.dataframe(
        f_df[
            [
                "hour_ahead",
                "heart_rate",
                "spo2",
                "respiratory_rate",
                "temperature",
                "predicted_hri",
                "risk_band",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


"""Shared Streamlit theme CSS and helpers."""

from __future__ import annotations

import streamlit as st

THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Manrope:wght@400;500;600;700&display=swap');

:root {
  --ink: #14323F;
  --muted: #5A7380;
  --accent: #0F7A6B;
  --accent-2: #1F6F8B;
  --warn: #C45C26;
  --danger: #9B2C2C;
  --surface: rgba(255,255,255,0.72);
  --line: rgba(20,50,63,0.12);
  --shadow: 0 18px 50px rgba(20,50,63,0.08);
}

html, body, [class*="css"] {
  font-family: 'Manrope', sans-serif;
  color: var(--ink);
}

.stApp {
  background: linear-gradient(160deg, #5B65DC 0%, #9AA1EB 42%, #EEEFFD 100%);
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { right: 1rem; }

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0F3A44 0%, #14525A 100%);
  border-right: none;
}
section[data-testid="stSidebar"] * { color: #E8F4F2 !important; }
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stNumberInput input {
  background: rgba(255,255,255,0.08) !important;
  border: 1px solid rgba(255,255,255,0.18) !important;
  color: #fff !important;
}
section[data-testid="stSidebar"] div[data-baseweb="slider"] div { background: rgba(255,255,255,0.25); }

.hero {
  padding: 1.4rem 0 0.6rem 0;
  animation: rise 700ms ease-out both;
}
.brand {
  font-family: 'Fraunces', serif;
  font-size: clamp(2.4rem, 4vw, 3.4rem);
  line-height: 1.05;
  letter-spacing: -0.02em;
  margin: 0;
  color: var(--ink);
}
.brand span { color: var(--accent); }
.tagline {
  margin: 0.55rem 0 0 0;
  max-width: 42rem;
  font-size: 1.05rem;
  color: var(--muted);
  font-weight: 500;
}
.status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 1.1rem;
  animation: rise 900ms ease-out both;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  border: 1px solid var(--line);
  background: var(--surface);
  backdrop-filter: blur(8px);
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--ink);
}
.chip.ok { border-color: rgba(15,122,107,0.35); color: var(--accent); }
.chip.warn { border-color: rgba(196,92,38,0.35); color: var(--warn); }

.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.85rem;
  margin: 1.25rem 0 0.4rem 0;
  animation: rise 1000ms ease-out both;
}
.kpi {
  padding: 1rem 1.05rem;
  background: var(--surface);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  backdrop-filter: blur(10px);
}
.kpi .label {
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 700;
}
.kpi .value {
  font-family: 'Fraunces', serif;
  font-size: 1.85rem;
  margin-top: 0.25rem;
  line-height: 1.1;
}
.kpi .sub { margin-top: 0.2rem; font-size: 0.8rem; color: var(--muted); }

.section-head {
  margin: 1.6rem 0 0.75rem 0;
  animation: rise 800ms ease-out both;
}
.section-head h2 {
  font-family: 'Fraunces', serif;
  font-size: 1.55rem;
  margin: 0;
}
.section-head p {
  margin: 0.25rem 0 0 0;
  color: var(--muted);
  font-size: 0.95rem;
}

.alert-item {
  border-left: 4px solid var(--accent);
  padding: 0.85rem 1rem;
  margin-bottom: 0.7rem;
  background: rgba(255,255,255,0.65);
  border-top: 1px solid var(--line);
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}
.alert-meta {
  font-size: 0.75rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 700;
}
.alert-title {
  font-family: 'Fraunces', serif;
  font-size: 1.05rem;
  margin: 0.25rem 0;
}
.alert-body { color: var(--ink); font-size: 0.92rem; line-height: 1.45; }
.alert-time { margin-top: 0.4rem; font-size: 0.75rem; color: var(--muted); }

.data-panel {
  margin-top: 0.8rem;
  padding: 0.85rem 0.95rem;
  border: 1px solid rgba(255,255,255,0.18);
  background: rgba(0,0,0,0.15);
  font-size: 0.84rem;
  line-height: 1.45;
}
.data-panel code {
  color: #B7F0E4 !important;
  background: transparent !important;
}

.footer-note {
  margin-top: 1.5rem;
  padding-top: 0.8rem;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 0.82rem;
}

@keyframes rise {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 900px) {
  .kpi-strip { grid-template-columns: 1fr 1fr; }
}
"""


def inject_theme() -> None:
    st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)


def band_color(band: str) -> str:
    return {
        "low": "#0F7A6B",
        "moderate": "#1F6F8B",
        "high": "#C45C26",
        "critical": "#9B2C2C",
    }.get((band or "").lower(), "#14323F")

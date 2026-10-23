# PreventVital

AI-powered preventive healthcare platform: wearable data + clinical parameters produce an explainable risk range, a patient dashboard, and an AI chatbot.

**Viva framing:** this is an academic prototype built on public and synthetic data. It is a risk screening and awareness tool, not a diagnostic device, and it is not clinically validated.

The phased Cursor prompts that expand this file are the source of the formulas, charts, and chatbot behaviour. Scaffold status is in the README.

## Goals

1. Ingest patient clinical parameters and historical wearable records.
2. Compute diabetes and cardiovascular risk with a transparent method.
3. Present a Low / Moderate / High risk range, an uncertainty interval, and the top contributing factors.
4. Visualise past wearable records as interactive graphs with trends and anomalies.
5. Provide a chatbot that answers from that patient's own data.
6. Ship a demo with datasets, three demo patients, and an explanation of every parameter and formula.

## Stack

Next.js 14 (App Router, TypeScript, Tailwind, shadcn/ui, ECharts) and FastAPI. SQLite for the demo; Postgres via `docker compose --profile postgres`. Models: scikit-learn, XGBoost, SHAP. Chat: provider-agnostic LLM client plus local Chroma/FAISS over short public guideline notes.

The earlier wearable-stream demo remains in `backend/main.py`, `frontend/` (Streamlit), and `web/` (marketing site). New code is `backend/app/`, `ml/`, and `docs/`.

## Risk model (hybrid, per disease)

- Layer A clinical baseline, 0-100. Diabetes: `0.5 * IDRS_scaled + 0.5 * ML_probability * 100` (Indian Diabetes Risk Score plus a calibrated Pima model). Cardiac: calibrated Framingham `TenYearCHD` probability times 100, with an optional point-score cross-check.
- Layer B wearable behaviour score from the last 30 days: `0.30*Activity + 0.25*Cardio + 0.20*Sleep + 0.15*Recovery + 0.10*Oxygen`.
- Layer C: `0.70 * Baseline + 0.30 * WearableScore`, clamped 0-100.
- Bands: 0-29 Low, 30-59 Moderate, 60-100 High. Uncertainty is the 10th-90th percentile. Warn when fewer than 14 wearable days or key labs are missing.
- Weights live only in `backend/app/core/config.py`. They are expert-informed heuristics. A sensitivity analysis (±10%) belongs in the report.

Wearable labels are not real outcomes. Clinical labels come from public datasets. Wearable series are simulated, conditioned on the clinical profile, and checked for realism against public wearable datasets (Fitbit / LifeSnaps). No public dataset links the same person's labs, months of wearables, and disease outcome.

## Demo personas

| Persona | Expected band |
|---|---|
| Priya, 28, F — BMI 22, glucose 88, active, good sleep | Low / Low |
| Rahul, 45, M — BMI 28, waist 98, glucose 112, parent with diabetes, sedentary, rising RHR, poor sleep | Diabetes Moderate-High, Cardiac Moderate |
| Suresh, 58, M — BMI 31, BP 148/94, glucose 132, HbA1c 6.6, LDL 160, smoker, low HRV, low SpO2 nights | High / High |

Plus about 50 random patients for a cohort view.

## Limitations to state before the examiner does

Public datasets are small or demographically narrow (Pima). Wearable data is simulated. Composite weights are not clinically validated. The tool does not diagnose. Future work is an Indian cohort with clinician review, real wearable APIs, and a doctor portal.

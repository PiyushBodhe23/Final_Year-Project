# PreventVital

Academic prototype: clinical parameters plus synthetic wearable history produce an explainable diabetes and cardiovascular **risk range**, with a patient dashboard and a grounded chatbot.

This is a risk-screening and awareness tool. It is not a diagnostic device and it is not clinically validated.

## PreventVital (scaffold)

```bash
pip install -r requirements.txt
python -m backend.app.seed
uvicorn backend.app.main:app --reload --app-dir .
```

Health check: http://127.0.0.1:8000/health

SQLite file: `data/preventvital.db`. Optional Postgres: `docker compose --profile postgres up -d` and set `DATABASE_URL`. Schema migrations: `alembic upgrade head`.

The Next.js marketing site stays in `web/`. Dashboard charts and the chatbot are later phases. The earlier wearable-stream demo (RF + LSTM, Streamlit) is unchanged below.

---

# Wearable Health Framework

End-to-end demo for continuous wearable vital streams: multi-platform normalization, RF + LSTM Health Risk Index (HRI), simulated 3-channel alerts, and an Ollama chatbot with live-data prompt injection.

> **Disclaimer:** Synthetic data only. Not for clinical diagnosis or patient care.

## Project layout

```
wearable-health-framework/
├── .cursorrules
├── requirements.txt
├── README.md
├── data/
│   └── synthetic_vitals.csv
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   ├── train_model.py
│   │   ├── risk_engine.py
│   │   └── weights/
│   └── services/
│       ├── normalizer.py
│       ├── alert_system.py
│       └── ollama_agent.py
└── frontend/
    ├── app.py
    └── components/
        ├── metrics.py
        ├── alerts_ui.py
        └── chatbot.py
```

## Quickstart

### 1. Install

```bash
cd wearable-health-framework
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Train models

```bash
python backend/models/train_model.py
```

Writes `backend/models/weights/rf_model.pkl` and `lstm_model.h5`. If weights are missing at runtime, the risk engine falls back to a rule-based HRI.

### 3. Start API

From the project root:

```bash
uvicorn backend.main:app --reload --app-dir .
```

API docs: http://127.0.0.1:8000/docs

### 4. Start dashboard

```bash
streamlit run frontend/app.py
```

### 5. Optional — Ollama chat

Install [Ollama](https://ollama.com/), pull a model, then ensure it is running:

```bash
ollama pull llama3.2
ollama serve
```

Default endpoint: `http://localhost:11434`. If Ollama is down, the chatbot returns a clear offline fallback.

## Main API routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness |
| GET | `/vitals/latest` | Latest synthetic row + HRI |
| GET | `/vitals/stream` | Recent stream window |
| POST | `/normalize` | Normalize Apple / Fitbit / Garmin-style payloads |
| POST | `/risk/assess` | Compute HRI for a vital payload |
| GET | `/alerts` | Current simulated 3-channel alerts |
| POST | `/chat` | Ollama chat with live vitals injected |

## Notes

- Alerts are **simulated** (Patient / Caregiver / Clinician) — nothing is sent externally.
- Use synthetic CSV only; do not point this demo at real PHI.

# Interoperable Wearable Health Data Framework

An end-to-end predictive healthcare monitoring system featuring multi-sensor data normalization, a Composite Health Risk Index (HRI) ensemble engine, automated 3-way alerts, and a live-vitals-aware AI Virtual Health Assistant powered by Ollama.

## Quickstart

1. **Install Ollama & Pull Model:**
   ```bash
   ollama pull llama3
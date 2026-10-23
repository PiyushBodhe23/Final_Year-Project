"""FastAPI entry point — vital stream, risk, alerts, and chat endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.config import (
    CHAT_PROVIDER,
    DATA_PATH,
    FEATURE_COLUMNS,
    FORECAST_HORIZON_HOURS,
    STREAM_WINDOW,
)
from backend.models.risk_engine import RiskResult, get_risk_engine
from backend.services.alert_system import AlertBundle, AlertMessage, get_recent_alerts, trigger_alerts
from backend.services.connectors import (
    DEVICE_SOURCES,
    FETCHERS,
    OAUTH_SOURCES,
    SOURCES,
    complete_oauth,
    connect_source,
    connected_sources,
    disconnect_source,
    fetch_all_connected,
    grant_device_permission,
    start_oauth,
)
from backend.services.normalizer import NormalizeRequest, NormalizedVitals, normalize_payload
from backend.services.health_assistant import (
    ChatRequest,
    ChatResponse,
    chat_health_assistant,
    gemini_available,
)
from backend.services.ollama_agent import ollama_available, resolve_ollama_model
from backend.services.patient_memory import (
    PatientPrediction,
    build_agent_context,
    enroll_patient,
    get_patient_history,
    list_patient_ids,
    predict_patient_future,
)
from backend.services.user_store import (
    ensure_demographics_file,
    get_demographics,
    list_demographics_roster,
    list_users,
    save_api_keys,
)

WEBSITE_DIR = Path(__file__).resolve().parent.parent / "website"

app = FastAPI(
    title="Wearable Health Framework API",
    description="Synthetic wearable vitals, HRI ensemble, simulated alerts, and Ollama chat.",
    version="0.1.0",
)


@app.on_event("startup")
def _startup() -> None:
    ensure_demographics_file()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def allow_embedded_preview(request, call_next):
    """Let Cursor Simple Browser (iframe) load the demo; Chrome is unaffected."""
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "frame-ancestors *;"
    return response


class AssessRequest(BaseModel):
    vitals: dict[str, Any] = Field(..., description="Normalized or raw vital fields")
    trigger_alert: bool = True


def _load_vitals_df() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise HTTPException(status_code=500, detail=f"Dataset missing: {DATA_PATH}")
    return pd.read_csv(DATA_PATH)


def _row_to_vitals(row: pd.Series) -> dict[str, Any]:
    return {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}


@app.get("/")
def root() -> FileResponse:
    page = WEBSITE_DIR / "index.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="Website not found")
    return FileResponse(page)


@app.get("/demo")
def demo_page() -> FileResponse:
    page = WEBSITE_DIR / "demo.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="Demo page not found")
    return FileResponse(page)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "dataset": DATA_PATH.exists(),
        "ollama": ollama_available(),
        "ollama_model": resolve_ollama_model(),
        "gemini": gemini_available(),
        "chat_provider": (
            "gemini"
            if gemini_available()
            else ("ollama" if CHAT_PROVIDER == "ollama" else "band-playbook")
        ),
        "features": FEATURE_COLUMNS,
    }


@app.get("/vitals/latest")
def vitals_latest() -> dict[str, Any]:
    df = _load_vitals_df()
    row = df.iloc[-1]
    vitals = _row_to_vitals(row)
    risk = get_risk_engine().assess(vitals)
    return {"vitals": vitals, "risk": risk.model_dump()}


@app.get("/vitals/stream")
def vitals_stream(limit: int = Query(default=STREAM_WINDOW, ge=1, le=500)) -> dict[str, Any]:
    df = _load_vitals_df()
    window = df.tail(limit)
    records = [_row_to_vitals(r) for _, r in window.iterrows()]
    engine = get_risk_engine()
    scored = []
    for rec in records:
        risk = engine.assess(rec)
        scored.append({"vitals": rec, "risk": risk.model_dump()})
    return {"count": len(scored), "stream": scored}


@app.post("/normalize", response_model=NormalizedVitals)
def normalize(req: NormalizeRequest) -> NormalizedVitals:
    return normalize_payload(req.payload)


@app.post("/risk/assess", response_model=RiskResult)
def risk_assess(req: AssessRequest) -> RiskResult:
    # Accept either already-normalized fields or nested raw payloads
    payload = req.vitals
    if any(k in payload for k in ("hr", "HeartRate", "SpO2", "vitals", "metrics")):
        normalized = normalize_payload(payload).model_dump()
    else:
        normalized = payload
    result = get_risk_engine().assess(normalized)
    if req.trigger_alert:
        trigger_alerts(
            result.hri,
            result.risk_band,
            drivers=[item.model_dump() for item in result.drivers],
        )
    return result


@app.get("/alerts", response_model=list[AlertMessage])
def alerts(limit: int = Query(default=20, ge=1, le=100)) -> list[AlertMessage]:
    return get_recent_alerts(limit)


@app.post("/alerts/trigger", response_model=AlertBundle)
def alerts_trigger(hri: float = Query(..., ge=0, le=100), risk_band: str | None = None) -> AlertBundle:
    return trigger_alerts(hri, risk_band)


@app.get("/patients")
def patients() -> dict[str, Any]:
    roster = list_demographics_roster()
    by_id = {r["patient_id"]: r for r in roster}
    ids = list_patient_ids()
    patients_out = []
    for pid in ids:
        rec = by_id.get(str(pid))
        if rec:
            patients_out.append(rec)
        else:
            patients_out.append({"patient_id": str(pid), "display_name": str(pid), "age": None, "gender": ""})
    return {"count": len(patients_out), "patient_ids": [p["patient_id"] for p in patients_out], "patients": patients_out}


@app.get("/patients/{patient_id}/history")
def patient_history(
    patient_id: str,
    limit: int = Query(default=24, ge=1, le=168),
) -> dict[str, Any]:
    history = get_patient_history(patient_id, limit=limit)
    return {
        "patient_id": patient_id,
        "count": len(history),
        "history": history,
        "is_new": len(history) == 0,
    }


@app.get("/patients/{patient_id}/predict", response_model=PatientPrediction)
def patient_predict(
    patient_id: str,
    horizon_hours: int = Query(default=FORECAST_HORIZON_HOURS, ge=1, le=24),
) -> PatientPrediction:
    try:
        return predict_patient_future(patient_id, horizon_hours=horizon_hours)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    vitals = req.vitals
    hri = req.hri
    band = req.risk_band
    history_text = req.history_text
    forecast_text = req.forecast_text
    trend_summary = req.trend_summary
    patient_id = req.patient_id

    if patient_id:
        try:
            ctx = build_agent_context(patient_id)
            vitals = vitals or ctx["vitals"]
            hri = hri if hri is not None else ctx["hri"]
            band = band or ctx["risk_band"]
            history_text = history_text or ctx.get("history_text") or ctx.get("history_text")
            forecast_text = forecast_text or ctx.get("forecast_text") or ctx.get("forecast_text")
            trend_summary = trend_summary or ctx["trend_summary"]
            # New patients must not inherit another patient's stream vitals
            if ctx.get("is_new"):
                demo = get_demographics(patient_id)
                vitals = {
                    "age": demo.get("age"),
                    "gender": demo.get("gender"),
                    "patient_id": patient_id,
                }
                hri = None
                band = None
                history_text = "Newly enrolled - no past readings."
                forecast_text = "No forecast - waiting for first wearable reading."
                trend_summary = "Newly enrolled patient - no wearable readings yet."
                return chat_health_assistant(
                    req.message,
                    vitals=vitals,
                    hri=hri,
                    risk_band=band,
                    patient_id=patient_id,
                    history_text=history_text,
                    forecast_text=forecast_text,
                    trend_summary=trend_summary,
                )
        except ValueError:
            pass

    if (vitals is None or hri is None) and not patient_id:
        try:
            latest = vitals_latest()
            vitals = vitals or latest["vitals"]
            hri = hri if hri is not None else latest["risk"]["hri"]
            band = band or latest["risk"]["risk_band"]
        except HTTPException:
            pass

    if patient_id:
        demo = get_demographics(patient_id)
        vitals = dict(vitals or {})
        vitals["age"] = demo.get("age", vitals.get("age"))
        vitals["gender"] = demo.get("gender", vitals.get("gender"))

    return chat_health_assistant(
        req.message,
        vitals=vitals,
        hri=hri,
        risk_band=band,
        patient_id=patient_id,
        history_text=history_text,
        forecast_text=forecast_text,
        trend_summary=trend_summary,
    )


class ConnectRequest(BaseModel):
    user_id: str
    source: str
    api_key: str | None = None


class CreateUserRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=80)
    age: int = Field(..., ge=1, le=120)
    gender: str = Field(..., min_length=1)


class SaveKeysRequest(BaseModel):
    user_id: str
    keys: dict[str, str]


@app.get("/connectors")
def list_connectors(user_id: str = Query(default="P001")) -> dict[str, Any]:
    return {"user_id": user_id, "sources": connected_sources(user_id)}


@app.post("/connectors/connect")
def connector_connect(req: ConnectRequest) -> dict[str, Any]:
    if req.source not in SOURCES:
        raise HTTPException(status_code=400, detail=f"Unknown source: {req.source}")
    try:
        if req.source in DEVICE_SOURCES:
            return grant_device_permission(req.user_id, req.source)  # type: ignore[arg-type]
        if req.api_key:
            save_api_keys(req.user_id, {req.source: req.api_key})
        return complete_oauth(req.user_id, req.source, api_key=req.api_key)  # type: ignore[arg-type]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/connectors/disconnect")
def connector_disconnect(req: ConnectRequest) -> dict[str, Any]:
    return disconnect_source(req.user_id, req.source)


@app.get("/connectors/{source}/fetch")
def connector_fetch(
    source: str,
    user_id: str = Query(..., min_length=1),
    limit: int = Query(default=24, ge=1, le=168),
) -> dict[str, Any]:
    fn = FETCHERS.get(source)
    if not fn:
        raise HTTPException(status_code=404, detail=f"Unknown source: {source}")
    try:
        metrics = fn(user_id, limit=limit)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"user_id": user_id, "source": source, "count": len(metrics), "metrics": metrics}


@app.get("/connectors/ingest")
def connector_ingest(
    user_id: str = Query(..., min_length=1),
    limit: int = Query(default=24, ge=1, le=168),
) -> dict[str, Any]:
    metrics = fetch_all_connected(user_id, limit=limit)
    return {"user_id": user_id, "count": len(metrics), "metrics": metrics}


@app.get("/patients/{patient_id}/dashboard")
def patient_dashboard(
    patient_id: str,
    horizon_hours: int = Query(default=FORECAST_HORIZON_HOURS, ge=1, le=24),
) -> dict[str, Any]:
    try:
        ctx = build_agent_context(patient_id, horizon_hours=horizon_hours)
        pred = predict_patient_future(patient_id, horizon_hours=horizon_hours)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    demo = get_demographics(patient_id)
    is_new = bool(ctx.get("is_new"))
    vitals = dict(ctx["vitals"] or {})
    vitals["age"] = demo.get("age")
    vitals["gender"] = demo.get("gender")

    cooldown_note = ""
    if is_new:
        alerts: list[dict[str, Any]] = []
    else:
        bundle = trigger_alerts(
            pred.latest_hri,
            pred.latest_risk_band,
            patient_id=patient_id,
            drivers=pred.drivers,
        )
        alerts = [a.model_dump() for a in bundle.alerts]
        cooldown_note = bundle.cooldown_note

    performance: list[dict[str, Any]] = []
    if not is_new:
        engine = get_risk_engine()
        age = demo.get("age")
        for row in (ctx.get("history") or [])[-16:]:
            sample = dict(row)
            sample["age"] = age
            point_hri, point_band = engine.snapshot_hri(sample)
            performance.append(
                {
                    "timestamp": row.get("timestamp"),
                    "heart_rate": row.get("heart_rate"),
                    "spo2": row.get("spo2"),
                    "hri": point_hri,
                    "risk_band": point_band,
                }
            )

    driver_line = ""
    top_drivers = [d for d in (pred.drivers or []) if float(d.get("points") or 0) >= 1][:3]
    if top_drivers:
        driver_line = " Why this score: " + ", ".join(
            f"{d.get('label')} +{float(d.get('points') or 0):.0f}" for d in top_drivers
        ) + "."
    trend_summary = (ctx["trend_summary"] or "") + driver_line

    return {
        "patient_id": patient_id,
        "vitals": vitals,
        "hri": ctx["hri"],
        "risk_band": ctx["risk_band"],
        "drivers": ctx.get("drivers") or [],
        "age_profile": ctx.get("age_profile") or pred.age_profile,
        "age_profile_label": ctx.get("age_profile_label") or pred.age_profile_label,
        "risk_method": ctx.get("risk_method") or pred.risk_method,
        "trend_note": ctx.get("trend_note") or pred.trend_note,
        "cooldown_note": cooldown_note,
        "trend_summary": trend_summary,
        "history": ctx["history"],
        "history_text": ctx.get("history_text") or ctx.get("history_text"),
        "forecast_text": ctx.get("forecast_text") or ctx.get("forecast_text"),
        "prediction": pred.model_dump(),
        "performance": performance,
        "alerts": alerts,
        "connectors": connected_sources(patient_id),
        "demographics": demo,
        "display_name": demo.get("display_name") or patient_id,
        "is_new": is_new,
    }


@app.get("/users")
def users_list() -> dict[str, Any]:
    return {"count": len(list_users()), "users": list_users()}


@app.post("/users")
def users_create(req: CreateUserRequest) -> dict[str, Any]:
    try:
        return enroll_patient(req.display_name, req.age, req.gender)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/users/keys")
def users_save_keys(req: SaveKeysRequest) -> dict[str, Any]:
    unknown = [k for k in (req.keys or {}) if k not in SOURCES]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown sources: {unknown}")
    status = save_api_keys(req.user_id, req.keys)
    return {"user_id": req.user_id, "credentials": status}


@app.get("/oauth/{source}/start")
def oauth_start(source: str, user_id: str = Query(...)) -> dict[str, Any]:
    if source not in OAUTH_SOURCES:
        raise HTTPException(status_code=400, detail="Source does not use OAuth2")
    try:
        return start_oauth(user_id, source)  # type: ignore[arg-type]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/oauth/{source}/callback")
def oauth_callback(
    source: str,
    user_id: str = Query(...),
    code: str = Query(default="demo_auth_code"),
) -> dict[str, Any]:
    if source not in OAUTH_SOURCES:
        raise HTTPException(status_code=400, detail="Source does not use OAuth2")
    try:
        return complete_oauth(user_id, source, code=code)  # type: ignore[arg-type]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/permissions/{source}/grant")
def permission_grant(source: str, user_id: str = Query(...)) -> dict[str, Any]:
    if source not in DEVICE_SOURCES:
        raise HTTPException(status_code=400, detail="Source is not a device SDK")
    try:
        return grant_device_permission(user_id, source)  # type: ignore[arg-type]
    except ValueError as extra:
        raise HTTPException(status_code=400, detail=str(extra)) from extra

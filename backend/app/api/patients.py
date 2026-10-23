"""Patient, wearable, risk, and methodology routes."""

from __future__ import annotations

from datetime import date

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.config import DISCLAIMER
from backend.app.core.db import get_db
from backend.app.models.tables import ClinicalRecord, Patient, RiskReport, WearableDaily
from backend.app.schemas.patients import (
    ClinicalOut,
    MetricTrendOut,
    PatientCreate,
    PatientDetail,
    PatientSummary,
    RiskOut,
)
from backend.app.services.chatbot.orchestrator import stream_events
from backend.app.services.risk_engine import (
    SUMMARY_METRICS,
    ScoreResult,
    _bmi,
    _wearable_frame,
    calculate_risk,
    latest_results,
    methodology_payload,
    report_to_result,
)
from backend.app.services.wearable_analytics import summarize_metrics
from ml.generate_synthetic import ClinicalProfile, generate_series, _lerp

router = APIRouter(prefix="/api")

WEARABLE_FIELDS = {
    "steps",
    "active_min",
    "calories",
    "rhr",
    "avg_hr",
    "max_hr",
    "hrv_rmssd",
    "spo2_avg",
    "spo2_min",
    "sleep_hours",
    "deep_pct",
    "rem_pct",
    "light_pct",
    "sleep_efficiency",
    "skin_temp_dev",
    "resp_rate",
}


def _patient_or_404(session: Session, patient_id: int) -> Patient:
    patient = session.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail=f"No patient {patient_id}")
    return patient


def _result_payload(result: ScoreResult) -> dict:
    return {
        "disease": result.disease,
        "baseline": result.baseline,
        "wearable_score": result.wearable_score,
        "subscores": result.subscores,
        "composite": result.composite,
        "ci_low": result.ci_low,
        "ci_high": result.ci_high,
        "band": result.band,
        "borderline": result.borderline,
        "confidence": result.confidence,
        "warnings": result.warnings,
        "factors": result.factors,
        "model_version": result.model_version,
        "idrs": result.idrs,
        "point_score": result.point_score,
        "ml_probability": result.ml_probability,
        "disclaimer": result.disclaimer,
    }


@router.get("/patients", response_model=list[PatientSummary])
def list_patients(session: Session = Depends(get_db)) -> list[Patient]:
    """Demo roster. Names other than the three personas are synthetic cohort ids."""
    return session.query(Patient).order_by(Patient.id).all()


@router.post("/patients", response_model=PatientDetail, status_code=201)
def create_patient(payload: PatientCreate, session: Session = Depends(get_db)) -> PatientDetail:
    """Register a new patient with their basic clinical & demographic information.

    Automatically generates 180 days of synthetic continuous wearable telemetry
    and calculates initial Diabetes & Cardiovascular risk screening reports.
    """
    # 1. Create Patient record
    patient = Patient(
        name=payload.name.strip(),
        age=payload.age,
        sex=payload.sex,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        waist_cm=payload.waist_cm,
        smoking=payload.smoking,
        cigs_per_day=payload.cigs_per_day,
        alcohol=payload.alcohol,
        activity_level=payload.activity_level,
        diet_quality=payload.diet_quality,
        stress_level=payload.stress_level,
        family_hx_diabetes=payload.family_hx_diabetes,
        family_hx_cvd=payload.family_hx_cvd,
        bp_meds=payload.bp_meds,
        existing_hypertension=payload.existing_hypertension,
        existing_diabetes=payload.existing_diabetes,
        prior_stroke=payload.prior_stroke,
    )
    session.add(patient)
    session.flush()

    # 2. Create ClinicalRecord with vital baseline
    clinical = ClinicalRecord(
        patient_id=patient.id,
        sys_bp=payload.sys_bp,
        dia_bp=payload.dia_bp,
        fasting_glucose=payload.fasting_glucose,
        hba1c=payload.hba1c,
        total_chol=payload.total_chol,
        hdl=payload.hdl,
        ldl=payload.ldl,
        triglycerides=payload.triglycerides,
    )
    session.add(clinical)
    session.flush()

    # 3. Generate conditioned 180-day synthetic wearable telemetry
    bmi = (payload.weight_kg / ((payload.height_cm / 100) ** 2)) if payload.height_cm and payload.weight_kg else 24.0
    score = (
        0.025 * (payload.age - 45)
        + 0.035 * (bmi - 25)
        + 0.008 * (payload.sys_bp - 120)
        + 0.012 * (payload.fasting_glucose - 100)
        + 0.35 * (1.0 if payload.smoking == "current" else (0.15 if payload.smoking == "former" else 0.0))
        + 0.45 * (1.0 if payload.existing_diabetes else 0.0)
    )
    burden = float(np.clip(1 / (1 + np.exp(-score)), 0.08, 0.92))

    profile = ClinicalProfile(
        name=patient.name,
        age=patient.age,
        sex=patient.sex,
        height_cm=round(payload.height_cm, 1),
        weight_kg=round(payload.weight_kg, 1),
        waist_cm=round(payload.waist_cm, 1),
        smoking=payload.smoking,
        cigs_per_day=payload.cigs_per_day,
        alcohol=payload.alcohol,
        activity_level=payload.activity_level,
        diet_quality=payload.diet_quality,
        stress_level=payload.stress_level,
        family_hx_diabetes=payload.family_hx_diabetes,
        family_hx_cvd=payload.family_hx_cvd,
        bp_meds=payload.bp_meds,
        existing_hypertension=payload.existing_hypertension,
        existing_diabetes=payload.existing_diabetes,
        prior_stroke=payload.prior_stroke,
        sys_bp=payload.sys_bp,
        dia_bp=payload.dia_bp,
        fasting_glucose=payload.fasting_glucose,
        hba1c=payload.hba1c,
        total_chol=payload.total_chol,
        hdl=payload.hdl,
        ldl=payload.ldl,
        triglycerides=payload.triglycerides,
        steps_mean=_lerp(9800, 2600, burden),
        rhr_mean=_lerp(60, 86, burden),
        rhr_rise_30d=_lerp(0, 4, burden) if burden > 0.55 else 0,
        hrv_mean=_lerp(48, 16, burden),
        sleep_mean=_lerp(7.5, 5.2, burden),
        sleep_efficiency_mean=_lerp(89, 68, burden),
        spo2_low_night_rate=_lerp(0.02, 0.24, burden),
        anomaly_blocks=1 if burden < 0.7 else 2,
        seed=10000 + patient.id,
    )

    df = generate_series(profile, n_days=180)

    wearable_records = [
        WearableDaily(
            patient_id=patient.id,
            date=row["date"],
            steps=float(row["steps"]),
            active_min=float(row["active_min"]),
            calories=float(row["calories"]),
            rhr=float(row["rhr"]),
            avg_hr=float(row["avg_hr"]),
            max_hr=float(row["max_hr"]),
            hrv_rmssd=float(row["hrv_rmssd"]),
            spo2_avg=float(row["spo2_avg"]),
            spo2_min=float(row["spo2_min"]),
            sleep_hours=float(row["sleep_hours"]),
            deep_pct=float(row["deep_pct"]),
            rem_pct=float(row["rem_pct"]),
            light_pct=float(row["light_pct"]),
            sleep_efficiency=float(row["sleep_efficiency"]),
            skin_temp_dev=float(row["skin_temp_dev"]),
            resp_rate=float(row["resp_rate"]),
        )
        for _, row in df.iterrows()
    ]
    session.bulk_save_objects(wearable_records)
    session.flush()

    # 4. Calculate Risk Reports
    calculate_risk(session, patient.id)
    session.commit()
    session.refresh(patient)

    return get_patient(patient.id, session)


@router.get("/patients/{patient_id}", response_model=PatientDetail)
def get_patient(patient_id: int, session: Session = Depends(get_db)) -> PatientDetail:
    """Profile and the latest clinical row."""
    patient = _patient_or_404(session, patient_id)
    clinical = (
        session.query(ClinicalRecord)
        .filter(ClinicalRecord.patient_id == patient_id)
        .order_by(ClinicalRecord.recorded_at.desc())
        .first()
    )
    return PatientDetail(
        id=patient.id,
        name=patient.name,
        age=patient.age,
        sex=patient.sex,
        height_cm=patient.height_cm,
        weight_kg=patient.weight_kg,
        waist_cm=patient.waist_cm,
        bmi=None if _bmi(patient) is None else round(_bmi(patient), 1),
        smoking=patient.smoking,
        cigs_per_day=patient.cigs_per_day,
        alcohol=patient.alcohol,
        activity_level=patient.activity_level,
        diet_quality=patient.diet_quality,
        stress_level=patient.stress_level,
        family_hx_diabetes=patient.family_hx_diabetes,
        family_hx_cvd=patient.family_hx_cvd,
        bp_meds=patient.bp_meds,
        existing_hypertension=patient.existing_hypertension,
        existing_diabetes=patient.existing_diabetes,
        prior_stroke=patient.prior_stroke,
        clinical=None
        if clinical is None
        else ClinicalOut(
            recorded_at=clinical.recorded_at,
            sys_bp=clinical.sys_bp,
            dia_bp=clinical.dia_bp,
            fasting_glucose=clinical.fasting_glucose,
            hba1c=clinical.hba1c,
            total_chol=clinical.total_chol,
            hdl=clinical.hdl,
            ldl=clinical.ldl,
            triglycerides=clinical.triglycerides,
        ),
        disclaimer=DISCLAIMER,
    )


@router.get("/patients/{patient_id}/wearables")
def wearables(
    patient_id: int,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    metrics: str | None = None,
    session: Session = Depends(get_db),
) -> dict:
    """Daily wearable rows. `metrics` is a comma-separated column list."""
    _patient_or_404(session, patient_id)
    chosen = [item.strip() for item in metrics.split(",")] if metrics else sorted(WEARABLE_FIELDS)
    unknown = [item for item in chosen if item not in WEARABLE_FIELDS]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown metrics: {', '.join(unknown)}")
    query = session.query(WearableDaily).filter(WearableDaily.patient_id == patient_id)
    if date_from is not None:
        query = query.filter(WearableDaily.date >= date_from)
    if date_to is not None:
        query = query.filter(WearableDaily.date <= date_to)
    rows = query.order_by(WearableDaily.date).all()
    return {
        "patient_id": patient_id,
        "disclaimer": DISCLAIMER,
        "series": [{**{"date": row.date.isoformat()}, **{name: getattr(row, name) for name in chosen}} for row in rows],
    }


@router.get("/patients/{patient_id}/wearables/summary", response_model=list[MetricTrendOut])
def wearable_summary(patient_id: int, session: Session = Depends(get_db)) -> list[MetricTrendOut]:
    """30-day means, trend arrows, and multi-day anomalies."""
    _patient_or_404(session, patient_id)
    rows = session.query(WearableDaily).filter(WearableDaily.patient_id == patient_id).all()
    trends = summarize_metrics(_wearable_frame(rows), SUMMARY_METRICS)
    return [
        MetricTrendOut(
            metric=item.metric,
            mean_30=round(item.mean_30, 2),
            mean_7=round(item.mean_7, 2),
            slope_per_day=round(item.slope_per_day, 4),
            trend=item.trend,
            anomaly_dates=item.anomaly_dates,
        )
        for item in trends
    ]


@router.post("/patients/{patient_id}/risk/calculate", response_model=list[RiskOut])
def risk_calculate(patient_id: int, session: Session = Depends(get_db)) -> list[dict]:
    """Run the composite score and store a report for each disease."""
    _patient_or_404(session, patient_id)
    try:
        results = calculate_risk(session, patient_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [_result_payload(result) for result in results]


@router.get("/patients/{patient_id}/risk/latest", response_model=list[RiskOut])
def risk_latest(patient_id: int, session: Session = Depends(get_db)) -> list[dict]:
    """Most recent stored score for diabetes and cardiovascular disease."""
    _patient_or_404(session, patient_id)
    return latest_results(session, patient_id)


@router.get("/patients/{patient_id}/risk/history", response_model=list[RiskOut])
def risk_history(patient_id: int, session: Session = Depends(get_db)) -> list[dict]:
    """Every stored score, oldest first."""
    _patient_or_404(session, patient_id)
    reports = (
        session.query(RiskReport)
        .filter(RiskReport.patient_id == patient_id)
        .order_by(RiskReport.generated_at, RiskReport.id)
        .all()
    )
    return [report_to_result(report) for report in reports]


class WhatIfBody(BaseModel):
    """Slider values. Omitted fields keep the stored patient data."""

    fasting_glucose: float | None = Field(default=None, ge=50, le=400)
    steps: float | None = Field(default=None, ge=0, le=30000)
    sleep_hours: float | None = Field(default=None, ge=0, le=14)


class ChatBody(BaseModel):
    """One patient-scoped chat turn."""

    patient_id: int
    message: str = Field(min_length=1, max_length=2000)


@router.post("/patients/{patient_id}/risk/what-if", response_model=list[RiskOut])
def risk_what_if(patient_id: int, body: WhatIfBody, session: Session = Depends(get_db)) -> list[dict]:
    """Recompute scores for the sliders without storing a new report."""
    _patient_or_404(session, patient_id)
    results = calculate_risk(
        session,
        patient_id,
        persist=False,
        fasting_glucose=body.fasting_glucose,
        steps=body.steps,
        sleep_hours=body.sleep_hours,
    )
    return [_result_payload(result) for result in results]


@router.post("/chat")
def chat(body: ChatBody, session: Session = Depends(get_db)) -> StreamingResponse:
    """Stream a grounded reply. Emergency phrases return the 112 message only."""
    _patient_or_404(session, body.patient_id)
    return StreamingResponse(
        stream_events(session, body.patient_id, body.message),
        media_type="text/event-stream",
    )


@router.get("/methodology")
def methodology() -> dict:
    """Weights, IDRS table, and band cut-offs. The page should quote these, not hardcode them."""
    return methodology_payload()

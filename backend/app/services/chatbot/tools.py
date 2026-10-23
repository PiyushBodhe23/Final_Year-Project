"""Patient tools. Every number in a chat answer must come from one of these."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.config import (
    SLEEP_HOURS_LOW,
    SPO2_THRESHOLD,
    STEPS_HEALTHY,
    WEARABLE_WINDOW_DAYS,
)
from backend.app.models.tables import ClinicalRecord, Patient, WearableDaily
from backend.app.services.risk_engine import (
    SUMMARY_METRICS,
    _bmi,
    _wearable_frame,
    calculate_risk,
    latest_results,
)
from backend.app.services.wearable_analytics import summarize_metrics


@dataclass
class ToolResult:
    """One tool call, kept for the Sources panel and audit log."""

    name: str
    payload: dict[str, Any]


def _ensure_scores(session: Session, patient_id: int) -> list[dict]:
    scores = latest_results(session, patient_id)
    if not scores:
        calculate_risk(session, patient_id)
        scores = latest_results(session, patient_id)
    return scores


def get_patient_summary(session: Session, patient_id: int) -> ToolResult:
    """Demographics plus the latest labs. Missing fields stay null."""
    patient = session.get(Patient, patient_id)
    if patient is None:
        return ToolResult("get_patient_summary", {"error": "unknown patient"})
    clinical = (
        session.query(ClinicalRecord)
        .filter(ClinicalRecord.patient_id == patient_id)
        .order_by(ClinicalRecord.recorded_at.desc())
        .first()
    )
    return ToolResult(
        "get_patient_summary",
        {
            "name": patient.name,
            "age": patient.age,
            "sex": patient.sex,
            "bmi": None if _bmi(patient) is None else round(_bmi(patient), 1),
            "waist_cm": patient.waist_cm,
            "activity_level": patient.activity_level,
            "smoking": patient.smoking,
            "family_hx_diabetes": patient.family_hx_diabetes,
            "fasting_glucose": None if clinical is None else clinical.fasting_glucose,
            "hba1c": None if clinical is None else clinical.hba1c,
            "sys_bp": None if clinical is None else clinical.sys_bp,
            "dia_bp": None if clinical is None else clinical.dia_bp,
            "total_chol": None if clinical is None else clinical.total_chol,
            "ldl": None if clinical is None else clinical.ldl,
            "hdl": None if clinical is None else clinical.hdl,
            "triglycerides": None if clinical is None else clinical.triglycerides,
        },
    )


def get_risk_report(session: Session, patient_id: int, disease: str | None = None) -> ToolResult:
    """Latest composite, band, and top factors for one or both diseases."""
    scores = _ensure_scores(session, patient_id)
    if disease:
        scores = [row for row in scores if row["disease"] == disease]
    compact = [
        {
            "disease": row["disease"],
            "composite": row["composite"],
            "ci_low": row["ci_low"],
            "ci_high": row["ci_high"],
            "band": row["band"],
            "baseline": row["baseline"],
            "wearable_score": row["wearable_score"],
            "subscores": row.get("subscores", {}),
            "factors": row.get("factors", [])[:6],
            "idrs": row.get("idrs"),
            "ml_probability": row.get("ml_probability"),
        }
        for row in scores
    ]
    return ToolResult("get_risk_report", {"reports": compact})


def get_wearable_trend(session: Session, patient_id: int, metric: str | None = None) -> ToolResult:
    """30-day means and trend arrows from the stored daily rows."""
    rows = session.query(WearableDaily).filter(WearableDaily.patient_id == patient_id).all()
    trends = summarize_metrics(_wearable_frame(rows), SUMMARY_METRICS)
    payload = [
        {
            "metric": item.metric,
            "mean_30": round(item.mean_30, 2),
            "mean_7": round(item.mean_7, 2),
            "trend": item.trend,
            "anomaly_days": len(item.anomaly_dates),
        }
        for item in trends
        if metric is None or item.metric == metric
    ]
    return ToolResult("get_wearable_trend", {"window_days": WEARABLE_WINDOW_DAYS, "trends": payload})


def compare_to_target(session: Session, patient_id: int) -> ToolResult:
    """Gaps versus the methodology targets. Positive gap means the person is short of the goal."""
    summary = get_patient_summary(session, patient_id).payload
    trends = get_wearable_trend(session, patient_id).payload["trends"]
    by_metric = {item["metric"]: item for item in trends}
    steps = by_metric.get("steps", {}).get("mean_30")
    sleep = by_metric.get("sleep_hours", {}).get("mean_30")
    spo2 = by_metric.get("spo2_min", {}).get("mean_30")
    rhr = by_metric.get("rhr", {}).get("mean_30")
    gaps = []
    if steps is not None:
        gaps.append({"metric": "steps", "value": steps, "target": STEPS_HEALTHY, "below_target": steps < STEPS_HEALTHY})
    if sleep is not None:
        gaps.append({"metric": "sleep_hours", "value": sleep, "target": SLEEP_HOURS_LOW, "below_target": sleep < SLEEP_HOURS_LOW})
    if spo2 is not None:
        gaps.append({"metric": "spo2_min", "value": spo2, "target": SPO2_THRESHOLD, "below_target": spo2 < SPO2_THRESHOLD})
    if rhr is not None:
        gaps.append({"metric": "rhr", "value": rhr, "target": 75, "below_target": rhr > 75})
    glucose = summary.get("fasting_glucose")
    if glucose is not None:
        gaps.append({"metric": "fasting_glucose", "value": glucose, "target": 99, "below_target": glucose > 99})
    return ToolResult("compare_to_target", {"gaps": gaps, "smoking": summary.get("smoking")})


def select_tools(message: str) -> list[str]:
    """Choose tools from the question. Recommendation and risk inquiries load the rich set."""
    text = message.lower()
    names = ["get_patient_summary", "get_risk_report"]
    if any(word in text for word in ("sleep", "step", "walk", "heart", "rhr", "hrv", "spo2", "oxygen", "trend", "vitals", "wearable")):
        names.append("get_wearable_trend")
    if any(word in text for word in ("why", "level", "risk", "should", "lower", "improve", "recommend", "what can", "how can", "advice", "target", "goal", "change", "diet", "lifestyle")):
        names.extend(["get_wearable_trend", "compare_to_target"])
    return list(dict.fromkeys(names))


def run_tools(session: Session, patient_id: int, message: str) -> list[ToolResult]:
    """Execute the selected tools against this patient's rows only."""
    mapping = {
        "get_patient_summary": lambda: get_patient_summary(session, patient_id),
        "get_risk_report": lambda: get_risk_report(session, patient_id),
        "get_wearable_trend": lambda: get_wearable_trend(session, patient_id),
        "compare_to_target": lambda: compare_to_target(session, patient_id),
    }
    return [mapping[name]() for name in select_tools(message) if name in mapping]

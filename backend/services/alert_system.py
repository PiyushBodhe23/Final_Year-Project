"""3-channel alert trigger: Patient, Caregiver, Clinician (simulated)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.config import ALERT_COOLDOWN_MINUTES, ALERT_LOG_PATH, HRI_THRESHOLDS

Channel = Literal["patient", "caregiver", "clinician"]
Severity = Literal["info", "warning", "urgent", "critical"]

_BAND_RANK = {"low": 0, "moderate": 1, "high": 2, "critical": 3}
_lock = Lock()


class AlertMessage(BaseModel):
    channel: Channel
    severity: Severity
    title: str
    message: str
    hri: float
    risk_band: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    delivered: bool = True  # simulated delivery
    patient_id: str | None = None
    drivers_summary: str = ""


class AlertBundle(BaseModel):
    risk_band: str
    hri: float
    alerts: list[AlertMessage]
    suppressed: bool = False
    cooldown_note: str = ""


def _load_state() -> dict[str, Any]:
    if not ALERT_LOG_PATH.exists():
        return {"history": [], "last_fire": {}}
    try:
        data = json.loads(ALERT_LOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"history": [], "last_fire": {}}
    data.setdefault("history", [])
    data.setdefault("last_fire", {})
    return data


def _save_state(state: dict[str, Any]) -> None:
    ALERT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ALERT_LOG_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _history_from_state(state: dict[str, Any]) -> list[AlertMessage]:
    out: list[AlertMessage] = []
    for item in state.get("history", []):
        try:
            out.append(AlertMessage.model_validate(item))
        except Exception:
            continue
    return out


def band_from_hri(hri: float) -> str:
    hri = max(0.0, min(100.0, float(hri)))
    for name, (lo, hi) in HRI_THRESHOLDS.items():
        if name == "critical" and hri >= lo:
            return name
        if lo <= hri < hi:
            return name
    return "low"


def drivers_summary(drivers: list[dict[str, Any]] | None) -> str:
    """Plain-language line naming the vitals that raised the score."""
    ranked = [
        item
        for item in (drivers or [])
        if float(item.get("points") or 0) >= 1
    ]
    ranked.sort(key=lambda item: float(item.get("points") or 0), reverse=True)
    top = ranked[:3]
    if not top:
        return "Scored vitals are inside the age-adjusted normal range."
    bits = []
    for item in top:
        label = item.get("label") or item.get("key") or "Vital"
        value = item.get("value")
        value_txt = "" if value is None else f" {value:g}"
        bits.append(f"{label}{value_txt}")
    return "Main contributors: " + ", ".join(bits) + "."


def _messages_for_band(
    hri: float,
    band: str,
    *,
    patient_id: str | None,
    summary: str,
) -> list[AlertMessage]:
    ts = datetime.now(timezone.utc).isoformat()
    common = {
        "hri": hri,
        "risk_band": band,
        "timestamp": ts,
        "delivered": True,
        "patient_id": patient_id,
        "drivers_summary": summary,
    }
    why = f" {summary}" if summary else ""

    if band == "low":
        return [
            AlertMessage(
                channel="patient",
                severity="info",
                title="Vitals look stable",
                message=f"Your Health Risk Index is in the low range.{why} Keep your usual routine and stay hydrated.",
                **common,
            )
        ]

    if band == "moderate":
        return [
            AlertMessage(
                channel="patient",
                severity="warning",
                title="Mild elevation detected",
                message=f"Some readings sit outside the expected range for this age group.{why} Rest and recheck in a few hours.",
                **common,
            ),
            AlertMessage(
                channel="caregiver",
                severity="info",
                title="Moderate HRI notice",
                message=f"Patient HRI is {hri:.0f} (moderate).{why} No urgent action; watch the trend.",
                **common,
            ),
        ]

    if band == "high":
        return [
            AlertMessage(
                channel="patient",
                severity="urgent",
                title="Elevated health risk",
                message=f"Your HRI is high.{why} Rest, skip strenuous activity, and contact your care team if you feel worse.",
                **common,
            ),
            AlertMessage(
                channel="caregiver",
                severity="warning",
                title="High HRI — check in",
                message=f"Patient HRI is {hri:.0f} (high).{why} Please check on the patient when you can.",
                **common,
            ),
            AlertMessage(
                channel="clinician",
                severity="warning",
                title="Review recommended",
                message=f"Simulated clinician alert: HRI {hri:.0f}.{why} Review the latest vital stream.",
                **common,
            ),
        ]

    return [
        AlertMessage(
            channel="patient",
            severity="critical",
            title="Critical risk signal",
            message=f"Critical HRI detected.{why} Seek urgent medical attention if you feel unwell. This is a simulation.",
            **common,
        ),
        AlertMessage(
            channel="caregiver",
            severity="critical",
            title="Critical patient alert",
            message=f"Patient HRI is {hri:.0f} (critical).{why} Immediate check-in recommended (simulated).",
            **common,
        ),
        AlertMessage(
            channel="clinician",
            severity="critical",
            title="Escalation — critical HRI",
            message=f"Simulated clinician escalation: HRI {hri:.0f}.{why} Triage the latest vitals.",
            **common,
        ),
    ]


def _should_suppress(state: dict[str, Any], patient_id: str | None, band: str) -> tuple[bool, str]:
    if not patient_id:
        return False, ""
    last = (state.get("last_fire") or {}).get(patient_id)
    if not last:
        return False, ""
    prev_band = str(last.get("band") or "low")
    if _BAND_RANK.get(band, 0) > _BAND_RANK.get(prev_band, 0):
        return False, ""
    try:
        fired_at = datetime.fromisoformat(str(last.get("at")))
    except ValueError:
        return False, ""
    if fired_at.tzinfo is None:
        fired_at = fired_at.replace(tzinfo=timezone.utc)
    quiet_until = fired_at + timedelta(minutes=ALERT_COOLDOWN_MINUTES)
    now = datetime.now(timezone.utc)
    if now < quiet_until:
        mins = max(1, int((quiet_until - now).total_seconds() // 60) + 1)
        return True, f"Same alert held for about {mins} min so it is not repeated."
    return False, ""


def trigger_alerts(
    hri: float,
    risk_band: str | None = None,
    *,
    patient_id: str | None = None,
    drivers: list[dict[str, Any]] | None = None,
) -> AlertBundle:
    """Build simulated alerts. Repeat notices for the same patient are cooled down."""
    band = risk_band or band_from_hri(hri)
    summary = drivers_summary(drivers)
    with _lock:
        state = _load_state()
        suppress, note = _should_suppress(state, patient_id, band)
        history = _history_from_state(state)
        if suppress:
            recent = [item for item in history if item.patient_id == patient_id][-6:]
            return AlertBundle(
                risk_band=band,
                hri=hri,
                alerts=list(reversed(recent)),
                suppressed=True,
                cooldown_note=note,
            )

        alerts = _messages_for_band(hri, band, patient_id=patient_id, summary=summary)
        history.extend(alerts)
        history = history[-200:]
        state["history"] = [item.model_dump() for item in history]
        if patient_id:
            state["last_fire"][patient_id] = {
                "band": band,
                "hri": hri,
                "at": datetime.now(timezone.utc).isoformat(),
            }
        _save_state(state)
    return AlertBundle(risk_band=band, hri=hri, alerts=alerts, suppressed=False, cooldown_note="")


def get_recent_alerts(limit: int = 20, patient_id: str | None = None) -> list[AlertMessage]:
    with _lock:
        history = _history_from_state(_load_state())
    if patient_id:
        history = [item for item in history if item.patient_id == patient_id]
    return list(reversed(history[-limit:]))


def clear_alerts() -> None:
    with _lock:
        _save_state({"history": [], "last_fire": {}})

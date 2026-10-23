"""Demo wearable connectors — unified metric schema from synthetic patient history.

Real OAuth/SDK calls are stubbed: tokens are stored in-memory and readings are
projected from the made-up dataset so the UI can demonstrate multi-app ingest.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel

from backend.services.patient_memory import get_patient_history
from backend.services.user_store import (
    connected_source_ids,
    credential_status,
    has_connection,
    mark_disconnected,
    save_api_keys,
    store_oauth_tokens,
)

Source = Literal[
    "apple_health",
    "fitbit",
    "google_fit",
    "samsung_health",
    "polar",
    "wahoo",
    "huawei",
]

SOURCES: tuple[Source, ...] = (
    "apple_health",
    "fitbit",
    "google_fit",
    "samsung_health",
    "polar",
    "wahoo",
    "huawei",
)

SOURCE_LABELS: dict[str, str] = {
    "apple_health": "Apple Health (HealthKit)",
    "fitbit": "Fitbit Web API",
    "google_fit": "Google Fit REST API",
    "samsung_health": "Samsung Health SDK",
    "polar": "Polar AccessLink",
    "wahoo": "Wahoo Fitness API",
    "huawei": "Huawei Health Kit",
}

# Which metrics each vendor typically exposes (demo mapping)
_SOURCE_METRICS: dict[str, tuple[str, ...]] = {
    "apple_health": ("steps", "heart_rate", "sleep", "calories"),
    "fitbit": ("steps", "heart_rate", "sleep", "calories"),
    "google_fit": ("steps", "heart_rate", "calories"),
    "samsung_health": ("steps", "heart_rate", "sleep"),
    "polar": ("heart_rate", "calories"),
    "wahoo": ("heart_rate", "steps"),
    "huawei": ("steps", "heart_rate", "sleep", "calories"),
}

# In-memory session cache mirrored from SQLite
_tokens: dict[str, dict[str, dict[str, Any]]] = {}

DEVICE_SOURCES = ("apple_health", "samsung_health")
OAUTH_SOURCES = ("fitbit", "google_fit", "polar", "wahoo", "huawei")


class UnifiedMetric(BaseModel):
    user_id: str
    timestamp: str
    metric_type: str
    value: float
    unit: str
    source: str


def _iso(ts: Any) -> str:
    if ts is None:
        return datetime.now(timezone.utc).isoformat()
    if hasattr(ts, "isoformat"):
        return ts.isoformat()
    text = str(ts)
    return text.replace(" ", "T") if "T" not in text[:20] else text


def _kcal_from_steps(steps: float) -> float:
    """Rough demo conversion: ~0.04 kcal per step."""
    return round(max(0.0, steps) * 0.04, 2)


def _sleep_hours_from_activity(activity: str) -> float:
    return 7.4 if str(activity).lower() == "sleep" else 0.0


def _row_to_metrics(row: dict[str, Any], source: str) -> list[dict[str, Any]]:
    uid = str(row.get("patient_id") or row.get("user_id") or "unknown")
    ts = _iso(row.get("timestamp"))
    wanted = _SOURCE_METRICS.get(source, ("heart_rate", "steps"))
    out: list[dict[str, Any]] = []

    mapping = {
        "heart_rate": (float(row.get("heart_rate", 0) or 0), "bpm"),
        "steps": (float(row.get("steps", 0) or 0), "count"),
        "sleep": (_sleep_hours_from_activity(str(row.get("activity", ""))), "hours"),
        "calories": (_kcal_from_steps(float(row.get("steps", 0) or 0)), "kcal"),
        "spo2": (float(row.get("spo2", 0) or 0), "%"),
        "respiratory_rate": (float(row.get("respiratory_rate", 0) or 0), "breaths/min"),
        "temperature": (float(row.get("temperature", 0) or 0), "C"),
    }
    for metric in wanted:
        if metric not in mapping:
            continue
        value, unit = mapping[metric]
        if metric == "sleep" and value <= 0:
            continue
        out.append(
            UnifiedMetric(
                user_id=uid,
                timestamp=ts,
                metric_type=metric,
                value=round(float(value), 2),
                unit=unit,
                source=source,
            ).model_dump()
        )
    return out


def connect_source(user_id: str, source: Source, api_key: str | None = None) -> dict[str, Any]:
    """OAuth2 (Fitbit/Google/Polar/Wahoo/Huawei) or device permission (Apple/Samsung)."""
    if source not in SOURCES:
        raise ValueError(f"Unknown source: {source}")
    if api_key:
        save_api_keys(user_id, {source: api_key})
    mode = "device_permission" if source in DEVICE_SOURCES else "oauth2"
    access = f"access_{source}_{user_id}_{datetime.now(timezone.utc).timestamp():.0f}"
    refresh = f"refresh_{source}_{user_id}"
    store_oauth_tokens(user_id, source, access, refresh, api_key or "")
    blob = {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "Bearer",
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "label": SOURCE_LABELS[source],
        "has_api_key": bool(api_key),
    }
    _tokens.setdefault(user_id, {})[source] = blob
    public = dict(blob)
    public.pop("access_token", None)
    public.pop("refresh_token", None)
    return {"user_id": user_id, "source": source, "connected": True, "auth": mode, "token": public}


def start_oauth(user_id: str, source: Source) -> dict[str, Any]:
    if source not in OAUTH_SOURCES:
        raise ValueError(f"{source} uses device permissions, not OAuth2")
    return {
        "user_id": user_id,
        "source": source,
        "auth_url": f"/oauth/{source}/callback?user_id={user_id}&code=demo_auth_code",
        "flow": "oauth2_authorization_code",
        "note": "Demo callback exchanges code for access + refresh tokens stored encrypted locally.",
    }


def complete_oauth(user_id: str, source: Source, code: str = "demo_auth_code", api_key: str | None = None) -> dict[str, Any]:
    if not code:
        raise ValueError("Missing authorization code")
    return connect_source(user_id, source, api_key=api_key)


def grant_device_permission(user_id: str, source: Source) -> dict[str, Any]:
    if source not in DEVICE_SOURCES:
        raise ValueError(f"{source} is not a device SDK source")
    return connect_source(user_id, source)


def disconnect_source(user_id: str, source: str) -> dict[str, Any]:
    _tokens.get(user_id, {}).pop(source, None)
    mark_disconnected(user_id, source)
    return {"user_id": user_id, "source": source, "connected": False}


def connected_sources(user_id: str) -> list[dict[str, Any]]:
    status = {c["source"]: c for c in credential_status(user_id)}
    mem = _tokens.get(user_id, {})
    return [
        {
            "source": src,
            "label": SOURCE_LABELS[src],
            "connected": bool(status.get(src, {}).get("connected") or src in mem),
            "has_api_key": bool(status.get(src, {}).get("has_api_key")),
            "key_fingerprint": status.get(src, {}).get("key_fingerprint"),
            "auth": "device_permission" if src in DEVICE_SOURCES else "oauth2",
        }
        for src in SOURCES
    ]


def _require_connected(user_id: str, source: Source) -> None:
    if has_connection(user_id, source) or source in _tokens.get(user_id, {}):
        return
    raise PermissionError(f"{source} is not connected for {user_id}")


def _fetch_for_source(user_id: str, source: Source, limit: int = 24) -> list[dict[str, Any]]:
    _require_connected(user_id, source)
    history = get_patient_history(user_id, limit=limit)
    if not history:
        return []
    metrics: list[dict[str, Any]] = []
    for row in history:
        metrics.extend(_row_to_metrics(row, source))
    return metrics


def fetch_apple_health(user_id: str, limit: int = 24) -> list[dict[str, Any]]:
    return _fetch_for_source(user_id, "apple_health", limit)


def fetch_fitbit(user_id: str, limit: int = 24) -> list[dict[str, Any]]:
    return _fetch_for_source(user_id, "fitbit", limit)


def fetch_google_fit(user_id: str, limit: int = 24) -> list[dict[str, Any]]:
    return _fetch_for_source(user_id, "google_fit", limit)


def fetch_samsung_health(user_id: str, limit: int = 24) -> list[dict[str, Any]]:
    return _fetch_for_source(user_id, "samsung_health", limit)


def fetch_polar(user_id: str, limit: int = 24) -> list[dict[str, Any]]:
    return _fetch_for_source(user_id, "polar", limit)


def fetch_wahoo(user_id: str, limit: int = 24) -> list[dict[str, Any]]:
    return _fetch_for_source(user_id, "wahoo", limit)


def fetch_huawei(user_id: str, limit: int = 24) -> list[dict[str, Any]]:
    return _fetch_for_source(user_id, "huawei", limit)


FETCHERS = {
    "apple_health": fetch_apple_health,
    "fitbit": fetch_fitbit,
    "google_fit": fetch_google_fit,
    "samsung_health": fetch_samsung_health,
    "polar": fetch_polar,
    "wahoo": fetch_wahoo,
    "huawei": fetch_huawei,
}


def fetch_all_connected(user_id: str, limit: int = 24) -> list[dict[str, Any]]:
    sources = connected_source_ids(user_id) or list(_tokens.get(user_id, {}).keys())
    merged: list[dict[str, Any]] = []
    for src in sources:
        fn = FETCHERS.get(src)
        if not fn:
            continue
        try:
            merged.extend(fn(user_id, limit=limit))
        except PermissionError:
            continue
    merged.sort(key=lambda m: m.get("timestamp") or "")
    return merged

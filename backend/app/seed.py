"""Load the three demo personas and the synthetic cohort into SQLite.

Re-running replaces PreventVital patients, labs, and wearable days. It does not
touch the older wearable-stream demo database.
"""

from __future__ import annotations

from datetime import datetime, time, timezone

from sqlalchemy import delete

from backend.app.core.config import SYNTHETIC_END
from backend.app.core.db import Base, SessionLocal, engine
from backend.app.models.tables import (
    ChatMessage,
    ChatSession,
    ClinicalRecord,
    Patient,
    RiskReport,
    WearableDaily,
)
from ml.generate_synthetic import ClinicalProfile, all_profiles, generate_series, write_preview


def init_db() -> None:
    """Create tables that the current models declare."""
    Base.metadata.create_all(bind=engine)


def _clear(session) -> None:
    """Remove prior PreventVital rows so persona ids stay Priya=1, Rahul=2, Suresh=3."""
    session.execute(delete(ChatMessage))
    session.execute(delete(ChatSession))
    session.execute(delete(RiskReport))
    session.execute(delete(WearableDaily))
    session.execute(delete(ClinicalRecord))
    session.execute(delete(Patient))


def _insert_profile(session, profile: ClinicalProfile) -> None:
    patient = Patient(
        name=profile.name,
        age=profile.age,
        sex=profile.sex,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        waist_cm=profile.waist_cm,
        smoking=profile.smoking,
        cigs_per_day=profile.cigs_per_day,
        alcohol=profile.alcohol,
        activity_level=profile.activity_level,
        diet_quality=profile.diet_quality,
        stress_level=profile.stress_level,
        family_hx_diabetes=profile.family_hx_diabetes,
        family_hx_cvd=profile.family_hx_cvd,
        bp_meds=profile.bp_meds,
        existing_hypertension=profile.existing_hypertension,
        existing_diabetes=profile.existing_diabetes,
        prior_stroke=profile.prior_stroke,
    )
    session.add(patient)
    session.flush()
    session.add(
        ClinicalRecord(
            patient_id=patient.id,
            recorded_at=_recorded_at(),
            sys_bp=profile.sys_bp,
            dia_bp=profile.dia_bp,
            fasting_glucose=profile.fasting_glucose,
            hba1c=profile.hba1c,
            total_chol=profile.total_chol,
            hdl=profile.hdl,
            ldl=profile.ldl,
            triglycerides=profile.triglycerides,
        )
    )
    frame = generate_series(profile)
    session.add_all(
        [
            WearableDaily(patient_id=patient.id, **row)
            for row in frame.to_dict(orient="records")
        ]
    )


def _recorded_at() -> datetime:
    """Stamp labs on the last day of the wearable window."""
    return datetime.combine(SYNTHETIC_END, time(9, 0), tzinfo=timezone.utc)


def seed() -> int:
    """Replace the PreventVital tables with personas plus the cohort. Returns the patient count."""
    init_db()
    profiles = all_profiles()
    write_preview(profiles)
    with SessionLocal() as session:
        _clear(session)
        for profile in profiles:
            _insert_profile(session, profile)
        session.commit()
        count = session.query(Patient).count()
    print(f"Seeded {count} synthetic patients, 180 wearable days each. Not real patient data.")
    return count


if __name__ == "__main__":
    seed()

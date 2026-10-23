"""Core PreventVital tables.

Clinical rows come from public datasets. Wearable rows are synthetic and
conditioned on those profiles. Nothing here is real protected health information.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.db import Base


class Patient(Base):
    """Demographics, lifestyle, and history used by IDRS and the cardiac model."""

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[str] = mapped_column(String(16), nullable=False)
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    waist_cm: Mapped[float | None] = mapped_column(Float)
    smoking: Mapped[str] = mapped_column(String(32), default="never")
    cigs_per_day: Mapped[float | None] = mapped_column(Float)
    alcohol: Mapped[str] = mapped_column(String(32), default="none")
    activity_level: Mapped[str] = mapped_column(String(32), default="moderate")
    diet_quality: Mapped[str] = mapped_column(String(32), default="average")
    stress_level: Mapped[int | None] = mapped_column(Integer)
    family_hx_diabetes: Mapped[str] = mapped_column(String(32), default="none")
    family_hx_cvd: Mapped[bool] = mapped_column(Boolean, default=False)
    bp_meds: Mapped[bool] = mapped_column(Boolean, default=False)
    existing_hypertension: Mapped[bool] = mapped_column(Boolean, default=False)
    existing_diabetes: Mapped[bool] = mapped_column(Boolean, default=False)
    prior_stroke: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clinical_records: Mapped[list[ClinicalRecord]] = relationship(back_populates="patient")
    wearable_days: Mapped[list[WearableDaily]] = relationship(back_populates="patient")
    risk_reports: Mapped[list[RiskReport]] = relationship(back_populates="patient")
    chat_sessions: Mapped[list[ChatSession]] = relationship(back_populates="patient")


class ClinicalRecord(Base):
    """One lab / measured snapshot. Reference ranges are for display only."""

    __tablename__ = "clinical_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sys_bp: Mapped[float | None] = mapped_column(Float)
    dia_bp: Mapped[float | None] = mapped_column(Float)
    fasting_glucose: Mapped[float | None] = mapped_column(Float)
    hba1c: Mapped[float | None] = mapped_column(Float)
    total_chol: Mapped[float | None] = mapped_column(Float)
    hdl: Mapped[float | None] = mapped_column(Float)
    ldl: Mapped[float | None] = mapped_column(Float)
    triglycerides: Mapped[float | None] = mapped_column(Float)

    patient: Mapped[Patient] = relationship(back_populates="clinical_records")


class WearableDaily(Base):
    """One synthetic day of wearable metrics, conditioned on the clinical profile."""

    __tablename__ = "wearable_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    steps: Mapped[float | None] = mapped_column(Float)
    active_min: Mapped[float | None] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float)
    rhr: Mapped[float | None] = mapped_column(Float)
    avg_hr: Mapped[float | None] = mapped_column(Float)
    max_hr: Mapped[float | None] = mapped_column(Float)
    hrv_rmssd: Mapped[float | None] = mapped_column(Float)
    spo2_avg: Mapped[float | None] = mapped_column(Float)
    spo2_min: Mapped[float | None] = mapped_column(Float)
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    deep_pct: Mapped[float | None] = mapped_column(Float)
    rem_pct: Mapped[float | None] = mapped_column(Float)
    light_pct: Mapped[float | None] = mapped_column(Float)
    sleep_efficiency: Mapped[float | None] = mapped_column(Float)
    skin_temp_dev: Mapped[float | None] = mapped_column(Float)
    resp_rate: Mapped[float | None] = mapped_column(Float)

    patient: Mapped[Patient] = relationship(back_populates="wearable_days")


class RiskReport(Base):
    """Stored composite score, uncertainty interval, and top contributing factors."""

    __tablename__ = "risk_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    disease: Mapped[str] = mapped_column(String(32))
    baseline: Mapped[float] = mapped_column(Float)
    wearable_score: Mapped[float] = mapped_column(Float)
    composite: Mapped[float] = mapped_column(Float)
    ci_low: Mapped[float] = mapped_column(Float)
    ci_high: Mapped[float] = mapped_column(Float)
    band: Mapped[str] = mapped_column(String(16))
    top_factors_json: Mapped[dict | list | None] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(64), default="untrained")

    patient: Mapped[Patient] = relationship(back_populates="risk_reports")


class ChatSession(Base):
    """A conversation bound to one demo patient."""

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped[Patient] = relationship(back_populates="chat_sessions")
    messages: Mapped[list[ChatMessage]] = relationship(back_populates="session")


class ChatMessage(Base):
    """One turn, including which tools the orchestrator called."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    tools_used_json: Mapped[dict | list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[ChatSession] = relationship(back_populates="messages")

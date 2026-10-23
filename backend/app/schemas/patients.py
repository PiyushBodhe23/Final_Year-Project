"""API payloads for patients, wearables, and risk reports."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from backend.app.core.config import DISCLAIMER


class PatientSummary(BaseModel):
    """Row in the demo patient list."""

    id: int
    name: str
    age: int
    sex: str


class PatientCreate(BaseModel):
    """Payload to register a new patient with their basic clinical and demographic data."""

    name: str = Field(..., min_length=2, max_length=120)
    age: int = Field(..., ge=18, le=100)
    sex: str = Field(default="M", pattern="^(M|F|Other)$")
    height_cm: float = Field(default=168.0, ge=100, le=240)
    weight_kg: float = Field(default=68.0, ge=30, le=250)
    waist_cm: float = Field(default=82.0, ge=40, le=180)
    smoking: str = Field(default="never")
    cigs_per_day: float = Field(default=0.0, ge=0)
    alcohol: str = Field(default="none")
    activity_level: str = Field(default="moderate")
    diet_quality: str = Field(default="average")
    stress_level: int = Field(default=4, ge=1, le=10)
    family_hx_diabetes: str = Field(default="none")
    family_hx_cvd: bool = Field(default=False)
    bp_meds: bool = Field(default=False)
    existing_hypertension: bool = Field(default=False)
    existing_diabetes: bool = Field(default=False)
    prior_stroke: bool = Field(default=False)

    # Clinical & Lab Vitals
    sys_bp: float = Field(default=120.0, ge=70, le=240)
    dia_bp: float = Field(default=80.0, ge=40, le=140)
    fasting_glucose: float = Field(default=95.0, ge=50, le=400)
    hba1c: float = Field(default=5.4, ge=4.0, le=15.0)
    total_chol: float = Field(default=190.0, ge=100, le=450)
    hdl: float = Field(default=50.0, ge=15, le=120)
    ldl: float = Field(default=115.0, ge=30, le=300)
    triglycerides: float = Field(default=140.0, ge=30, le=600)


class ClinicalOut(BaseModel):
    """Latest lab snapshot. Reference ranges are for display, not diagnosis."""

    recorded_at: datetime | None = None
    sys_bp: float | None = None
    dia_bp: float | None = None
    fasting_glucose: float | None = None
    hba1c: float | None = None
    total_chol: float | None = None
    hdl: float | None = None
    ldl: float | None = None
    triglycerides: float | None = None


class PatientDetail(PatientSummary):
    """Profile plus the latest clinical row."""

    height_cm: float | None = None
    weight_kg: float | None = None
    waist_cm: float | None = None
    bmi: float | None = None
    smoking: str
    cigs_per_day: float | None = None
    alcohol: str
    activity_level: str
    diet_quality: str
    stress_level: int | None = None
    family_hx_diabetes: str
    family_hx_cvd: bool
    bp_meds: bool
    existing_hypertension: bool
    existing_diabetes: bool
    prior_stroke: bool
    clinical: ClinicalOut | None = None
    disclaimer: str = DISCLAIMER


class FactorOut(BaseModel):
    """One signed contribution on the composite scale."""

    name: str
    detail: str
    points: float


class RiskOut(BaseModel):
    """One disease score. This is a screening range, not a diagnosis."""

    disease: str
    baseline: float
    wearable_score: float
    subscores: dict[str, float]
    composite: float
    ci_low: float
    ci_high: float
    band: str
    borderline: bool
    confidence: str
    warnings: list[str]
    factors: list[FactorOut]
    model_version: str
    idrs: float | None = None
    point_score: float | None = None
    ml_probability: float | None = None
    generated_at: datetime | None = None
    disclaimer: str = DISCLAIMER


class MetricTrendOut(BaseModel):
    """30-day wearable summary for one metric."""

    metric: str
    mean_30: float
    mean_7: float
    slope_per_day: float
    trend: str
    anomaly_dates: list[date] = Field(default_factory=list)

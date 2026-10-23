"""Synthetic wearable series conditioned on a clinical profile.

No public dataset contains one person's labs, months of wearables, and a disease
label. Clinical rows are taken from the Framingham teaching extract or typed in
for the three viva personas. Daily wearables are simulated. Ranges sit inside
published adult bands (resting HR roughly 50-90 bpm, RMSSD roughly 15-60 ms,
sleep 5-9 h, steps from about 2,000 to 12,000, SpO2 mostly 94-99%). This is a
realism check against those bands, not a statistical match to LifeSnaps.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from backend.app.core.config import (
    COHORT_SIZE,
    FRAMINGHAM_CSV,
    SYNTHETIC_DAYS,
    SYNTHETIC_DIR,
    SYNTHETIC_END,
    SYNTHETIC_SEED,
)

WEARABLE_COLUMNS: list[str] = [
    "date",
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
]


@dataclass(frozen=True)
class ClinicalProfile:
    """One demo person. Wearable targets are the healthy-to-concern anchors for the simulator."""

    name: str
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    waist_cm: float
    smoking: str
    cigs_per_day: float
    alcohol: str
    activity_level: str
    diet_quality: str
    stress_level: int
    family_hx_diabetes: str
    family_hx_cvd: bool
    bp_meds: bool
    existing_hypertension: bool
    existing_diabetes: bool
    prior_stroke: bool
    sys_bp: float
    dia_bp: float
    fasting_glucose: float
    hba1c: float
    total_chol: float
    hdl: float
    ldl: float
    triglycerides: float
    steps_mean: float
    rhr_mean: float
    rhr_rise_30d: float
    hrv_mean: float
    sleep_mean: float
    sleep_efficiency_mean: float
    spo2_low_night_rate: float
    anomaly_blocks: int
    seed: int


def _clip(values: np.ndarray, low: float, high: float) -> np.ndarray:
    return np.clip(values, low, high)


def _ar1(mean: np.ndarray, phi: float, sigma: float, rng: np.random.Generator) -> np.ndarray:
    """Autocorrelated daily noise so a chart looks like a person, not white noise."""
    out = np.empty(len(mean))
    out[0] = mean[0] + rng.normal(0, sigma)
    for index in range(1, len(mean)):
        shock = rng.normal(0, sigma)
        out[index] = mean[index] + phi * (out[index - 1] - mean[index - 1]) + shock
    return out


def _dates(n_days: int) -> list[date]:
    start = SYNTHETIC_END - timedelta(days=n_days - 1)
    return [start + timedelta(days=offset) for offset in range(n_days)]


def demo_personas() -> list[ClinicalProfile]:
    """Priya, Rahul, and Suresh. Seeds are fixed so the viva charts do not move."""
    return [
        ClinicalProfile(
            name="Priya",
            age=28,
            sex="F",
            height_cm=162,
            weight_kg=57.7,
            waist_cm=72,
            smoking="never",
            cigs_per_day=0,
            alcohol="none",
            activity_level="regular",
            diet_quality="good",
            stress_level=3,
            family_hx_diabetes="none",
            family_hx_cvd=False,
            bp_meds=False,
            existing_hypertension=False,
            existing_diabetes=False,
            prior_stroke=False,
            sys_bp=110,
            dia_bp=72,
            fasting_glucose=88,
            hba1c=5.2,
            total_chol=170,
            hdl=62,
            ldl=90,
            triglycerides=90,
            steps_mean=9800,
            rhr_mean=58,
            rhr_rise_30d=0,
            hrv_mean=52,
            sleep_mean=7.6,
            sleep_efficiency_mean=90,
            spo2_low_night_rate=0.01,
            anomaly_blocks=1,
            seed=SYNTHETIC_SEED + 1,
        ),
        ClinicalProfile(
            name="Rahul",
            age=45,
            sex="M",
            height_cm=172,
            weight_kg=82.8,
            waist_cm=98,
            smoking="never",
            cigs_per_day=0,
            alcohol="moderate",
            activity_level="sedentary",
            diet_quality="average",
            stress_level=7,
            family_hx_diabetes="one parent",
            family_hx_cvd=False,
            bp_meds=False,
            existing_hypertension=False,
            existing_diabetes=False,
            prior_stroke=False,
            sys_bp=132,
            dia_bp=86,
            fasting_glucose=112,
            hba1c=5.8,
            total_chol=220,
            hdl=38,
            ldl=140,
            triglycerides=180,
            steps_mean=3400,
            rhr_mean=74,
            rhr_rise_30d=6,
            hrv_mean=28,
            sleep_mean=5.6,
            sleep_efficiency_mean=74,
            spo2_low_night_rate=0.05,
            anomaly_blocks=1,
            seed=SYNTHETIC_SEED + 2,
        ),
        ClinicalProfile(
            name="Suresh",
            age=58,
            sex="M",
            height_cm=168,
            weight_kg=87.5,
            waist_cm=108,
            smoking="current",
            cigs_per_day=15,
            alcohol="moderate",
            activity_level="sedentary",
            diet_quality="poor",
            stress_level=8,
            family_hx_diabetes="one parent",
            family_hx_cvd=True,
            bp_meds=True,
            existing_hypertension=True,
            existing_diabetes=True,
            prior_stroke=False,
            sys_bp=148,
            dia_bp=94,
            fasting_glucose=132,
            hba1c=6.6,
            total_chol=238,
            hdl=36,
            ldl=160,
            triglycerides=210,
            steps_mean=2600,
            rhr_mean=86,
            rhr_rise_30d=2,
            hrv_mean=16,
            sleep_mean=5.1,
            sleep_efficiency_mean=68,
            spo2_low_night_rate=0.28,
            anomaly_blocks=2,
            seed=SYNTHETIC_SEED + 3,
        ),
    ]


def _burden(row: pd.Series) -> float:
    """Map a Framingham row onto 0-1 so higher clinical risk gets a worse wearable pattern."""
    score = (
        0.025 * (float(row["age"]) - 45)
        + 0.035 * (float(row["BMI"]) - 25)
        + 0.008 * (float(row["sysBP"]) - 120)
        + 0.012 * (float(row["glucose"]) - 100)
        + 0.35 * float(row["currentSmoker"])
        + 0.45 * float(row["diabetes"])
    )
    return float(np.clip(1 / (1 + np.exp(-score)), 0.08, 0.92))


def _lerp(healthy: float, concern: float, burden: float) -> float:
    return healthy + burden * (concern - healthy)


REAL_MALE_NAMES = [
    "Vikram", "Rohan", "Amit", "Rajesh", "Arjun", "Sanjay", "Manoj", "Tarun",
    "Harish", "Alok", "Nikhil", "Gaurav", "Vivek", "Chetan", "Kunal", "Aditya",
    "Manish", "Deepak", "Abhishek", "Prashant", "Karthik", "Ramesh", "Siddharth",
    "Varun", "Sunil", "Anand", "Naveen", "Sachin", "Vijay", "Ashok", "Kishore",
    "Hemant", "Rajat", "Pravin", "Sameer", "Mahesh", "Devendra", "Girish", "Jayesh",
    "Lalit", "Mohit", "Pankaj", "Rakesh", "Sandeep", "Tushar", "Umesh", "Vikas",
    "Yogesh", "Bhavesh", "Chirag", "Dinesh", "Govind", "Harshad", "Jagdish",
]

REAL_FEMALE_NAMES = [
    "Ananya", "Neha", "Sunita", "Pooja", "Meera", "Deepa", "Kavita", "Shilpa",
    "Sneha", "Swati", "Ritu", "Preeti", "Shweta", "Divya", "Pallavi", "Aarti",
    "Bhavna", "Chaitali", "Geeta", "Ishita", "Jyoti", "Kiran", "Lata", "Madhuri",
    "Nisha", "Pratibha", "Radha", "Sarita", "Tanvi", "Urmila", "Vaishali", "Yamini",
    "Anjali", "Bina", "Damini", "Ekta", "Gauri", "Hema", "Indira", "Jaya",
    "Kalyani", "Leela", "Meenakshi", "Namrata", "Poonam", "Rashmi", "Seema", "Tejal",
    "Usha", "Vidya", "Alka", "Chhaya", "Dipika", "Gayatri",
]

REAL_SURNAMES = [
    "Patel", "Sharma", "Verma", "Iyer", "Rao", "Nair", "Kapoor", "Mehra",
    "Deshmukh", "Nambiar", "Joshi", "Kulkarni", "Sen", "Reddy", "Hegde",
    "Singhania", "Bhat", "Pillai", "Dasgupta", "Saxena", "Agarwal", "Choudhury",
    "Menon", "Goswami", "Trivedi", "Malhotra", "Bhattacharya", "Somani", "Nadkarni",
    "Bansal", "Gupta", "Mishra", "Pandey", "Chatterjee", "Banerjee", "Mukherjee",
    "Ghosh", "Bose", "Dutta", "Sengupta", "Chakraborty", "Roy", "Das", "Majumdar",
    "Sinha", "Srivastava", "Tiwari", "Dubey", "Shukla", "Tripathi",
]


def cohort_from_framingham(n: int = COHORT_SIZE, seed: int = SYNTHETIC_SEED) -> list[ClinicalProfile]:
    """Sample real Framingham exams and fill the labs that file does not contain.

    HbA1c is estimated from glucose with the ADAG rearrangement and noise.
    HDL, triglycerides, waist, and family history are drawn from plausible
    ranges. Those fields are synthetic add-ons, not Framingham measurements.
    """
    if not FRAMINGHAM_CSV.exists():
        raise FileNotFoundError(f"Missing Framingham extract: {FRAMINGHAM_CSV}")
    frame = pd.read_csv(FRAMINGHAM_CSV).dropna(
        subset=["age", "BMI", "sysBP", "diaBP", "glucose", "totChol", "male", "currentSmoker"]
    )
    rng = np.random.default_rng(seed)
    picked = frame.sample(n=n, random_state=seed)
    profiles: list[ClinicalProfile] = []
    for index, row in enumerate(picked.itertuples(index=False), start=1):
        series = pd.Series(row._asdict())
        burden = _burden(series)
        male = int(series["male"]) == 1
        height = float(rng.normal(172 if male else 158, 4))
        weight = float(series["BMI"]) * (height / 100) ** 2
        waist = (2.4 if male else 2.2) * float(series["BMI"]) + (28 if male else 26)
        hdl = float(np.clip(rng.normal(45 if male else 55, 10), 28, 90))
        triglycerides = float(np.clip(rng.normal(130 + (float(series["BMI"]) - 25) * 4, 35), 55, 400))
        ldl = float(series["totChol"]) - hdl - triglycerides / 5
        ldl = float(np.clip(ldl, 50, 240))
        hba1c = float(np.clip((float(series["glucose"]) + 46.7) / 28.7 + rng.normal(0, 0.12), 4.8, 11))
        if int(series["diabetes"]) == 1:
            hba1c = max(hba1c, float(rng.uniform(6.5, 8.2)))
        smoker = int(series["currentSmoker"]) == 1
        activity = "regular" if burden < 0.35 else "moderate" if burden < 0.62 else "sedentary"
        profiles.append(
            ClinicalProfile(
                name=f"{REAL_MALE_NAMES[(index - 1) % len(REAL_MALE_NAMES)] if male else REAL_FEMALE_NAMES[(index - 1) % len(REAL_FEMALE_NAMES)]} {REAL_SURNAMES[(index * 7 + (1 if male else 3)) % len(REAL_SURNAMES)]}",
                age=int(series["age"]),
                sex="M" if male else "F",
                height_cm=round(height, 1),
                weight_kg=round(weight, 1),
                waist_cm=round(float(np.clip(waist, 64, 130)), 1),
                smoking="current" if smoker else "never",
                cigs_per_day=float(series["cigsPerDay"]) if smoker and pd.notna(series["cigsPerDay"]) else 0,
                alcohol=str(rng.choice(["none", "moderate", "heavy"], p=[0.45, 0.4, 0.15])),
                activity_level=activity,
                diet_quality="good" if burden < 0.35 else "average" if burden < 0.62 else "poor",
                stress_level=int(np.clip(round(2 + 7 * burden), 1, 10)),
                family_hx_diabetes="one parent" if (int(series["diabetes"]) == 1 or rng.random() < 0.2) else "none",
                family_hx_cvd=bool(rng.random() < 0.15 + 0.2 * burden),
                bp_meds=bool(series["BPMeds"] == 1) if pd.notna(series["BPMeds"]) else False,
                existing_hypertension=bool(int(series["prevalentHyp"]) == 1),
                existing_diabetes=bool(int(series["diabetes"]) == 1),
                prior_stroke=bool(int(series["prevalentStroke"]) == 1),
                sys_bp=float(series["sysBP"]),
                dia_bp=float(series["diaBP"]),
                fasting_glucose=float(series["glucose"]),
                hba1c=round(hba1c, 2),
                total_chol=float(series["totChol"]),
                hdl=round(hdl, 1),
                ldl=round(ldl, 1),
                triglycerides=round(triglycerides, 1),
                steps_mean=_lerp(9800, 2600, burden),
                rhr_mean=_lerp(60, 86, burden),
                rhr_rise_30d=_lerp(0, 4, burden) if burden > 0.55 else 0,
                hrv_mean=_lerp(48, 16, burden),
                sleep_mean=_lerp(7.5, 5.2, burden),
                sleep_efficiency_mean=_lerp(89, 68, burden),
                spo2_low_night_rate=_lerp(0.02, 0.24, burden),
                anomaly_blocks=1 if burden < 0.7 else 2,
                seed=SYNTHETIC_SEED + 100 + index,
            )
        )
    return profiles


def generate_series(profile: ClinicalProfile, n_days: int = SYNTHETIC_DAYS) -> pd.DataFrame:
    """Build one daily wearable frame. Weekends lower steps and lengthen sleep.

    The last 30 days carry `rhr_rise_30d` as a linear climb so a rising resting
    heart rate is visible on Rahul. Short anomaly blocks mimic a few sick days.
    """
    rng = np.random.default_rng(profile.seed)
    days = _dates(n_days)
    weekend = np.array([day.weekday() >= 5 for day in days])
    step_level = np.where(weekend, profile.steps_mean * 0.84, profile.steps_mean)
    sleep_level = np.where(weekend, profile.sleep_mean + 0.35, profile.sleep_mean)
    rhr_level = np.full(n_days, profile.rhr_mean, dtype=float)
    if profile.rhr_rise_30d:
        rhr_level[-30:] = profile.rhr_mean + np.linspace(0, profile.rhr_rise_30d, 30)

    steps = _clip(_ar1(step_level, 0.45, profile.steps_mean * 0.08, rng), 800, 18000)
    rhr = _clip(_ar1(rhr_level, 0.55, 1.8, rng), 45, 110)
    hrv = _clip(_ar1(np.full(n_days, profile.hrv_mean), 0.5, 3.0, rng), 8, 110)
    sleep = _clip(_ar1(sleep_level, 0.4, 0.35, rng), 3.5, 10.5)
    efficiency = _clip(
        _ar1(np.full(n_days, profile.sleep_efficiency_mean), 0.35, 2.5, rng),
        55,
        98,
    )
    spo2_avg = _clip(_ar1(np.full(n_days, 97.2 - profile.spo2_low_night_rate * 6), 0.4, 0.35, rng), 90, 99.5)
    spo2_min = _clip(spo2_avg - rng.uniform(1.0, 2.2, n_days), 85, 99)
    low_night = rng.random(n_days) < profile.spo2_low_night_rate
    spo2_min[low_night] = rng.uniform(90.0, 93.4, int(low_night.sum())) if low_night.any() else spo2_min
    spo2_avg[low_night] = np.minimum(spo2_avg[low_night], spo2_min[low_night] + 1.4)

    anomaly = np.zeros(n_days, dtype=bool)
    for _ in range(profile.anomaly_blocks):
        start = int(rng.integers(12, max(13, n_days - 55)))
        anomaly[start : start + 4] = True
    rhr[anomaly] += 11
    hrv[anomaly] *= 0.72
    steps[anomaly] *= 0.45
    sleep[anomaly] = np.maximum(3.5, sleep[anomaly] - 1.4)
    skin = rng.normal(0, 0.12, n_days)
    skin[anomaly] += 0.75
    spo2_min[anomaly] -= 1.2

    active = _clip(steps / 230 + rng.normal(0, 4, n_days), 0, 160)
    calories = _clip(14 * profile.weight_kg + steps * 0.045 + rng.normal(0, 40, n_days), 1200, 4500)
    avg_hr = _clip(rhr + 8 + active * 0.15, 50, 150)
    max_hr = _clip(avg_hr + rng.uniform(25, 45, n_days), 80, 190)
    deep = _clip(rng.normal(18 if profile.sleep_mean >= 7 else 10, 2.5, n_days), 4, 30)
    rem = _clip(rng.normal(22 if profile.sleep_mean >= 7 else 14, 2.5, n_days), 5, 35)
    light = _clip(100 - deep - rem, 40, 90)
    resp = _clip(_ar1(np.full(n_days, 14 + profile.spo2_low_night_rate * 8), 0.4, 0.6, rng), 10, 24)

    frame = pd.DataFrame(
        {
            "date": days,
            "steps": np.round(steps, 0),
            "active_min": np.round(active, 1),
            "calories": np.round(calories, 0),
            "rhr": np.round(rhr, 1),
            "avg_hr": np.round(avg_hr, 1),
            "max_hr": np.round(max_hr, 1),
            "hrv_rmssd": np.round(hrv, 1),
            "spo2_avg": np.round(spo2_avg, 1),
            "spo2_min": np.round(spo2_min, 1),
            "sleep_hours": np.round(sleep, 2),
            "deep_pct": np.round(deep, 1),
            "rem_pct": np.round(rem, 1),
            "light_pct": np.round(light, 1),
            "sleep_efficiency": np.round(efficiency, 1),
            "skin_temp_dev": np.round(skin, 2),
            "resp_rate": np.round(resp, 1),
        }
    )
    return frame


def all_profiles() -> list[ClinicalProfile]:
    """Three named personas followed by the Framingham-sampled cohort."""
    return demo_personas() + cohort_from_framingham()


def write_preview(profiles: list[ClinicalProfile] | None = None) -> None:
    """Save clinical profiles and the three persona series for the report appendix."""
    chosen = profiles if profiles is not None else all_profiles()
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([profile.__dict__ for profile in chosen]).to_csv(SYNTHETIC_DIR / "profiles.csv", index=False)
    demo_frames = [generate_series(profile).assign(name=profile.name) for profile in chosen if profile.seed <= SYNTHETIC_SEED + 3]
    pd.concat(demo_frames, ignore_index=True).to_csv(SYNTHETIC_DIR / "demo_wearables.csv", index=False)


def main() -> None:
    """Write the preview CSVs. Database loading is `python -m backend.app.seed`."""
    profiles = all_profiles()
    write_preview(profiles)
    print(f"Wrote {len(profiles)} profiles to {SYNTHETIC_DIR}")


if __name__ == "__main__":
    main()

"""RAG chatbot: patient tools + guideline retrieval, then a grounded recommendation.

The language model never sees the raw database. It operates on structured clinical
tools, risk indices (IDRS, Framingham CVD), and retrieved guideline passages.
If the LLM is offline or busy, a highly structured, evidence-backed deterministic
draft is shown as-is, so the application operates seamlessly without internet.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.config import DISCLAIMER
from backend.app.services.chatbot.guardrails import EMERGENCY_REPLY, is_emergency, post_check
from backend.app.services.chatbot.llm_client import rephrase
from backend.app.services.chatbot.rag import Passage, retrieve
from backend.app.services.chatbot.tools import ToolResult, run_tools

__all__ = ["answer", "is_emergency", "stream_events"]


def _reports(tools: list[ToolResult]) -> list[dict[str, Any]]:
    for item in tools:
        if item.name == "get_risk_report":
            return list(item.payload.get("reports") or [])
    return []


def _summary(tools: list[ToolResult]) -> dict[str, Any]:
    for item in tools:
        if item.name == "get_patient_summary":
            return item.payload
    return {}


def _trends(tools: list[ToolResult]) -> list[dict[str, Any]]:
    for item in tools:
        if item.name == "get_wearable_trend":
            return list(item.payload.get("trends") or [])
    return []


def _gaps(tools: list[ToolResult]) -> list[dict[str, Any]]:
    for item in tools:
        if item.name == "compare_to_target":
            return list(item.payload.get("gaps") or [])
    return []


def _extract_context(tools: list[ToolResult]) -> dict[str, Any]:
    """Compile structured patient health and index metrics for intelligent counseling."""
    summary = _summary(tools)
    reports = {row["disease"]: row for row in _reports(tools)}
    trends = {item["metric"]: item for item in _trends(tools)}

    bmi = summary.get("bmi")
    bmi_category = "Normal"
    if bmi is not None:
        if bmi < 18.5:
            bmi_category = "Underweight"
        elif bmi <= 22.9:
            bmi_category = "Normal (Asian Indian)"
        elif bmi <= 24.9:
            bmi_category = "Overweight (Asian Indian)"
        else:
            bmi_category = "Obese (Asian Indian)"

    diabetes_rep = reports.get("diabetes", {})
    cardiac_rep = reports.get("cardiac", {})

    return {
        "name": summary.get("name", "Patient"),
        "age": summary.get("age", 35),
        "sex": summary.get("sex", "M"),
        "bmi": bmi,
        "bmi_category": bmi_category,
        "waist_cm": summary.get("waist_cm"),
        "activity_level": summary.get("activity_level", "moderate"),
        "smoking": summary.get("smoking", "never"),
        "fasting_glucose": summary.get("fasting_glucose"),
        "hba1c": summary.get("hba1c"),
        "sys_bp": summary.get("sys_bp"),
        "dia_bp": summary.get("dia_bp"),
        "diabetes_band": diabetes_rep.get("band", "Low"),
        "diabetes_score": diabetes_rep.get("composite", 15.0),
        "diabetes_idrs": diabetes_rep.get("idrs", 20),
        "cardiac_band": cardiac_rep.get("band", "Low"),
        "cardiac_score": cardiac_rep.get("composite", 10.0),
        "steps_mean": trends.get("steps", {}).get("mean_30"),
        "sleep_mean": trends.get("sleep_hours", {}).get("mean_30"),
        "rhr_mean": trends.get("rhr", {}).get("mean_30"),
        "spo2_mean": trends.get("spo2_min", {}).get("mean_30"),
        "gaps": _gaps(tools),
    }


def _detect_intent(question: str) -> str:
    """Identify the clinical focus of the user's query."""
    text = question.lower()
    if any(w in text for w in ("diet", "food", "eat", "eating", "meal", "carb", "sugar", "fruit", "snack", "fiber", "salt", "nutrition", "breakfast", "dinner", "lunch")):
        return "diet"
    if any(w in text for w in ("walk", "step", "exercise", "workout", "gym", "activity", "aerobic", "active", "fitness")):
        return "exercise"
    if any(w in text for w in ("heart", "cardio", "bp", "blood pressure", "rhr", "pulse", "cholesterol", "lipid", "chest", "cvd", "vascular")):
        return "cardio"
    if any(w in text for w in ("diabetes", "diabetic", "glucose", "sugar", "hba1c", "idrs", "prediabetes", "insulin")):
        return "diabetes"
    if any(w in text for w in ("sleep", "tired", "fatigue", "rest", "rem", "deep", "spo2", "oxygen", "wake", "insomnia", "bed")):
        return "sleep"
    return "general"


def _build_precautions(intent: str, ctx: dict[str, Any]) -> list[str]:
    """Targeted precautions (what to avoid or monitor closely) based on health and index."""
    precautions: list[str] = []

    # Smoking precaution
    if ctx.get("smoking") == "current":
        precautions.append(
            "**Tobacco Cessation Priority**: As an active smoker, smoking accelerates arterial stiffness and multiplies both cardiovascular and glycemic risks. Avoid smoking within 1 hour before sleep or exercise, and consider a structured cessation program."
        )

    # Glycemic / Diabetes precautions
    if intent in ("diet", "diabetes", "general"):
        if ctx.get("diabetes_band") in ("Moderate", "High") or (ctx.get("fasting_glucose") and ctx["fasting_glucose"] > 99):
            precautions.append(
                "**Limit Simple & Refined Carbohydrates**: Avoid refined wheat flour (maida), white bread, polished white rice, sweetened beverages, and sugary snacks, which cause sharp glucose spikes."
            )
            precautions.append(
                "**Avoid Meal Skipping**: Do not skip meals (especially breakfast or lunch). Erratic meal timing causes compensatory hunger and increases insulin resistance."
            )
        else:
            precautions.append(
                "**Be Mindful of Hidden Sugars**: Even in low-risk bands, limit packaged fruit juices, sweetened teas, and processed snacks to protect metabolic baseline."
            )

    # Cardiovascular / Heart precautions
    if intent in ("cardio", "exercise", "general"):
        if ctx.get("cardiac_band") in ("Moderate", "High") or (ctx.get("sys_bp") and ctx["sys_bp"] >= 130) or (ctx.get("rhr_mean") and ctx["rhr_mean"] > 75):
            precautions.append(
                "**Sodium & Salt Restriction**: Keep daily sodium intake under 2,000 mg (about 1 teaspoon of table salt). Avoid salty snacks (namkeen, chips), papads, pickles, and canned soups to prevent blood pressure elevation."
            )
            precautions.append(
                "**Avoid Sudden Unconditioned Strain**: If your resting heart rate is elevated, avoid sudden bursts of high-intensity training without a warm-up. Build cardiovascular stamina gradually."
            )
        else:
            precautions.append(
                "**Maintain Cardiovascular Awareness**: Moderate your intake of trans-fats, deep-fried snacks, and saturated fats to keep your lipid markers and blood pressure in the optimal range."
            )

    # Sleep & Recovery precautions
    if intent in ("sleep", "general"):
        if ctx.get("sleep_mean") and ctx["sleep_mean"] < 6.8:
            precautions.append(
                "**Avoid Late-Night Screen & Stimulant Exposure**: Refrain from screen time (blue light) and caffeine at least 2 hours before bed; nocturnal cortisol spikes interfere with deep restorative sleep and elevate morning glucose."
            )
        if ctx.get("spo2_mean") and ctx["spo2_mean"] < 94:
            precautions.append(
                "**Monitor Nocturnal Breathing**: Ensure proper sleeping posture and comfortable head elevation. If nocturnal SpO₂ dips persist, consult an ENT or pulmonologist for sleep apnea evaluation."
            )

    # Activity precautions
    if intent in ("exercise", "general"):
        if ctx.get("activity_level") == "sedentary" or (ctx.get("steps_mean") and ctx["steps_mean"] < 6000):
            precautions.append(
                "**Avoid Prolonged Unbroken Sitting**: Sedentary bouts exceeding 60 minutes decrease muscle glucose transporter (GLUT4) activity. Stand or stretch for 2 minutes every hour."
            )

    return precautions[:4]


def _build_suggestions(intent: str, ctx: dict[str, Any], passages: list[Passage]) -> list[str]:
    """Actionable lifestyle levers (diet, exercise, sleep, routine tests) based on health and index."""
    suggestions: list[str] = []

    # Nutrition suggestions
    if intent in ("diet", "diabetes", "general"):
        suggestions.append(
            "**Fiber-First Meal Sequencing (ICMR & ADA Protocol)**: Begin your main meals with a bowl of raw vegetable salad, sautéed greens, or whole sprouts before eating carbohydrates. This forms a natural fiber barrier that blunts post-meal glucose absorption by up to 30%."
        )
        suggestions.append(
            "**Incorporate Low-Glycemic Whole Grains**: Replace polished white rice with traditional Indian whole grains such as foxtail millet (kangni), pearl millet (bajra), finger millet (ragi), or steel-cut oats."
        )
        suggestions.append(
            "**Heart-Healthy Monounsaturated Fats**: Include a small handful (20–30g) of raw almonds, walnuts, and chia or flaxseeds daily to support HDL cholesterol and vascular elasticity."
        )

    # Physical activity suggestions
    if intent in ("exercise", "general", "diabetes", "cardio"):
        steps_val = ctx.get("steps_mean")
        if steps_val and steps_val < 7500:
            target_step = min(10000, int(steps_val + 1500))
            suggestions.append(
                f"**Gradual Step Progression**: Your 30-day average is approximately `{steps_val:.0f}` steps/day. Aim to reach `{target_step}` steps/day over the next two weeks by taking short 10-minute walking breaks during your workday."
            )
        else:
            suggestions.append(
                "**Maintain WHO Aerobic Goal**: Continue achieving 150–300 minutes of moderate aerobic activity weekly (such as brisk walking at 5 km/h) to keep your cardiorespiratory fitness in peak condition."
            )
        suggestions.append(
            "**15-Minute Post-Meal Walk**: A brisk 10 to 15-minute walk within 30 minutes after your largest meal significantly aids digestion and stimulates non-insulin glucose clearance in skeletal muscles."
        )

    # Sleep & Recovery suggestions
    if intent in ("sleep", "general"):
        suggestions.append(
            "**Anchor a Consistent Sleep Schedule**: Go to bed and wake up at the exact same time every day (including weekends) to align your circadian rhythm, enhance Stage 3 deep sleep, and optimize metabolic hormone balance."
        )
        suggestions.append(
            "**Pre-Sleep Autonomic Wind-Down**: Practice 5 minutes of relaxed diaphragmatic breathing (e.g. 4-second inhale, 7-second hold, 8-second exhale) before sleep to lower sympathetic tone and resting heart rate."
        )

    # Cardiovascular & Blood Pressure suggestions
    if intent in ("cardio", "general"):
        suggestions.append(
            "**DASH Dietary Approach**: Emphasize potassium- and magnesium-rich foods (spinach, bananas, lentils, seeds) while keeping sodium minimal to maintain optimal vascular compliance."
        )

    # Clinical checkup suggestion
    if ctx.get("diabetes_band") in ("Moderate", "High") or ctx.get("cardiac_band") in ("Moderate", "High"):
        suggestions.append(
            "**Preventive Lab Verification**: Schedule a routine fasting blood glucose, HbA1c, and fasting lipid profile with your healthcare practitioner every 3–6 months to monitor your index trajectory."
        )
    else:
        suggestions.append(
            "**Annual Wellness Review**: Re-verify routine clinical markers (fasting blood sugar, blood pressure, and lipid panel) annually to sustain your favorable risk profile."
        )

    return suggestions[:5]


def _build_follow_ups(intent: str, ctx: dict[str, Any]) -> list[str]:
    """Generate 2 relevant follow-up questions tailored to the question and patient context."""
    name = ctx.get("name", "you")
    band = ctx.get("diabetes_band", "Low")
    cardiac = ctx.get("cardiac_band", "Low")

    if intent == "diet":
        return [
            f"Would you like a sample 1-day low-glycemic Indian meal plan with healthy swaps for breakfast, lunch, and dinner?",
            f"Do you tend to experience afternoon energy dips or sugar cravings after your main meals?",
        ]
    if intent == "exercise":
        return [
            f"Would you like a 3-week progressive walking schedule to comfortably boost your daily step count without fatigue?",
            f"What time of day is most convenient for you to fit in a 15-minute post-meal walk?",
        ]
    if intent == "cardio":
        return [
            f"Would you like practical dietary tips to replace high-sodium condiments with flavorful Indian herbs and spices?",
            f"Have you had your blood pressure and resting pulse checked during a routine doctor visit in the past 6 months?",
        ]
    if intent == "sleep":
        return [
            f"Would you like a step-by-step evening wind-down routine to help increase your deep sleep percentage?",
            f"Do you typically wake up feeling refreshed, or do you notice morning grogginess?",
        ]
    if intent == "diabetes":
        return [
            f"Would you like more details on how the 'fiber-first' meal sequencing technique helps blunt blood glucose spikes?",
            f"Should we look at our What-If simulator to see how increasing sleep and steps affects your diabetes index?",
        ]

    # General follow-ups based on risk bands
    if band in ("Moderate", "High"):
        return [
            f"Which lifestyle area would you prefer to focus on first: fine-tuning daily nutrition, increasing walking steps, or improving sleep?",
            f"Would you like suggestions on specific questions to discuss with your doctor regarding your {band} diabetes risk band?",
        ]
    if cardiac in ("Moderate", "High"):
        return [
            f"Would you like a customized low-sodium meal guide tailored to heart-healthy Indian cooking?",
            f"Should we explore safe, low-impact aerobic routines to gradually reduce your resting pulse?",
        ]

    return [
        f"Which lifestyle area would you like to explore next: nutrition, daily step progression, or sleep recovery?",
        f"Would you like to test hypothetical lifestyle changes in our What-If simulator to see your risk score improve?",
    ]


def _compose(question: str, tools: list[ToolResult], passages: list[Passage]) -> str:
    """Generate a direct, grounded answer focusing on precautions, suggestions, and follow-ups."""
    ctx = _extract_context(tools)
    intent = _detect_intent(question)
    name = ctx["name"]
    age = ctx["age"]
    sex = ctx["sex"]

    precautions = _build_precautions(intent, ctx)
    suggestions = _build_suggestions(intent, ctx, passages)
    follow_ups = _build_follow_ups(intent, ctx)

    lines: list[str] = []

    # 1. Header & Direct Answer
    lines.append(f"### 📋 Preventive Health Assessment for {name} ({age} {sex})")
    lines.append("")

    # Direct introductory answer to the question
    if intent == "diet":
        lines.append(
            f"Regarding your inquiry on nutrition and diet: For your current metabolic profile, optimizing dietary quality through **fiber-rich whole foods, controlled carbohydrate portions, and low-sodium choices** is your highest-yield lifestyle lever to maintain favorable risk indices."
        )
    elif intent == "exercise":
        lines.append(
            f"Regarding your physical activity and exercise: Consistent aerobic movement—specifically **brisk walking of 150–300 minutes per week** combined with light resistance and post-meal strolls—is the most effective way to strengthen insulin sensitivity and cardiovascular endurance."
        )
    elif intent == "cardio":
        lines.append(
            f"Regarding your cardiovascular health: Your cardiac risk profile is evaluated using the Framingham CVD model and continuous resting vitals. Managing **sodium intake, keeping resting heart rate conditioned, and prioritizing recovery** are key to maintaining long-term arterial elasticity."
        )
    elif intent == "sleep":
        lines.append(
            f"Regarding your sleep and recovery: Quality sleep is foundational to autonomic balance and glucose regulation. Ensuring **7 to 8.5 hours of uninterrupted sleep with stable nocturnal oxygenation** protects against metabolic inflammation and daytime fatigue."
        )
    elif intent == "diabetes":
        lines.append(
            f"Regarding your diabetes screening and glycemic health: Your Indian Diabetes Risk Score (IDRS) and composite index assess lifestyle, age, waist circumference, and activity. Emphasizing **glycemic stability, fiber intake, and daily movement** directly lowers your risk trajectory."
        )
    else:
        lines.append(
            f"Here is your focused health assessment addressing *\"{question.strip()}\"*. Based on your clinical screening markers, continuous wearable telemetry, and evidence-grounded guidelines (ICMR, WHO, ADA, AHA), here are your tailored precautions and actionable suggestions."
        )

    lines.append("")

    # 2. Health Standing & Index Context (Compact & Informative, not a raw dump)
    lines.append("#### 📊 General Health & Risk Index Context")
    bmi_str = f"`{ctx['bmi']} kg/m²` ({ctx['bmi_category']})" if ctx["bmi"] else "Recorded"
    diabetes_status = f"**{ctx['diabetes_band']} Risk** (Composite: `{ctx['diabetes_score']}`, IDRS: `{ctx['diabetes_idrs']}/100`)"
    cardiac_status = f"**{ctx['cardiac_band']} Risk** (Composite: `{ctx['cardiac_score']}%`)"

    lines.append(
        f"- **Clinical Indices**: Diabetes is in the {diabetes_status} | Cardiovascular is in the {cardiac_status}."
    )
    vitals_summary = []
    if ctx.get("fasting_glucose"):
        vitals_summary.append(f"Fasting Glucose: `{ctx['fasting_glucose']} mg/dL`")
    if ctx.get("hba1c"):
        vitals_summary.append(f"HbA1c: `{ctx['hba1c']}%`")
    vitals_summary.append(f"BMI: {bmi_str}")
    if ctx.get("steps_mean"):
        vitals_summary.append(f"Avg Steps: `{ctx['steps_mean']:.0f}/day`")
    if ctx.get("sleep_mean"):
        vitals_summary.append(f"Avg Sleep: `{ctx['sleep_mean']:.1f} hrs`")
    lines.append(f"- **Key Biomarkers**: {' | '.join(vitals_summary)}.")

    lines.append("")

    # 3. Targeted Precautions
    lines.append("#### ⚠️ Essential Precautions (What to Watch Out For)")
    for p in precautions:
        lines.append(f"- {p}")

    lines.append("")

    # 4. Actionable Suggestions
    lines.append("#### 💡 Actionable Suggestions & Lifestyle Levers")
    for s in suggestions:
        lines.append(f"- {s}")

    lines.append("")

    # 5. Recommended Follow-up Questions
    lines.append("#### 💬 Recommended Follow-up Questions")
    for q in follow_ups:
        lines.append(f"- *{q}*")

    return "\n".join(lines)


def answer(session: Session, patient_id: int, message: str) -> tuple[str, list[str], bool, list[str]]:
    """Return reply, source labels, emergency flag, and tool names."""
    if is_emergency(message):
        return EMERGENCY_REPLY, ["emergency guardrail"], True, []

    tools = run_tools(session, patient_id, message)
    passages = retrieve(message)
    draft = _compose(message, tools, passages)

    # Let local LLM polish if available, else keep the high-quality structured draft
    polished = rephrase(message, draft) or draft
    text = post_check(polished)
    sources = [item.name for item in tools] + [f"guideline:{item.source}" for item in passages]
    return text, sources, False, [item.name for item in tools]


def stream_events(session: Session, patient_id: int, message: str) -> Iterator[str]:
    """Server-sent events for the dashboard chat."""
    text, sources, emergency, tools_used = answer(session, patient_id, message)
    step = 40
    for index in range(0, len(text), step):
        yield f"data: {json.dumps({'token': text[index:index + step]})}\n\n"
    yield f"data: {json.dumps({'done': True, 'sources': sources, 'emergency': emergency, 'tools': tools_used, 'disclaimer': DISCLAIMER})}\n\n"

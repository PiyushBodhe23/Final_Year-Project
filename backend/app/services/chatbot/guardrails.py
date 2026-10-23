"""Pre- and post-checks so the chatbot cannot act like a clinician."""

from __future__ import annotations

from backend.app.core.config import DISCLAIMER

EMERGENCY_TERMS: tuple[str, ...] = (
    "chest pain",
    "chest pains",
    "heart attack",
    "crushing chest",
    "angina",
    "breathless",
    "breathlessness",
    "can't breathe",
    "cannot breathe",
    "short of breath",
    "shortness of breath",
    "fainting",
    "fainted",
    "passed out",
    "loss of consciousness",
    "stroke",
    "paralysis",
    "slurred speech",
    "seizure",
    "suicidal",
    "suicide",
    "kill myself",
    "want to die",
)

EMERGENCY_REPLY: str = (
    "⚠️ **CRITICAL MEDICAL ALERT: IMMEDIATE ATTENTION REQUIRED**\n\n"
    "This sounds like it could be an emergency. Stop using this chat and seek urgent care now. "
    "In India call 112, or go to the nearest emergency department. "
    "PreventVital cannot assess emergencies and cannot give treatment advice."
)

_FORBIDDEN: tuple[str, ...] = (
    "you have diabetes",
    "you have heart disease",
    "you are diabetic",
    "take metformin",
    "take insulin",
    "start statin",
    "mg twice",
    "mg daily",
)


def is_emergency(message: str) -> bool:
    """True when the message should skip RAG and tools."""
    text = message.lower()
    return any(term in text for term in EMERGENCY_TERMS)


def post_check(text: str) -> str:
    """Strip diagnosis-style claims and always attach the academic disclaimer."""
    cleaned = text.strip()
    lowered = cleaned.lower()
    for phrase in _FORBIDDEN:
        if phrase in lowered:
            cleaned += (
                "\n\nI cannot confirm a diagnosis or suggest medicines. "
                "Use the screening numbers above only as a prompt to talk with a clinician."
            )
            break
    if DISCLAIMER.lower() not in cleaned.lower():
        cleaned = f"{cleaned}\n\n{DISCLAIMER}"
    return cleaned

"""Local LLM rephraser grounded strictly in clinical index & guidance.

Preserves exact numbers, risk bands, and clinical facts while delivering
compassionate, actionable precautions, lifestyle suggestions, and follow-up questions.
"""

from __future__ import annotations

import os
import requests


def rephrase(question: str, grounded_draft: str) -> str | None:
    """Ask Ollama or local LLM to polish wording into an engaging, empathetic counseling reply.

    Returns None if offline, busy, or timed out (fast failover to deterministic draft).
    """
    if os.environ.get("PREVENTVITAL_OLLAMA") == "0":
        return None

    host = os.environ.get("OLLAMA_HOST", os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    model = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

    system_instruction = (
        "You are PreventVital's clinical AI health assistant for preventive care in India. "
        "Your role is to guide the user with evidence-based precautions and actionable lifestyle suggestions "
        "grounded strictly in their general health profile, risk indices (Indian Diabetes Risk Score / CVD band), and wearable trends.\n\n"
        "RESPONSE RULES:\n"
        "1. DIRECT & CONCISE: Answer the user's specific question directly in the opening paragraph. Do NOT dump long tables of raw numbers.\n"
        "2. HEALTH & RISK INDEX CONTEXT: Keep the general health & risk index context concise (1-2 sentences summarizing their risk band, BMI, and vital baseline).\n"
        "3. PRECAUTIONS: Highlight 2-3 targeted precautions (what to avoid or watch out for) based on their risk level.\n"
        "4. SUGGESTIONS: Provide 3-4 concrete, high-yield lifestyle suggestions (nutrition, exercise, sleep, routine tests) following ICMR/WHO/ADA/AHA guidelines.\n"
        "5. FOLLOW-UP QUESTIONS: Always end your response with exactly 2 thoughtful, relevant follow-up questions under the markdown heading '#### 💬 Recommended Follow-up Questions'.\n"
        "6. SAFETY: Do not prescribe drugs or offer definitive diagnoses. Keep guidance educational, preventive, and supportive."
    )

    try:
        response = requests.post(
            f"{host.rstrip('/')}/api/chat",
            json={
                "model": model,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 600,
                },
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {
                        "role": "user",
                        "content": (
                            f"User Inquiry: {question}\n\n"
                            f"Grounded Health Context & Draft:\n{grounded_draft}\n\n"
                            "Please provide a refined, to-the-point response with essential precautions, lifestyle suggestions, and 2 follow-up questions."
                        ),
                    },
                ],
            },
            timeout=12.0,
        )
        if response.status_code == 200:
            content = response.json().get("message", {}).get("content", "").strip()
            # Verify the response has reasonable length and quality
            if len(content) > 100:
                return content
        return None
    except Exception:
        # Seamless failover to deterministic grounded draft
        return None

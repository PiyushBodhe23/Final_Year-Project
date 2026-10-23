"""Emergency path, RAG retrieval, and patient-grounded recommendations."""

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.chatbot.guardrails import is_emergency
from backend.app.services.chatbot.orchestrator import answer
from backend.app.services.chatbot.rag import retrieve
from backend.app.core.db import SessionLocal


def test_chest_pain_is_emergency() -> None:
    assert is_emergency("I have chest pain since morning")
    assert not is_emergency("Why is my diabetes risk moderate?")


def test_rag_retrieves_activity_guideline() -> None:
    passages = retrieve("How many minutes of activity should an adult do each week?")
    sources = {item.source for item in passages}
    assert "who-activity.md" in sources


def test_recommendation_uses_rahul_saved_numbers() -> None:
    with SessionLocal() as session:
        text, sources, emergency, tools = answer(
            session, 2, "What should I do to lower my diabetes risk?"
        )
    assert emergency is False
    assert "get_risk_report" in tools
    assert any(item.startswith("guideline:") for item in sources)
    assert "call 112" not in text.lower()
    assert "53" in text or "Moderate" in text
    assert "glucose" in text.lower() or "steps" in text.lower()
    assert "metformin" not in text.lower()


def test_chat_stream_emergency() -> None:
    client = TestClient(app)
    with client.stream("POST", "/api/chat", json={"patient_id": 2, "message": "I have chest pain"}) as response:
        body = b"".join(response.iter_bytes()).decode("utf-8")
    assert "112" in body
    assert "emergency" in body

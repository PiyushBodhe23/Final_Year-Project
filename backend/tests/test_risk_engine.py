"""IDRS points and the three viva personas land in the planned bands."""

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.risk_engine import idrs_parts


def test_idrs_matches_the_published_point_table() -> None:
    priya = idrs_parts(28, "F", 72, "regular", "none")
    rahul = idrs_parts(45, "M", 98, "sedentary", "one parent")
    suresh = idrs_parts(58, "M", 108, "sedentary", "one parent")
    assert sum(priya.values()) == 0
    assert sum(rahul.values()) == 70
    assert rahul["IDRS age"] == 20
    assert rahul["IDRS waist"] == 10
    assert rahul["IDRS activity"] == 30
    assert rahul["IDRS family history"] == 10
    assert sum(suresh.values()) == 90


def test_persona_bands_and_methodology() -> None:
    client = TestClient(app)
    scores = {}
    for patient_id, name in [(1, "Priya"), (2, "Rahul"), (3, "Suresh")]:
        response = client.post(f"/api/patients/{patient_id}/risk/calculate")
        assert response.status_code == 200, response.text
        by_disease = {row["disease"]: row for row in response.json()}
        scores[name] = by_disease
        assert "not a diagnostic" in by_disease["diabetes"]["disclaimer"].lower()

    assert scores["Priya"]["diabetes"]["band"] == "Low"
    assert scores["Priya"]["cardiac"]["band"] == "Low"
    assert scores["Rahul"]["diabetes"]["band"] in {"Moderate", "High"}
    assert scores["Rahul"]["cardiac"]["band"] == "Moderate"
    assert scores["Suresh"]["diabetes"]["band"] == "High"
    assert scores["Suresh"]["cardiac"]["band"] == "High"

    method = client.get("/api/methodology")
    assert method.status_code == 200
    body = method.json()
    assert "0.7 * baseline" in body["composite"]
    assert body["idrs"]["activity"]["sedentary"] == 30

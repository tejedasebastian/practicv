from __future__ import annotations

import httpx
import pytest

from tests.e2e.support import ApiContext


def _create_offer(
    client: httpx.Client,
    title: str,
    requirements: str,
    description: str,
    url: str,
) -> dict:
    response = client.post(
        "/api/v1/offers/manual",
        json={
            "title": title,
            "company": "Match Corp",
            "source_url": url,
            "location": "Lima",
            "modality": "Híbrido",
            "description": description,
            "requirements_text": requirements,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["offer"]


def test_match_apply_with_full_coverage(
    client: httpx.Client,
    api: ApiContext,
) -> None:
    offer = _create_offer(
        client,
        "Practicante de Datos Match",
        "SQL intermedio, PowerBI intermedio, Excel intermedio",
        "Python deseable.",
        "https://example.com/offers/match-full",
    )
    response = client.post(
        "/api/v1/matches",
        json={"profile_id": api.profile_id, "offer_id": offer["id"]},
    )

    assert response.status_code == 200, response.text
    match = response.json()
    assert match["overall_score"] == pytest.approx(100.0)
    assert match["must_have_score"] == pytest.approx(100.0)
    assert match["confidence"] > 0
    assert match["decision"] == "apply"
    assert match["gaps_json"] == []
    skills = {item["skill"]: item for item in match["explanation_json"]}
    assert skills["Power BI"]["requirement_type"] == "must"
    assert skills["Power BI"]["required_level"] == 2
    assert skills["Power BI"]["user_level"] == 2
    assert skills["Python"]["requirement_type"] == "nice"
    assert skills["Python"]["status"] == "met"


def test_match_reports_must_have_gap(
    client: httpx.Client,
    api: ApiContext,
) -> None:
    offer = _create_offer(
        client,
        "Practicante de Data Engineering",
        "SQL intermedio, Databricks intermedio",
        "Buscamos perfil de datos.",
        "https://example.com/offers/match-gap",
    )
    response = client.post(
        "/api/v1/matches",
        json={"profile_id": api.profile_id, "offer_id": offer["id"]},
    )

    assert response.status_code == 200, response.text
    match = response.json()
    assert match["must_have_score"] == pytest.approx(50.0)
    assert match["overall_score"] == pytest.approx(50.0)
    assert match["decision"] == "improve_cv"
    gap_skills = {gap["skill"] for gap in match["gaps_json"]}
    assert "Databricks" in gap_skills
    databricks = next(gap for gap in match["gaps_json"] if gap["skill"] == "Databricks")
    assert databricks["required_level"] == 2
    assert databricks["user_level"] == 0
    assert "Agrega evidencia" in databricks["suggestion"]


def test_match_nice_to_have_gap_and_override(
    client: httpx.Client,
    api: ApiContext,
) -> None:
    offer = _create_offer(
        client,
        "Practicante de BI Match",
        "SQL intermedio",
        "Tableau deseable.",
        "https://example.com/offers/match-nice",
    )
    created = client.post(
        "/api/v1/matches",
        json={"profile_id": api.profile_id, "offer_id": offer["id"]},
    )
    assert created.status_code == 200, created.text
    match = created.json()
    assert match["must_have_score"] == pytest.approx(100.0)
    assert match["overall_score"] == pytest.approx(75.0)
    assert match["decision"] == "apply_with_gaps"
    gaps = {gap["skill"]: gap for gap in match["gaps_json"]}
    assert gaps["Tableau"]["requirement_type"] == "nice"

    override = client.patch(
        f"/api/v1/matches/{match['id']}",
        json={"decision": "apply", "reason": "Revisado manualmente"},
    )
    assert override.status_code == 200, override.text
    overridden = override.json()
    assert overridden["decision"] == "apply"
    assert overridden["overridden"] is True
    assert overridden["override_reason"] == "Revisado manualmente"

    detail = client.get(f"/api/v1/matches/{match['id']}")
    assert detail.status_code == 200
    assert detail.json()["overridden"] is True

    listed = client.get(f"/api/v1/profiles/{api.profile_id}/matches")
    assert listed.status_code == 200
    assert listed.json()
    assert "offer" in listed.json()[0]

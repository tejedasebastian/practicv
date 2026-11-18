from __future__ import annotations

import httpx

from practicv.adapters.cv.parser import DOCX_MIME, PDF_MIME
from tests.e2e.fixtures import build_docx_cv, build_pdf_cv
from tests.e2e.support import ApiContext


def _create_profile(client: httpx.Client) -> dict:
    response = client.post(
        "/api/v1/profiles",
        json={
            "full_name": "Fase Dos Demo",
            "email": "fase2.demo@example.com",
            "career": "Ingeniería de Software",
            "cycle": 8,
            "location": "Lima",
            "target_roles": ["Data Analyst"],
            "locale": "es",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_profile_crud_cv_upload_and_ai_consent(
    client: httpx.Client,
    api: ApiContext,
) -> None:
    profile = _create_profile(client)
    profile_id = profile["id"]

    update = client.patch(
        f"/api/v1/profiles/{profile_id}",
        json={"career": "Data Science", "target_roles": ["BI Analyst"]},
    )
    assert update.status_code == 200
    assert update.json()["career"] == "Data Science"
    assert update.json()["target_roles"] == ["BI Analyst"]

    pdf_upload = client.post(
        f"/api/v1/profiles/{profile_id}/cv",
        files={"file": ("cv_demo.pdf", build_pdf_cv(), PDF_MIME)},
    )
    assert pdf_upload.status_code == 201, pdf_upload.text
    pdf_data = pdf_upload.json()
    assert pdf_data["filename"] == "cv_demo.pdf"
    assert "experiencia" in pdf_data["sections"]
    assert "habilidades" in pdf_data["sections"]
    assert pdf_data["contact"]["email"] == "sebas.demo@example.com"
    assert pdf_data["contact"]["phone"] is not None
    skill_names = {skill["canonical_name"] for skill in pdf_data["skills"]}
    assert {"Python", "SQL", "Power BI", "FastAPI", "Docker"} <= skill_names
    power_bi = next(skill for skill in pdf_data["skills"] if skill["canonical_name"] == "Power BI")
    assert "PowerBI" in (power_bi["evidence"] or "")
    assert pdf_data["skills"][0]["confirmed"] is False

    docx_upload = client.post(
        f"/api/v1/profiles/{profile_id}/cv",
        files={"file": ("cv_demo.docx", build_docx_cv(), DOCX_MIME)},
    )
    assert docx_upload.status_code == 201, docx_upload.text
    docx_data = docx_upload.json()
    assert docx_data["filename"] == "cv_demo.docx"
    assert "experiencia" in docx_data["sections"]

    active_cv = client.get(f"/api/v1/profiles/{profile_id}/cv")
    assert active_cv.status_code == 200
    assert active_cv.json()["filename"] == "cv_demo.docx"

    selected = docx_data["skills"][:2]
    skills_payload = {
        "skills": [
            {
                "skill_id": selected[0]["skill_id"],
                "level": 3,
                "evidence": "Proyecto de datos",
                "confirmed": True,
            },
            {
                "skill_id": selected[1]["skill_id"],
                "level": 2,
                "evidence": "Curso",
                "confirmed": True,
            },
        ]
    }
    skills_update = client.patch(
        f"/api/v1/profiles/{profile_id}/cv/skills",
        json=skills_payload,
    )
    assert skills_update.status_code == 200, skills_update.text
    updated_skills = skills_update.json()["skills"]
    assert len(updated_skills) == 2
    assert {skill["level"] for skill in updated_skills} == {2, 3}
    assert all(skill["confirmed"] for skill in updated_skills)

    raw_text = (
        "Mi correo es sebas.demo@example.com y mi teléfono +51 987 654 321. "
        "Experiencia en Python y SQL. Proyectos de BI."
    )
    no_consent = client.post(
        f"/api/v1/profiles/{profile_id}/cv/analyze-ai",
        json={"text": raw_text, "consent": False},
    )
    assert no_consent.status_code == 422
    assert no_consent.json()["error"]["code"] == "validation_error"

    with_consent = client.post(
        f"/api/v1/profiles/{profile_id}/cv/analyze-ai",
        json={"text": raw_text, "consent": True},
    )
    assert with_consent.status_code == 200, with_consent.text
    ai_data = with_consent.json()
    assert ai_data["provider"] == "stub"
    assert ai_data["pii_removed"] is True
    assert "sebas.demo@example.com" not in ai_data["redacted_text"]
    assert "987 654 321" not in ai_data["redacted_text"]
    assert "[EMAIL]" in ai_data["redacted_text"]
    assert "[PHONE]" in ai_data["redacted_text"]
    assert ai_data["suggestions"]

    invalid_file = client.post(
        f"/api/v1/profiles/{profile_id}/cv",
        files={"file": ("cv.txt", b"not a cv", "text/plain")},
    )
    assert invalid_file.status_code == 422
    assert invalid_file.json()["error"]["code"] == "validation_error"

    deleted = client.delete(f"/api/v1/profiles/{profile_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/profiles/{profile_id}").status_code == 404

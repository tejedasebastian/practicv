from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from tests.e2e.support import ApiContext

ARTIFACTS_DIR = Path(__file__).resolve().parents[3] / "artifacts" / "e2e"


def _write_artifact(name: str, content: bytes) -> str:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTIFACTS_DIR / name
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def test_full_flow_and_artifacts(
    client: httpx.Client,
    api: ApiContext,
) -> None:
    offer_response = client.post(
        "/api/v1/offers/manual",
        json={
            "title": "Practicante de Datos Full Flow",
            "company": "Full Flow Corp",
            "source_url": "https://example.com/offers/full-flow",
            "location": "Lima",
            "modality": "Híbrido",
            "salary_text": "S/ 1,600",
            "salary_amount": 1600,
            "description": "Oferta completa para el flujo E2E.",
            "requirements_text": "SQL intermedio, Power BI intermedio",
            "deadline_at": "2026-12-31T00:00:00Z",
        },
    )
    assert offer_response.status_code == 201, offer_response.text
    offer = offer_response.json()["offer"]

    match_response = client.post(
        "/api/v1/matches",
        json={"profile_id": api.profile_id, "offer_id": offer["id"]},
    )
    assert match_response.status_code == 200, match_response.text
    match = match_response.json()
    assert match["overall_score"] >= 80

    application_response = client.post(
        "/api/v1/applications",
        json={
            "profile_id": api.profile_id,
            "offer_id": offer["id"],
            "status": "applied",
            "next_action_at": "2026-12-15T00:00:00Z",
            "next_action_note": "Hacer seguimiento.",
            "notes": "Flujo completo E2E.",
        },
    )
    assert application_response.status_code == 201, application_response.text
    application = application_response.json()["application"]

    reminder_response = client.post(
        f"/api/v1/applications/{application['id']}/reminders",
        json={
            "due_at": "2026-12-10T09:00:00Z",
            "channel": "in_app",
            "message": "Seguimiento full flow.",
        },
    )
    assert reminder_response.status_code == 201, reminder_response.text

    workbook = client.get(
        "/api/v1/exports/applications.xlsx",
        params={"profile_id": api.profile_id},
    )
    assert workbook.status_code == 200
    csv_export = client.get(
        "/api/v1/exports/applications.csv",
        params={"profile_id": api.profile_id},
    )
    assert csv_export.status_code == 200
    ics_export = client.get(
        "/api/v1/exports/calendar.ics",
        params={"profile_id": api.profile_id},
    )
    assert ics_export.status_code == 200
    assert "BEGIN:VCALENDAR" in ics_export.text

    checksums = {
        "applications.xlsx": _write_artifact("applications.xlsx", workbook.content),
        "applications.csv": _write_artifact("applications.csv", csv_export.content),
        "calendar.ics": _write_artifact("calendar.ics", ics_export.content),
        "matches.json": _write_artifact(
            "matches.json",
            json.dumps(match, ensure_ascii=False, indent=2).encode("utf-8"),
        ),
    }

    manifest = {
        "checkpoint": "phase-7",
        "generated_at": datetime.now(UTC).isoformat(),
        "profile_id": api.profile_id,
        "offer_id": offer["id"],
        "match_id": match["id"],
        "application_id": application["id"],
        "steps": {
            "profile_seeded": True,
            "offer_created": True,
            "match_computed": True,
            "application_created": True,
            "reminder_created": True,
            "xlsx_exported": True,
            "csv_exported": True,
            "ics_exported": True,
        },
        "counts": {
            "offers": len(api.offer_ids) + 1,
            "applications": 4,
        },
        "checksums": checksums,
    }
    _write_artifact(
        "run_manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
    )
    checksum_lines = "\n".join(f"{digest}  {name}" for name, digest in checksums.items())
    _write_artifact("checksums.sha256", (checksum_lines + "\n").encode("utf-8"))

    for name in (
        "run_manifest.json",
        "matches.json",
        "applications.xlsx",
        "applications.csv",
        "calendar.ics",
        "checksums.sha256",
    ):
        assert (ARTIFACTS_DIR / name).exists(), name

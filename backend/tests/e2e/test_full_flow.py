from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import httpx
from openpyxl import load_workbook

from tests.e2e.support import ApiContext

ARTIFACTS_DIR = Path(__file__).resolve().parents[3] / "artifacts" / "e2e"
REQUIRED_SHEETS = {
    "Postulaciones",
    "Ofertas",
    "Matches",
    "Brechas",
    "Timeline",
    "Habilidades",
}
CSV_HEADER = "empresa,puesto,estado,match,must_have,decision,postulada,proxima_accion,nota"


def _write_artifact(name: str, content: bytes) -> str:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTIFACTS_DIR / name
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


def test_full_flow_and_artifacts(
    client: httpx.Client,
    api: ApiContext,
) -> None:
    timings: dict[str, float] = {}

    start = time.perf_counter()
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
    timings["offer_create"] = _elapsed_ms(start)
    assert offer_response.status_code == 201, offer_response.text
    offer = offer_response.json()["offer"]

    start = time.perf_counter()
    match_response = client.post(
        "/api/v1/matches",
        json={"profile_id": api.profile_id, "offer_id": offer["id"]},
    )
    timings["match_compute"] = _elapsed_ms(start)
    assert match_response.status_code == 200, match_response.text
    match = match_response.json()
    assert match["overall_score"] >= 80
    assert match["must_have_score"] >= 80
    assert match["decision"] == "apply"
    assert match["gaps_json"] == []
    assert match["confidence"] > 0

    start = time.perf_counter()
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
    timings["application_create"] = _elapsed_ms(start)
    assert application_response.status_code == 201, application_response.text
    application = application_response.json()["application"]

    start = time.perf_counter()
    reminder_response = client.post(
        f"/api/v1/applications/{application['id']}/reminders",
        json={
            "due_at": "2026-12-10T09:00:00Z",
            "channel": "in_app",
            "message": "Seguimiento full flow.",
        },
    )
    timings["reminder_create"] = _elapsed_ms(start)
    assert reminder_response.status_code == 201, reminder_response.text

    start = time.perf_counter()
    workbook = client.get(
        "/api/v1/exports/applications.xlsx",
        params={"profile_id": api.profile_id},
    )
    timings["xlsx_export"] = _elapsed_ms(start)
    assert workbook.status_code == 200
    workbook_loaded = load_workbook(BytesIO(workbook.content), read_only=True)
    sheets = workbook_loaded.sheetnames
    assert set(sheets) >= REQUIRED_SHEETS, sheets
    workbook_loaded.close()

    start = time.perf_counter()
    csv_export = client.get(
        "/api/v1/exports/applications.csv",
        params={"profile_id": api.profile_id},
    )
    timings["csv_export"] = _elapsed_ms(start)
    assert csv_export.status_code == 200
    csv_header = csv_export.text.splitlines()[0]
    assert csv_header == CSV_HEADER, csv_header
    assert "Full Flow Corp" in csv_export.text

    start = time.perf_counter()
    ics_export = client.get(
        "/api/v1/exports/calendar.ics",
        params={"profile_id": api.profile_id},
    )
    timings["ics_export"] = _elapsed_ms(start)
    assert ics_export.status_code == 200
    assert "BEGIN:VCALENDAR" in ics_export.text
    assert "BEGIN:VEVENT" in ics_export.text
    assert "Seguimiento full flow." in ics_export.text

    artifacts = {
        "applications.xlsx": workbook.content,
        "applications.csv": csv_export.content,
        "calendar.ics": ics_export.content,
        "matches.json": json.dumps(match, ensure_ascii=False, indent=2).encode("utf-8"),
    }
    checksums = {name: _write_artifact(name, content) for name, content in artifacts.items()}

    quality_report = {
        "checkpoint": "phase-7",
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "medium-hard full flow: manual offer -> explainable match -> "
            "application -> reminder -> xlsx/csv/ics exports"
        ),
        "result": "passed",
        "checks": [
            {
                "name": "offer_created",
                "passed": offer_response.status_code == 201,
                "detail": f"HTTP {offer_response.status_code}, source_type={offer['source_type']}",
            },
            {
                "name": "match_computed",
                "passed": True,
                "detail": (
                    f"overall={match['overall_score']}, "
                    f"must_have={match['must_have_score']}, decision={match['decision']}"
                ),
            },
            {
                "name": "match_without_gaps",
                "passed": match["gaps_json"] == [],
                "detail": f"gaps={len(match['gaps_json'])}",
            },
            {
                "name": "application_created",
                "passed": application_response.status_code == 201,
                "detail": (
                    f"status={application['status']}, "
                    f"duplicate={application_response.json()['duplicate']}"
                ),
            },
            {
                "name": "reminder_created",
                "passed": reminder_response.status_code == 201,
                "detail": f"channel={reminder_response.json()['channel']}",
            },
            {
                "name": "xlsx_sheets",
                "passed": set(sheets) >= REQUIRED_SHEETS,
                "detail": ", ".join(sheets),
            },
            {
                "name": "csv_header",
                "passed": csv_header == CSV_HEADER,
                "detail": csv_header,
            },
            {
                "name": "ics_events",
                "passed": "BEGIN:VEVENT" in ics_export.text,
                "detail": "BEGIN:VCALENDAR + BEGIN:VEVENT + reminder",
            },
        ],
        "metrics_ms": timings,
        "counts": {
            "offers": len(api.offer_ids) + 1,
            "applications": 4,
            "matches": 1,
            "reminders": 1,
        },
        "artifacts": {
            name: {
                "bytes": len(content),
                "sha256": checksums[name],
            }
            for name, content in artifacts.items()
        },
    }
    quality_bytes = json.dumps(
        quality_report,
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")
    checksums["quality_report.json"] = _write_artifact(
        "quality_report.json",
        quality_bytes,
    )

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
            "quality_report_written": True,
        },
        "counts": {
            "offers": len(api.offer_ids) + 1,
            "applications": 4,
        },
        "checksums": checksums,
        "checksums_note": (
            "checksums.sha256 covers the five payload artifacts "
            "(xlsx, csv, ics, matches, quality report); it cannot cover "
            "run_manifest.json or itself without a circular dependency."
        ),
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
        "quality_report.json",
        "checksums.sha256",
    ):
        assert (ARTIFACTS_DIR / name).exists(), name

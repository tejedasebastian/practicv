from __future__ import annotations

from io import BytesIO

import httpx
from openpyxl import load_workbook

from tests.e2e.support import ApiContext


def test_application_kanban_events_reminders_and_exports(
    client: httpx.Client,
    api: ApiContext,
) -> None:
    offer_id = api.offer_ids[3]
    created = client.post(
        "/api/v1/applications",
        json={
            "profile_id": api.profile_id,
            "offer_id": offer_id,
            "status": "saved",
            "next_action_at": "2026-12-15T00:00:00Z",
            "next_action_note": "Preparar CV adaptado.",
            "notes": "Postulación de prueba.",
        },
    )
    assert created.status_code == 201, created.text
    application = created.json()["application"]
    assert created.json()["duplicate"] is False
    assert application["status"] == "saved"
    application_id = application["id"]

    duplicate = client.post(
        "/api/v1/applications",
        json={"profile_id": api.profile_id, "offer_id": offer_id},
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["application"]["id"] == application_id

    listed = client.get("/api/v1/applications", params={"profile_id": api.profile_id})
    assert listed.status_code == 200
    assert any(item["application"]["id"] == application_id for item in listed.json())
    assert listed.json()[0]["offer"]["title"]

    detail = client.get(f"/api/v1/applications/{application_id}")
    assert detail.status_code == 200
    assert detail.json()["application"]["id"] == application_id

    moved = client.patch(
        f"/api/v1/applications/{application_id}",
        json={
            "status": "interview",
            "next_action_note": "Preparar entrevista técnica.",
        },
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["status"] == "interview"
    assert moved.json()["applied_at"] is not None

    event = client.post(
        f"/api/v1/applications/{application_id}/events",
        json={
            "event_type": "interview",
            "event_at": "2026-12-01T15:00:00Z",
            "notes": "Entrevista con el equipo de datos.",
        },
    )
    assert event.status_code == 201, event.text
    events = client.get(f"/api/v1/applications/{application_id}/events")
    assert events.status_code == 200
    assert any(item["event_type"] == "interview" for item in events.json())

    reminder = client.post(
        f"/api/v1/applications/{application_id}/reminders",
        json={
            "due_at": "2026-12-10T09:00:00Z",
            "channel": "in_app",
            "message": "Hacer seguimiento a la entrevista.",
        },
    )
    assert reminder.status_code == 201, reminder.text
    reminders = client.get(f"/api/v1/applications/{application_id}/reminders")
    assert reminders.status_code == 200
    assert len(reminders.json()) == 1

    profile_reminders = client.get(f"/api/v1/profiles/{api.profile_id}/reminders")
    assert profile_reminders.status_code == 200
    assert any(item["id"] == reminder.json()["id"] for item in profile_reminders.json())

    workbook_response = client.get(
        "/api/v1/exports/applications.xlsx",
        params={"profile_id": api.profile_id},
    )
    assert workbook_response.status_code == 200
    workbook = load_workbook(BytesIO(workbook_response.content))
    assert {"Postulaciones", "Ofertas", "Matches", "Brechas", "Timeline", "Habilidades"} <= set(
        workbook.sheetnames
    )
    assert workbook["Postulaciones"].max_row >= 2

    csv_response = client.get(
        "/api/v1/exports/applications.csv",
        params={"profile_id": api.profile_id},
    )
    assert csv_response.status_code == 200
    assert "empresa,puesto,estado" in csv_response.text
    assert "Match Corp" in csv_response.text or "Practicante" in csv_response.text

    ics_response = client.get(
        "/api/v1/exports/calendar.ics",
        params={"profile_id": api.profile_id},
    )
    assert ics_response.status_code == 200
    assert "BEGIN:VCALENDAR" in ics_response.text
    assert "BEGIN:VEVENT" in ics_response.text
    assert "Hacer seguimiento" in ics_response.text

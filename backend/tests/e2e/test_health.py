from __future__ import annotations

import httpx


def test_health_reports_database_ok(client: httpx.Client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "PractiCV"
    assert payload["version"] == "0.2.0"
    assert payload["environment"] == "test"
    assert payload["database"] == "ok"


def test_root_metadata(client: httpx.Client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "PractiCV"
    assert payload["health"] == "/health"

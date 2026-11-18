from __future__ import annotations

import httpx

from tests.e2e.support import ApiContext


def test_profile_round_trip(client: httpx.Client, api: ApiContext) -> None:
    response = client.get(f"/api/v1/profiles/{api.profile_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["full_name"] == "Estudiante Demo"
    assert payload["career"] == "Ingeniería de Software"
    assert payload["locale"] == "es"
    assert payload["target_roles"] == ["Data Analyst", "BI Analyst", "Backend Developer"]
    assert response.headers["x-request-id"]


def test_domain_error_format(client: httpx.Client) -> None:
    response = client.get("/api/v1/profiles/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "not_found"
    assert payload["error"]["message"] == "Profile not found"
    assert payload["error"]["details"]["profile_id"] == "00000000-0000-0000-0000-000000000000"

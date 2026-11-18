from __future__ import annotations

import httpx

from tests.e2e.support import ApiContext


def test_offer_ranking_uses_window_function(
    client: httpx.Client,
    api: ApiContext,
) -> None:
    response = client.get(
        f"/api/v1/analytics/offer-ranking/{api.profile_id}",
        params={"limit": 5},
    )

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 5
    assert [row["rank"] for row in rows] == [1, 2, 3, 4, 5]
    assert rows[0]["overall_score"] >= rows[-1]["overall_score"]


def test_top_offers_plpgsql_function(client: httpx.Client, api: ApiContext) -> None:
    response = client.get(
        f"/api/v1/analytics/top-offers/{api.profile_id}",
        params={"limit": 5},
    )

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 5
    assert {"offer_id", "title", "company", "overall_score", "decision"} <= set(rows[0])
    assert rows[0]["decision"] in {"apply", "apply_with_gaps", "improve_cv"}


def test_application_funnel(client: httpx.Client, api: ApiContext) -> None:
    response = client.get(f"/api/v1/analytics/application-funnel/{api.profile_id}")

    assert response.status_code == 200
    rows = response.json()
    assert {row["status"] for row in rows} == {"saved", "applied", "interview"}
    assert all(row["total"] >= 1 for row in rows)

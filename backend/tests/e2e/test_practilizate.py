from __future__ import annotations

import csv
import io

import httpx

HEADER = [
    "title",
    "company",
    "url",
    "location",
    "modality",
    "salary_amount",
    "salary_currency",
    "published_at",
    "deadline_at",
    "requirements_text",
    "offer_id",
]
ROWS = [
    [
        "Practicante Practilizate",
        "Practilizate Corp",
        "https://example.com/practilizate/1",
        "Lima",
        "Hibrido",
        "1300",
        "PEN",
        "2026-11-01",
        "2026-12-31",
        "SQL y Excel",
        "9001",
    ],
    [
        "Practicante Duplicada",
        "Practilizate Corp",
        "https://example.com/practilizate/1",
        "Lima",
        "Hibrido",
        "1300",
        "PEN",
        "2026-11-01",
        "2026-12-31",
        "SQL y Excel",
        "9001",
    ],
    [
        "Practicante Sin Empresa",
        "",
        "https://example.com/practilizate/3",
        "Lima",
        "Remoto",
        "1000",
        "PEN",
        "2026-11-01",
        "2026-12-31",
        "Python",
        "9003",
    ],
    [
        "Practicante Sin URL",
        "Practilizate Corp Dos",
        "",
        "Arequipa",
        "Presencial",
        "1100",
        "PEN",
        "2026-11-02",
        "2026-12-30",
        "Power BI",
        "9004",
    ],
]
buffer = io.StringIO()
writer = csv.writer(buffer)
writer.writerow(HEADER)
writer.writerows(ROWS)
CSV_CONTENT = buffer.getvalue()


def test_practilizate_status_and_import(client: httpx.Client) -> None:
    status = client.get("/api/v1/offers/sources/practilizate/status")
    assert status.status_code == 200
    assert status.json()["enabled"] is True

    imported = client.post(
        "/api/v1/offers/import/practilizate",
        files={"file": ("practilizate.csv", CSV_CONTENT.encode("utf-8"), "text/csv")},
    )
    assert imported.status_code == 200, imported.text
    data = imported.json()
    assert data["created"] == 2
    assert data["duplicates"] == 1
    assert data["errors"]
    assert data["total_rows"] == 4
    assert data["preview"][0]["company"] == "Practilizate Corp"
    assert data["preview"][0]["salary_amount"] == 1300.0

    listed = client.get("/api/v1/offers", params={"source_type": "practilizate"})
    assert listed.status_code == 200
    offers = listed.json()
    assert len(offers) == 2
    assert {offer["company"] for offer in offers} == {
        "Practilizate Corp",
        "Practilizate Corp Dos",
    }
    assert all(offer["source_type"] == "practilizate" for offer in offers)


def test_practilizate_rejects_invalid_csv(client: httpx.Client) -> None:
    invalid = client.post(
        "/api/v1/offers/import/practilizate",
        files={"file": ("practilizate.csv", b"title,url\nSolo titulo,https://x.test", "text/csv")},
    )
    assert invalid.status_code == 422
    assert "company" in invalid.text

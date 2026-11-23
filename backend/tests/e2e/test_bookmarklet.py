from __future__ import annotations

import json

import httpx

JOB_LD = {
    "@context": "https://schema.org",
    "@type": "JobPosting",
    "title": "Practicante de Datos Bookmarklet",
    "description": "<p>Buscamos practicante con SQL y Power BI.</p><b>Modalidad hibrida</b>",
    "hiringOrganization": {"@type": "Organization", "name": "Bookmarklet Corp"},
    "jobLocation": {
        "@type": "Place",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Lima",
            "addressRegion": "Lima",
            "addressCountry": "PE",
        },
    },
    "employmentType": "Hibrido",
    "datePosted": "2026-11-01",
    "validThrough": "2026-12-20",
    "baseSalary": {
        "@type": "MonetaryAmount",
        "currency": "PEN",
        "value": {"@type": "QuantitativeValue", "value": 1500},
    },
}

CREATE_FIELDS = (
    "title",
    "company",
    "source_url",
    "location",
    "modality",
    "salary_text",
    "salary_amount",
    "salary_currency",
    "description",
    "requirements_text",
    "published_at",
    "deadline_at",
)


def test_bookmarklet_preview_create_and_duplicate(client: httpx.Client) -> None:
    url = "https://example.com/bookmarklet/datos-2026"
    preview = client.post(
        "/api/v1/offers/bookmarklet/preview",
        json={
            "url": url,
            "title": "Titulo de la pestana",
            "og_site_name": "Portal Demo",
            "jsonld": [json.dumps(JOB_LD)],
            "text": "Texto visible de la pagina",
        },
    )

    assert preview.status_code == 200, preview.text
    data = preview.json()
    assert data["title"] == "Practicante de Datos Bookmarklet"
    assert data["company"] == "Bookmarklet Corp"
    assert data["source_url"] == url
    assert data["location"] == "Lima, Lima, PE"
    assert data["salary_amount"] == 1500.0
    assert data["salary_currency"] == "PEN"
    assert data["deadline_at"].startswith("2026-12-20")
    assert data["confidence"] == 0.9
    assert data["warnings"] == []
    assert "<b>" not in (data["description"] or "").lower()

    payload = {key: data[key] for key in CREATE_FIELDS}
    created = client.post("/api/v1/offers/bookmarklet", json=payload)
    assert created.status_code == 201, created.text
    created_data = created.json()
    assert created_data["duplicate"] is False
    assert created_data["offer"]["source_type"] == "bookmarklet"
    assert created_data["offer"]["source_url"] == url

    duplicate = client.post("/api/v1/offers/bookmarklet", json=payload)
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["offer"]["id"] == created_data["offer"]["id"]


def test_bookmarklet_preview_falls_back_without_jsonld(client: httpx.Client) -> None:
    preview = client.post(
        "/api/v1/offers/bookmarklet/preview",
        json={
            "url": "https://example.com/bookmarklet/sin-jsonld",
            "title": "Solo titulo visible",
            "text": "Descripcion visible de la oferta",
        },
    )

    assert preview.status_code == 200, preview.text
    data = preview.json()
    assert data["title"] == "Solo titulo visible"
    assert data["company"] == ""
    assert data["confidence"] == 0.3
    assert any("JSON-LD" in warning for warning in data["warnings"])
    assert any("empresa" in warning.lower() for warning in data["warnings"])


def test_bookmarklet_preview_uses_graph_and_og_site_name(client: httpx.Client) -> None:
    graph = {"@context": "https://schema.org", "@graph": [{"@type": "WebPage"}, JOB_LD]}
    preview = client.post(
        "/api/v1/offers/bookmarklet/preview",
        json={
            "url": "https://example.com/bookmarklet/graph",
            "title": "Titulo",
            "og_site_name": "Portal Demo",
            "jsonld": [json.dumps(graph)],
            "text": "",
        },
    )

    assert preview.status_code == 200, preview.text
    data = preview.json()
    assert data["company"] == "Bookmarklet Corp"
    assert data["salary_amount"] == 1500.0
    assert data["warnings"] == []

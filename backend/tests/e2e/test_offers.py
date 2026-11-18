from __future__ import annotations

import asyncio
import threading
from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest

from practicv.adapters.sources.practicas_pe_mcp import FixtureMCPClient
from practicv.domain.errors import MCPUnavailableError

MANUAL_URL = "https://example.com/offers/manual-1"
CSV_URL = "https://example.com/offers/csv-1"
MCP_URLS = [
    "https://www.practicas.pe/oferta-convocatoria-9001.html",
    "https://www.practicas.pe/oferta-convocatoria-9002.html",
]

JOB_HTML = """
<!doctype html>
<html>
  <head>
    <title>Practicante de Analítica Web</title>
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": "Practicante de Analítica Web",
        "description": "<p>Buscamos practicante con Python y SQL.</p><b>Importante</b>",
        "hiringOrganization": {"@type": "Organization", "name": "WebData Perú"},
        "jobLocation": {
          "@type": "Place",
          "address": {
            "@type": "PostalAddress",
            "addressLocality": "Lima",
            "addressRegion": "Lima",
            "addressCountry": "PE"
          }
        },
        "employmentType": "Híbrido",
        "datePosted": "2026-11-01",
        "validThrough": "2026-12-20",
        "baseSalary": {
          "@type": "MonetaryAmount",
          "currency": "PEN",
          "value": {"@type": "QuantitativeValue", "value": 1350}
        }
      }
    </script>
  </head>
  <body>Oferta de prueba</body>
</html>
"""


class LocalOfferHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/robots.txt":
            body = b"User-agent: *\nAllow: /\n"
            content_type = "text/plain"
        elif self.path == "/job":
            body = JOB_HTML.encode("utf-8")
            content_type = "text/html; charset=utf-8"
        else:
            body = b"not found"
            content_type = "text/plain"
            self.send_response(404)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


@pytest.fixture(scope="module")
def local_offer_server() -> Generator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalOfferHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_manual_offer_and_duplicate(client: httpx.Client) -> None:
    payload = {
        "title": "Practicante de Datos Manual",
        "company": "Manual Corp",
        "source_url": MANUAL_URL,
        "location": "Lima",
        "modality": "Híbrido",
        "salary_text": "S/ 1,200",
        "salary_amount": 1200,
        "description": "Oferta manual de datos.",
        "requirements_text": "Python, SQL",
        "deadline_at": "2026-12-31T00:00:00Z",
    }

    created = client.post("/api/v1/offers/manual", json=payload)
    assert created.status_code == 201, created.text
    created_data = created.json()
    assert created_data["duplicate"] is False
    assert created_data["offer"]["source_type"] == "manual"
    assert created_data["offer"]["source_url"] == MANUAL_URL
    offer_id = created_data["offer"]["id"]

    duplicate = client.post("/api/v1/offers/manual", json=payload)
    assert duplicate.status_code == 200
    duplicate_data = duplicate.json()
    assert duplicate_data["duplicate"] is True
    assert duplicate_data["offer"]["id"] == offer_id

    detail = client.get(f"/api/v1/offers/{offer_id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == payload["title"]


def test_csv_import_preview_and_duplicate(client: httpx.Client) -> None:
    csv_content = (
        "titulo,empresa,url,ubicacion,modalidad,sueldo,descripcion,requisitos,fecha_limite\n"
        "Practicante CSV Sin Sueldo,CSV Corp,"
        f"{CSV_URL},Lima,Remoto,,Oferta CSV,Excel,2026-12-15\n"
        "Practicante Duplicada,Duplicada Corp,"
        f"{MANUAL_URL},Lima,Híbrido,1000,Duplicada,SQL,2026-12-20\n"
    )
    response = client.post(
        "/api/v1/offers/import/csv",
        files={"file": ("ofertas.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["created"] == 1
    assert data["duplicates"] == 1
    assert data["total_rows"] == 2
    assert len(data["preview"]) == 2
    assert any("no salary" in warning for warning in data["warnings"])
    assert data["preview"][0]["salary_amount"] is None


def test_url_capture_jsonld(
    client: httpx.Client,
    local_offer_server: str,
) -> None:
    url = f"{local_offer_server}/job"
    response = client.post("/api/v1/offers/capture-url", json={"url": url})

    assert response.status_code == 201, response.text
    data = response.json()
    offer = data["offer"]
    assert data["duplicate"] is False
    assert offer["title"] == "Practicante de Analítica Web"
    assert offer["company"] == "WebData Perú"
    assert offer["source_type"] == "url"
    assert offer["salary_amount"] == 1350.0
    assert offer["deadline_at"].startswith("2026-12-20")
    assert "<b>" not in (offer["description"] or "").lower()

    duplicate = client.post("/api/v1/offers/capture-url", json={"url": url})
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True


def test_mcp_search_and_import(client: httpx.Client) -> None:
    status = client.get("/api/v1/offers/sources/status")
    assert status.status_code == 200
    status_data = status.json()
    assert status_data["mcp"] == "available"
    assert status_data["filters"]["carreras"]

    search = client.post(
        "/api/v1/offers/mcp/search",
        json={
            "q": "datos",
            "modality": "preprofesional",
            "career": "18",
            "department": "15",
            "limit": 10,
        },
    )
    assert search.status_code == 200, search.text
    search_data = search.json()
    assert search_data["total"] == 2
    assert len(search_data["results"]) == 2
    assert search_data["results"][0]["url"] in MCP_URLS

    imported = client.post(
        "/api/v1/offers/mcp/import",
        json={"urls": MCP_URLS},
    )
    assert imported.status_code == 200, imported.text
    imported_data = imported.json()
    assert imported_data["created"] == 2
    assert imported_data["duplicates"] == 0

    duplicate = client.post(
        "/api/v1/offers/mcp/import",
        json={"urls": MCP_URLS},
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicates"] == 2

    listed = client.get("/api/v1/offers", params={"source_type": "mcp_practicas_pe"})
    assert listed.status_code == 200
    assert len(listed.json()) == 2


def test_mcp_fixture_failure_mode(tmp_path: Path) -> None:
    """Failure modes: missing fixture dir, missing file, invalid JSON."""
    client = FixtureMCPClient(str(tmp_path))
    with pytest.raises(MCPUnavailableError) as exc_info:
        asyncio.run(client.search())
    assert exc_info.value.code == "mcp_unavailable"
    assert exc_info.value.status_code == 503

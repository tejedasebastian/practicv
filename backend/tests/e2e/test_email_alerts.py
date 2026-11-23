from __future__ import annotations

import threading
from collections.abc import Generator
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

JOB_HTML = """
<!doctype html>
<html>
  <head>
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": "Practicante de Datos desde Correo",
        "description": "<p>Oferta importada desde una alerta de correo.</p>",
        "hiringOrganization": {"@type": "Organization", "name": "Correo Corp"},
        "jobLocation": {"@type": "Place", "address": {"addressLocality": "Lima"}},
        "validThrough": "2026-12-31",
        "baseSalary": {
          "@type": "MonetaryAmount",
          "currency": "PEN",
          "value": {"@type": "QuantitativeValue", "value": 1400}
        }
      }
    </script>
    <title>Oferta de correo</title>
  </head>
  <body>Oferta de correo</body>
</html>
"""


class EmailOfferHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/robots.txt":
            body = b"User-agent: *\nAllow: /\n"
            status = 200
            content_type = "text/plain"
        elif self.path == "/job":
            body = JOB_HTML.encode("utf-8")
            status = 200
            content_type = "text/html; charset=utf-8"
        else:
            body = b"not found"
            status = 404
            content_type = "text/plain"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


@pytest.fixture(scope="module")
def email_server() -> Generator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), EmailOfferHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _email(links: list[tuple[str, str]]) -> bytes:
    message = EmailMessage()
    message["Subject"] = "Ofertas de la semana"
    message["From"] = "alertas@example.com"
    message["To"] = "estudiante@example.com"
    message.set_content("Nuevas ofertas para ti.")
    html = "<html><body><h1>Ofertas</h1>" + "".join(
        f'<p><a href="{url}">{title}</a></p>' for url, title in links
    )
    html += "</body></html>"
    message.add_alternative(html, subtype="html")
    return message.as_bytes()


def test_email_preview_and_import(
    client: httpx.Client,
    email_server: str,
) -> None:
    job_url = f"{email_server}/job"
    broken_url = f"{email_server}/broken"
    content = _email(
        [
            (job_url, "Practicante de Datos desde Correo"),
            (broken_url, "Oferta rota"),
            (job_url, "Practicante duplicado en el correo"),
        ]
    )

    preview = client.post(
        "/api/v1/offers/import/email/preview",
        files={"file": ("alertas.eml", content, "message/rfc822")},
    )
    assert preview.status_code == 200, preview.text
    data = preview.json()
    assert data["subject"] == "Ofertas de la semana"
    assert len(data["candidates"]) == 2
    assert data["candidates"][0]["url"] == job_url
    assert data["candidates"][0]["title"] == "Practicante de Datos desde Correo"
    assert data["warnings"] == []

    imported = client.post(
        "/api/v1/offers/import/email",
        json={"urls": [job_url, broken_url]},
    )
    assert imported.status_code == 200, imported.text
    imported_data = imported.json()
    assert imported_data["created"] == 1
    assert imported_data["duplicates"] == 0
    assert imported_data["errors"]
    assert imported_data["preview"][0]["company"] == "Correo Corp"
    assert imported_data["preview"][0]["salary_amount"] == 1400.0

    duplicate = client.post(
        "/api/v1/offers/import/email",
        json={"urls": [job_url]},
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicates"] == 1


def test_email_preview_rejects_empty_file(client: httpx.Client) -> None:
    response = client.post(
        "/api/v1/offers/import/email/preview",
        files={"file": ("vacio.eml", b"", "message/rfc822")},
    )
    assert response.status_code == 422
    assert "empty" in response.text.lower()

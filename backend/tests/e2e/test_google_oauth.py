from __future__ import annotations

import base64
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from practicv.adapters.auth.google_oauth import (
    GoogleOAuthClient,
    MemoryTokenStore,
    consume_state,
    create_state,
    reset_state,
)
from practicv.config import Settings

HTML_BODY = (
    '<html><body><a href="https://example.com/ofertas/datos">'
    "Practicante de Datos desde Gmail</a></body></html>"
)


def _b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/token":
        body = request.content.decode()
        if "grant_type=refresh_token" in body:
            return httpx.Response(
                200,
                json={
                    "access_token": "access-refreshed",
                    "expires_in": 3600,
                    "scope": "https://www.googleapis.com/auth/gmail.readonly",
                    "token_type": "Bearer",
                },
            )
        return httpx.Response(
            200,
            json={
                "access_token": "access-initial",
                "refresh_token": "refresh-1",
                "expires_in": 3600,
                "scope": "https://www.googleapis.com/auth/gmail.readonly",
                "token_type": "Bearer",
            },
        )
    if path == "/oauth2/v3/userinfo":
        assert request.headers["authorization"] == "Bearer access-initial"
        return httpx.Response(200, json={"email": "demo@example.com"})
    if path == "/gmail/v1/users/me/messages":
        return httpx.Response(200, json={"messages": [{"id": "m1"}]})
    if path == "/gmail/v1/users/me/messages/m1":
        if request.url.params.get("format") == "metadata":
            return httpx.Response(
                200,
                json={
                    "id": "m1",
                    "snippet": "Oferta de datos",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Alertas de la semana"},
                            {"name": "From", "value": "alertas@example.com"},
                            {"name": "Date", "value": "Mon, 23 Nov 2026 10:00:00 +0000"},
                        ]
                    },
                },
            )
        return httpx.Response(
            200,
            json={
                "id": "m1",
                "snippet": "Oferta de datos",
                "payload": {
                    "mimeType": "text/html",
                    "headers": [
                        {"name": "Subject", "value": "Alertas de la semana"},
                        {"name": "From", "value": "alertas@example.com"},
                    ],
                    "body": {"data": _b64(HTML_BODY)},
                },
            },
        )
    return httpx.Response(404, json={"error": "not found"})


@pytest.fixture(autouse=True)
def _reset_oauth_state() -> None:
    reset_state()


def test_authorization_url_and_state() -> None:
    settings = Settings(
        google_client_id="client-id",
        google_client_secret="client-secret",
        google_redirect_uri="http://localhost:8000/api/v1/email/oauth/google/callback",
    )
    client = GoogleOAuthClient(settings=settings, store=MemoryTokenStore())
    state = create_state()
    url = client.authorization_url(state)
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert parsed.netloc == "accounts.google.com"
    assert params["client_id"] == ["client-id"]
    assert params["access_type"] == ["offline"]
    assert params["prompt"] == ["consent"]
    assert params["state"] == [state]
    assert params["scope"] == ["https://www.googleapis.com/auth/gmail.readonly"]
    assert consume_state(state) is True
    assert consume_state(state) is False


def test_exchange_list_and_preview_message() -> None:
    settings = Settings(
        google_client_id="client-id",
        google_client_secret="client-secret",
        google_redirect_uri="http://localhost:8000/api/v1/email/oauth/google/callback",
    )
    store = MemoryTokenStore()
    transport = httpx.MockTransport(_handler)
    client = GoogleOAuthClient(
        settings=settings,
        store=store,
        http=httpx.Client(transport=transport),
    )

    token = client.exchange_code("code-1")
    assert token["refresh_token"] == "refresh-1"
    assert store.load()["email"] == "demo@example.com"
    assert client.status()["connected"] is True
    assert client.status()["email"] == "demo@example.com"

    messages = client.list_messages("alertas", 10)
    assert len(messages) == 1
    assert messages[0].subject == "Alertas de la semana"
    assert messages[0].sender == "alertas@example.com"

    preview = client.preview_message("m1")
    assert len(preview.candidates) == 1
    assert preview.candidates[0].url == "https://example.com/ofertas/datos"
    assert preview.candidates[0].title == "Practicante de Datos desde Gmail"

    store.save({**store.load(), "expires_at": 0})
    assert client.refresh_access_token() == "access-refreshed"


def test_status_without_connection() -> None:
    settings = Settings(
        google_client_id="client-id",
        google_client_secret="client-secret",
    )
    client = GoogleOAuthClient(settings=settings, store=MemoryTokenStore())
    status = client.status()
    assert status["configured"] is True
    assert status["connected"] is False
    assert status["email"] is None

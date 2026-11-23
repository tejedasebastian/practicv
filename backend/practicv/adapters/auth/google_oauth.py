from __future__ import annotations

import base64
import json
import secrets
import time
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any
from urllib.parse import urlencode

import httpx
import keyring
import keyring.errors
from bs4 import BeautifulSoup

from practicv.adapters.sources.email_alerts import EmailPreview, parse_email
from practicv.config import Settings, get_settings
from practicv.domain.errors import ValidationError

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
STATE_TTL_SECONDS = 600
KEYRING_SERVICE = "practicv-google-oauth"
KEYRING_USER = "default"


class TokenStore:
    def load(self) -> dict | None:
        raise NotImplementedError

    def save(self, token: dict) -> None:
        raise NotImplementedError

    def delete(self) -> None:
        raise NotImplementedError


class KeyringTokenStore(TokenStore):
    def __init__(self, service: str = KEYRING_SERVICE, username: str = KEYRING_USER) -> None:
        self.service = service
        self.username = username

    def load(self) -> dict | None:
        try:
            raw = keyring.get_password(self.service, self.username)
        except keyring.errors.KeyringError:
            return None
        if not raw:
            return None
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) else None

    def save(self, token: dict) -> None:
        keyring.set_password(self.service, self.username, json.dumps(token))

    def delete(self) -> None:
        try:
            keyring.delete_password(self.service, self.username)
        except keyring.errors.PasswordDeleteError:
            return


class MemoryTokenStore(TokenStore):
    def __init__(self) -> None:
        self.value: dict | None = None

    def load(self) -> dict | None:
        return dict(self.value) if self.value else None

    def save(self, token: dict) -> None:
        self.value = dict(token)

    def delete(self) -> None:
        self.value = None


_token_store: TokenStore = KeyringTokenStore()
_states: dict[str, float] = {}


def get_token_store() -> TokenStore:
    return _token_store


def set_token_store(store: TokenStore) -> None:
    global _token_store
    _token_store = store


def create_state() -> str:
    state = secrets.token_urlsafe(24)
    _states[state] = time.time() + STATE_TTL_SECONDS
    return state


def consume_state(state: str) -> bool:
    deadline = _states.pop(state, None)
    return bool(deadline and deadline >= time.time())


def reset_state() -> None:
    _states.clear()


@dataclass(slots=True)
class GmailMessage:
    id: str
    subject: str
    sender: str
    date: str
    snippet: str


class GoogleOAuthClient:
    def __init__(
        self,
        settings: Settings | None = None,
        store: TokenStore | None = None,
        http: Any | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.store = store or get_token_store()
        self.http = http or httpx

    @property
    def configured(self) -> bool:
        return bool(self.settings.google_client_id and self.settings.google_client_secret)

    def authorization_url(self, state: str) -> str:
        if not self.configured:
            raise ValidationError(
                "Google OAuth is not configured.",
                {"hint": "Set PRACTICV_GOOGLE_CLIENT_ID and PRACTICV_GOOGLE_CLIENT_SECRET."},
            )
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": self.settings.google_redirect_uri,
            "response_type": "code",
            "scope": self.settings.google_oauth_scopes,
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
        }
        return f"{AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> dict:
        if not self.configured:
            raise ValidationError("Google OAuth is not configured.")
        response = self.http.post(
            TOKEN_URL,
            data={
                "client_id": self.settings.google_client_id,
                "client_secret": self.settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.settings.google_redirect_uri,
            },
            timeout=15,
        )
        if response.status_code >= 400:
            raise ValidationError(
                "Google rejected the authorization code.",
                {"status": response.status_code, "body": response.text[:500]},
            )
        payload = response.json()
        token = {
            "access_token": payload.get("access_token"),
            "refresh_token": payload.get("refresh_token"),
            "expires_at": time.time() + int(payload.get("expires_in", 3600)) - 60,
            "scope": payload.get("scope"),
            "token_type": payload.get("token_type"),
        }
        previous = self.store.load() or {}
        if not token["refresh_token"] and previous.get("refresh_token"):
            token["refresh_token"] = previous["refresh_token"]
        self.store.save(token)
        try:
            email = self._fetch_email(token["access_token"])
        except (httpx.HTTPError, ValueError, KeyError):
            email = previous.get("email")
        if email:
            token["email"] = email
            self.store.save(token)
        return token

    def _fetch_email(self, access_token: str) -> str | None:
        response = self.http.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if response.status_code >= 400:
            return None
        payload = response.json()
        return payload.get("email")

    def _token(self) -> dict:
        token = self.store.load()
        if not token:
            raise ValidationError(
                "Google account is not connected.",
                {"hint": "Open /api/v1/email/google/authorize first."},
            )
        return token

    def refresh_access_token(self) -> str:
        token = self._token()
        if token.get("access_token") and token.get("expires_at", 0) > time.time() + 60:
            return token["access_token"]
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            raise ValidationError(
                "Google refresh token is missing.",
                {"hint": "Reconnect the Google account."},
            )
        response = self.http.post(
            TOKEN_URL,
            data={
                "client_id": self.settings.google_client_id,
                "client_secret": self.settings.google_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=15,
        )
        if response.status_code >= 400:
            raise ValidationError(
                "Google refresh failed.",
                {"status": response.status_code, "body": response.text[:500]},
            )
        payload = response.json()
        token["access_token"] = payload.get("access_token")
        token["expires_at"] = time.time() + int(payload.get("expires_in", 3600)) - 60
        token["scope"] = payload.get("scope", token.get("scope"))
        token["token_type"] = payload.get("token_type", token.get("token_type"))
        self.store.save(token)
        return token["access_token"]

    def status(self) -> dict:
        token = self.store.load() if self.configured else None
        return {
            "configured": self.configured,
            "connected": bool(token and token.get("refresh_token")),
            "email": token.get("email") if token else None,
            "detail": (
                "Google OAuth is not configured."
                if not self.configured
                else "Google account connected."
                if token and token.get("refresh_token")
                else "Google account not connected."
            ),
        }

    def _gmail_get(self, path: str, params: dict | None = None) -> dict:
        response = self.http.get(
            f"{GMAIL_API}{path}",
            params=params or {},
            headers={"Authorization": f"Bearer {self.refresh_access_token()}"},
            timeout=20,
        )
        if response.status_code == 401:
            self.store.delete()
            raise ValidationError(
                "Google session expired. Reconnect the account.",
                {"status": 401},
            )
        if response.status_code >= 400:
            raise ValidationError(
                "Gmail request failed.",
                {"status": response.status_code, "body": response.text[:500]},
            )
        return response.json()

    def list_messages(self, query: str = "", limit: int = 10) -> list[GmailMessage]:
        payload = self._gmail_get(
            "/messages",
            {"maxResults": min(max(limit, 1), 20), "q": query} if query else {"maxResults": limit},
        )
        messages: list[GmailMessage] = []
        for item in payload.get("messages", []):
            message_id = item.get("id")
            if not message_id:
                continue
            data = self._gmail_get(
                f"/messages/{message_id}",
                {
                    "format": "metadata",
                    "metadataHeaders": ["Subject", "From", "Date"],
                },
            )
            message_payload = data.get("payload") or {}
            headers = {
                str(header.get("name", "")).lower(): header.get("value", "")
                for header in message_payload.get("headers", [])
                if isinstance(header, dict)
            }
            messages.append(
                GmailMessage(
                    id=message_id,
                    subject=str(headers.get("subject", "")),
                    sender=str(headers.get("from", "")),
                    date=str(headers.get("date", "")),
                    snippet=str(data.get("snippet", "")),
                )
            )
        return messages

    def preview_message(self, message_id: str) -> EmailPreview:
        data = self._gmail_get(f"/messages/{message_id}", {"format": "full"})
        payload = data.get("payload") or {}
        return parse_email(self._message_to_email(payload, data.get("snippet", "")))

    def _message_to_email(self, payload: dict, snippet: str = "") -> bytes:
        message = EmailMessage()
        headers = {
            str(header.get("name", "")).lower(): header.get("value", "")
            for header in payload.get("headers", [])
            if isinstance(header, dict)
        }
        for name, header in (
            ("Subject", "subject"),
            ("From", "from"),
            ("To", "to"),
            ("Date", "date"),
        ):
            if headers.get(header):
                message[name] = str(headers[header])

        bodies: dict[str, list[str]] = {"text/plain": [], "text/html": []}

        def collect(part: dict) -> None:
            mime_type = str(part.get("mimeType", ""))
            encoded = (part.get("body") or {}).get("data")
            if encoded and mime_type in bodies:
                try:
                    decoded = base64.urlsafe_b64decode(encoded + "===").decode(
                        "utf-8", errors="replace"
                    )
                except (ValueError, TypeError):
                    decoded = ""
                if decoded:
                    bodies[mime_type].append(decoded)
            for child in part.get("parts", []):
                if isinstance(child, dict):
                    collect(child)

        collect(payload)
        text = "\n".join(bodies["text/plain"]).strip()
        html = "\n".join(bodies["text/html"]).strip()
        if text:
            message.set_content(text)
        elif html:
            message.set_content(BeautifulSoup(html, "html.parser").get_text(" ", strip=True))
        else:
            message.set_content(snippet or " ")
        if html:
            message.add_alternative(html, subtype="html")
        return message.as_bytes()

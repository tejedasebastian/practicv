from __future__ import annotations

from dataclasses import asdict

import httpx
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from practicv.adapters.auth.google_oauth import (
    GoogleOAuthClient,
    consume_state,
    create_state,
)
from practicv.adapters.db.session import get_session
from practicv.api.schemas import (
    EmailCandidateResponse,
    EmailPreviewResponse,
    GmailImportRequest,
    GmailMessageListResponse,
    GmailMessageRequest,
    GmailMessageResponse,
    GoogleAuthorizeResponse,
    GoogleStatusResponse,
    OfferImportResponse,
)
from practicv.config import get_settings
from practicv.domain.errors import ValidationError
from practicv.services.email_alerts import import_email_urls

router = APIRouter(prefix="/email", tags=["email"])


def _client() -> GoogleOAuthClient:
    return GoogleOAuthClient()


@router.get("/google/status", response_model=GoogleStatusResponse)
def google_status() -> GoogleStatusResponse:
    return GoogleStatusResponse(**_client().status())


@router.get("/google/authorize", response_model=GoogleAuthorizeResponse)
def google_authorize() -> GoogleAuthorizeResponse:
    state = create_state()
    return GoogleAuthorizeResponse(auth_url=_client().authorization_url(state))


@router.get("/google/callback")
def google_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> RedirectResponse:
    settings = get_settings()
    target = f"{settings.frontend_origin}/ofertas"
    if error or not code or not state or not consume_state(state):
        return RedirectResponse(f"{target}?gmail=error")
    try:
        _client().exchange_code(code)
    except (ValidationError, httpx.HTTPError):
        return RedirectResponse(f"{target}?gmail=error")
    return RedirectResponse(f"{target}?gmail=connected")


@router.get("/google/messages", response_model=GmailMessageListResponse)
def google_messages(
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=10, ge=1, le=20),
) -> GmailMessageListResponse:
    messages = _client().list_messages(q, limit)
    return GmailMessageListResponse(
        messages=[
            GmailMessageResponse(
                id=item.id,
                subject=item.subject,
                sender=item.sender,
                date=item.date,
                snippet=item.snippet,
            )
            for item in messages
        ],
        warnings=[] if messages else ["No se encontraron correos para esa busqueda."],
    )


@router.post("/google/preview", response_model=EmailPreviewResponse)
def google_preview(payload: GmailMessageRequest) -> EmailPreviewResponse:
    preview = _client().preview_message(payload.message_id)
    return EmailPreviewResponse(
        subject=preview.subject,
        candidates=[
            EmailCandidateResponse(url=item.url, title=item.title, source=item.source)
            for item in preview.candidates
        ],
        warnings=preview.warnings,
    )


@router.post("/google/import", response_model=OfferImportResponse)
def google_import(
    payload: GmailImportRequest,
    session: Session = Depends(get_session),
) -> OfferImportResponse:
    settings = get_settings()
    result = import_email_urls(
        session,
        payload.urls,
        settings.url_capture_user_agent,
    )
    session.commit()
    return OfferImportResponse(**asdict(result))

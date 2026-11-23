from __future__ import annotations

from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.orm import Session

from practicv.adapters.db.repositories import OfferRepository
from practicv.adapters.db.session import get_session
from practicv.adapters.sources.email_alerts import parse_email
from practicv.adapters.sources.practicas_pe_mcp import MCPClient, get_mcp_client
from practicv.adapters.sources.practilizate import parse_practilizate_csv
from practicv.api.schemas import (
    BookmarkletPreviewRequest,
    BookmarkletPreviewResponse,
    EmailCandidateResponse,
    EmailImportRequest,
    EmailPreviewResponse,
    MCPImportRequest,
    MCPSearchRequest,
    MCPSearchResponse,
    OfferCreate,
    OfferImportResponse,
    OfferMutationResponse,
    OfferResponse,
    PractilizateStatusResponse,
    SourceStatusResponse,
    UrlCaptureRequest,
)
from practicv.config import get_settings
from practicv.domain.enums import SourceType
from practicv.domain.errors import MCPUnavailableError, NotFoundError, ValidationError
from practicv.services.bookmarklet import extract_bookmarklet
from practicv.services.email_alerts import import_email_urls
from practicv.services.offers import (
    ImportResult,
    capture_url,
    import_rows,
    parse_import_file,
    save_offer,
)

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post("/manual", response_model=OfferMutationResponse)
def create_manual_offer(
    payload: OfferCreate,
    response: Response,
    session: Session = Depends(get_session),
) -> OfferMutationResponse:
    offer, duplicate = save_offer(session, payload.model_dump(), SourceType.MANUAL)
    session.commit()
    response.status_code = 200 if duplicate else 201
    return OfferMutationResponse(
        offer=OfferResponse.model_validate(offer),
        duplicate=duplicate,
    )


@router.post("/bookmarklet/preview", response_model=BookmarkletPreviewResponse)
def preview_bookmarklet(
    payload: BookmarkletPreviewRequest,
) -> BookmarkletPreviewResponse:
    return BookmarkletPreviewResponse(**extract_bookmarklet(payload.model_dump()))


@router.post("/bookmarklet", response_model=OfferMutationResponse)
def create_bookmarklet_offer(
    payload: OfferCreate,
    response: Response,
    session: Session = Depends(get_session),
) -> OfferMutationResponse:
    offer, duplicate = save_offer(session, payload.model_dump(), SourceType.BOOKMARKLET)
    session.commit()
    response.status_code = 200 if duplicate else 201
    return OfferMutationResponse(
        offer=OfferResponse.model_validate(offer),
        duplicate=duplicate,
    )


@router.post("/import/csv", response_model=OfferImportResponse)
async def import_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> OfferImportResponse:
    content = await file.read()
    if not content:
        raise ValidationError("The import file is empty.")
    rows = parse_import_file(content, file.filename or "import.csv")
    result = import_rows(session, rows, SourceType.CSV)
    session.commit()
    return OfferImportResponse(**asdict(result))


@router.post("/import/email/preview", response_model=EmailPreviewResponse)
async def preview_email(
    file: UploadFile = File(...),
) -> EmailPreviewResponse:
    content = await file.read()
    preview = parse_email(content)
    return EmailPreviewResponse(
        subject=preview.subject,
        candidates=[
            EmailCandidateResponse(url=item.url, title=item.title, source=item.source)
            for item in preview.candidates
        ],
        warnings=preview.warnings,
    )


@router.post("/import/email", response_model=OfferImportResponse)
def import_email(
    payload: EmailImportRequest,
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


@router.get("/sources/practilizate/status", response_model=PractilizateStatusResponse)
def practilizate_status() -> PractilizateStatusResponse:
    enabled = get_settings().practilizate_enabled
    return PractilizateStatusResponse(
        enabled=enabled,
        detail=(
            "Practilizate adapter is enabled."
            if enabled
            else "Practilizate adapter is disabled. Set PRACTICV_PRACTILIZATE_ENABLED=true."
        ),
    )


@router.post("/import/practilizate", response_model=OfferImportResponse)
async def import_practilizate(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> OfferImportResponse:
    settings = get_settings()
    if not settings.practilizate_enabled:
        raise ValidationError(
            "Practilizate adapter is disabled.",
            {"hint": "Set PRACTICV_PRACTILIZATE_ENABLED=true to enable it."},
        )
    content = await file.read()
    rows = parse_practilizate_csv(content)
    result = import_rows(session, rows, SourceType.PRACTILIZATE)
    session.commit()
    return OfferImportResponse(**asdict(result))


@router.post("/capture-url", response_model=OfferMutationResponse)
def capture_offer_url(
    payload: UrlCaptureRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> OfferMutationResponse:
    settings = get_settings()
    offer, duplicate = capture_url(
        session,
        payload.url,
        settings.url_capture_user_agent,
    )
    session.commit()
    response.status_code = 200 if duplicate else 201
    return OfferMutationResponse(
        offer=OfferResponse.model_validate(offer),
        duplicate=duplicate,
    )


@router.get("/sources/status", response_model=SourceStatusResponse)
async def source_status(
    client: MCPClient = Depends(get_mcp_client),
) -> SourceStatusResponse:
    try:
        filters = await client.list_filters()
        return SourceStatusResponse(mcp="available", filters=filters)
    except MCPUnavailableError as exc:
        return SourceStatusResponse(mcp="unavailable", detail=exc.message)


@router.post("/mcp/search", response_model=MCPSearchResponse)
async def mcp_search(
    payload: MCPSearchRequest,
    client: MCPClient = Depends(get_mcp_client),
) -> MCPSearchResponse:
    result = await client.search(
        q=payload.q,
        modality=payload.modality,
        career=payload.career,
        department=payload.department,
        order=payload.order,
        page=payload.page,
        pages=payload.pages,
        limit=payload.limit,
    )
    results = result.get("resultados", [])
    return MCPSearchResponse(
        results=results,
        total=int(result.get("total_devueltos", len(results))),
        warning=result.get("advertencia"),
    )


@router.post("/mcp/import", response_model=OfferImportResponse)
async def mcp_import(
    payload: MCPImportRequest,
    session: Session = Depends(get_session),
    client: MCPClient = Depends(get_mcp_client),
) -> OfferImportResponse:
    result = ImportResult(total_rows=len(payload.urls))
    for index, url in enumerate(payload.urls, start=1):
        try:
            raw = await client.get_offer(url)
            offer, duplicate = save_offer(session, raw, SourceType.MCP_PRACTICAS_PE)
            if duplicate:
                result.duplicates += 1
            else:
                result.created += 1
                result.offer_ids.append(str(offer.id))
            if index <= 5:
                result.preview.append(
                    {
                        "title": offer.title,
                        "company": offer.company,
                        "salary_amount": offer.salary_amount,
                        "source_url": offer.source_url,
                        "duplicate": duplicate,
                    }
                )
        except ValidationError as exc:
            result.errors.append({"row": index, "message": exc.message, "details": exc.details})
    session.commit()
    return OfferImportResponse(**asdict(result))


@router.get("", response_model=list[OfferResponse])
def list_offers(
    source_type: SourceType | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[OfferResponse]:
    offers = OfferRepository(session).list(limit=limit, source_type=source_type)
    return [OfferResponse.model_validate(offer) for offer in offers]


@router.get("/{offer_id}", response_model=OfferResponse)
def get_offer(
    offer_id: UUID,
    session: Session = Depends(get_session),
) -> OfferResponse:
    offer = OfferRepository(session).get(offer_id)
    if offer is None:
        raise NotFoundError("Offer not found", {"offer_id": str(offer_id)})
    return OfferResponse.model_validate(offer)

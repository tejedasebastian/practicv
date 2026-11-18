from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from practicv.adapters.db.repositories import (
    ApplicationRepository,
    MatchRepository,
    OfferRepository,
    ReminderRepository,
)
from practicv.adapters.db.session import get_session
from practicv.api.schemas import (
    ApplicationCreate,
    ApplicationEventCreate,
    ApplicationEventResponse,
    ApplicationMutationResponse,
    ApplicationResponse,
    ApplicationUpdate,
    ApplicationWithOfferResponse,
    MatchResponse,
    OfferResponse,
    ReminderCreate,
    ReminderResponse,
)
from practicv.domain.entities import Reminder
from practicv.domain.errors import NotFoundError
from practicv.services.applications import create_application

router = APIRouter(tags=["applications"])


def _get_application_or_404(
    session: Session,
    application_id: UUID,
):
    application = ApplicationRepository(session).get(application_id)
    if application is None:
        raise NotFoundError("Application not found", {"application_id": str(application_id)})
    return application


@router.post("/applications", response_model=ApplicationMutationResponse)
def create_application_route(
    payload: ApplicationCreate,
    response: Response,
    session: Session = Depends(get_session),
) -> ApplicationMutationResponse:
    application, duplicate = create_application(
        session,
        profile_id=payload.profile_id,
        offer_id=payload.offer_id,
        status=payload.status,
        applied_at=payload.applied_at,
        next_action_at=payload.next_action_at,
        next_action_note=payload.next_action_note,
        notes=payload.notes,
        cv_document_id=payload.cv_document_id,
    )
    session.commit()
    response.status_code = 200 if duplicate else 201
    return ApplicationMutationResponse(
        application=ApplicationResponse.model_validate(application),
        duplicate=duplicate,
    )


@router.get("/applications", response_model=list[ApplicationWithOfferResponse])
def list_applications(
    profile_id: UUID = Query(...),
    session: Session = Depends(get_session),
) -> list[ApplicationWithOfferResponse]:
    offer_repo = OfferRepository(session)
    match_repo = MatchRepository(session)
    results: list[ApplicationWithOfferResponse] = []
    for application in ApplicationRepository(session).list_by_profile(profile_id):
        offer = offer_repo.get(application.offer_id)
        if offer is None:
            continue
        match = match_repo.get_latest(profile_id, application.offer_id)
        results.append(
            ApplicationWithOfferResponse(
                application=ApplicationResponse.model_validate(application),
                offer=OfferResponse.model_validate(offer),
                match=MatchResponse.model_validate(match) if match else None,
            )
        )
    return results


@router.get("/applications/{application_id}", response_model=ApplicationWithOfferResponse)
def get_application(
    application_id: UUID,
    session: Session = Depends(get_session),
) -> ApplicationWithOfferResponse:
    application = _get_application_or_404(session, application_id)
    offer = OfferRepository(session).get(application.offer_id)
    if offer is None:
        raise NotFoundError("Offer not found", {"offer_id": str(application.offer_id)})
    match = MatchRepository(session).get_latest(application.profile_id, application.offer_id)
    return ApplicationWithOfferResponse(
        application=ApplicationResponse.model_validate(application),
        offer=OfferResponse.model_validate(offer),
        match=MatchResponse.model_validate(match) if match else None,
    )


@router.patch("/applications/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: UUID,
    payload: ApplicationUpdate,
    session: Session = Depends(get_session),
) -> ApplicationResponse:
    _get_application_or_404(session, application_id)
    fields = payload.model_dump(exclude_unset=True)
    updated = ApplicationRepository(session).update(application_id, **fields)
    session.commit()
    return ApplicationResponse.model_validate(updated)


@router.post(
    "/applications/{application_id}/events",
    response_model=ApplicationEventResponse,
    status_code=201,
)
def add_application_event(
    application_id: UUID,
    payload: ApplicationEventCreate,
    session: Session = Depends(get_session),
) -> ApplicationEventResponse:
    _get_application_or_404(session, application_id)
    event = ApplicationRepository(session).add_event(
        application_id,
        payload.event_type,
        payload.event_at,
        payload.notes,
    )
    session.commit()
    return ApplicationEventResponse.model_validate(event)


@router.get(
    "/applications/{application_id}/events",
    response_model=list[ApplicationEventResponse],
)
def list_application_events(
    application_id: UUID,
    session: Session = Depends(get_session),
) -> list[ApplicationEventResponse]:
    _get_application_or_404(session, application_id)
    events = ApplicationRepository(session).list_events(application_id)
    return [ApplicationEventResponse.model_validate(event) for event in events]


@router.post(
    "/applications/{application_id}/reminders",
    response_model=ReminderResponse,
    status_code=201,
)
def add_application_reminder(
    application_id: UUID,
    payload: ReminderCreate,
    session: Session = Depends(get_session),
) -> ReminderResponse:
    _get_application_or_404(session, application_id)
    reminder = ReminderRepository(session).create(
        Reminder(
            application_id=application_id,
            due_at=payload.due_at,
            channel=payload.channel,
            message=payload.message,
        )
    )
    session.commit()
    return ReminderResponse.model_validate(reminder)


@router.get(
    "/applications/{application_id}/reminders",
    response_model=list[ReminderResponse],
)
def list_application_reminders(
    application_id: UUID,
    session: Session = Depends(get_session),
) -> list[ReminderResponse]:
    _get_application_or_404(session, application_id)
    reminders = ReminderRepository(session).list_by_application(application_id)
    return [ReminderResponse.model_validate(reminder) for reminder in reminders]


@router.get(
    "/profiles/{profile_id}/reminders",
    response_model=list[ReminderResponse],
)
def list_profile_reminders(
    profile_id: UUID,
    session: Session = Depends(get_session),
) -> list[ReminderResponse]:
    reminders = ReminderRepository(session).list_by_profile(profile_id)
    return [ReminderResponse.model_validate(reminder) for reminder in reminders]

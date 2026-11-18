from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from practicv.adapters.db.repositories import (
    ApplicationRepository,
    OfferRepository,
    ProfileRepository,
)
from practicv.domain.entities import Application, utcnow
from practicv.domain.enums import ApplicationStatus
from practicv.domain.errors import NotFoundError


def create_application(
    session: Session,
    profile_id: UUID,
    offer_id: UUID,
    status: ApplicationStatus = ApplicationStatus.SAVED,
    applied_at: datetime | None = None,
    next_action_at: datetime | None = None,
    next_action_note: str | None = None,
    notes: str | None = None,
    cv_document_id: UUID | None = None,
) -> tuple[Application, bool]:
    if ProfileRepository(session).get(profile_id) is None:
        raise NotFoundError("Profile not found", {"profile_id": str(profile_id)})
    if OfferRepository(session).get(offer_id) is None:
        raise NotFoundError("Offer not found", {"offer_id": str(offer_id)})

    repo = ApplicationRepository(session)
    existing = repo.get_by_profile_offer(profile_id, offer_id)
    if existing is not None:
        return existing, True

    if status == ApplicationStatus.APPLIED and applied_at is None:
        applied_at = utcnow()
    application = Application(
        profile_id=profile_id,
        offer_id=offer_id,
        status=status,
        applied_at=applied_at,
        next_action_at=next_action_at,
        next_action_note=next_action_note,
        notes=notes,
        cv_document_id=cv_document_id,
    )
    created = repo.create(application)
    repo.add_event(
        created.id,
        "created",
        utcnow(),
        notes="Postulación creada desde PractiCV.",
    )
    return created, False

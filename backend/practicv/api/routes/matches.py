from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from practicv.adapters.db.repositories import MatchRepository, OfferRepository
from practicv.adapters.db.session import get_session
from practicv.api.schemas import (
    MatchOverrideRequest,
    MatchRequest,
    MatchResponse,
    MatchWithOfferResponse,
    OfferResponse,
)
from practicv.domain.errors import NotFoundError
from practicv.services.matching import compute_match

router = APIRouter(tags=["matches"])


@router.post("/matches", response_model=MatchResponse)
def create_match(
    payload: MatchRequest,
    session: Session = Depends(get_session),
) -> MatchResponse:
    match = compute_match(session, payload.profile_id, payload.offer_id)
    session.commit()
    return MatchResponse.model_validate(match)


@router.get("/matches/{match_id}", response_model=MatchResponse)
def get_match(
    match_id: UUID,
    session: Session = Depends(get_session),
) -> MatchResponse:
    match = MatchRepository(session).get(match_id)
    if match is None:
        raise NotFoundError("Match not found", {"match_id": str(match_id)})
    return MatchResponse.model_validate(match)


@router.patch("/matches/{match_id}", response_model=MatchResponse)
def override_match(
    match_id: UUID,
    payload: MatchOverrideRequest,
    session: Session = Depends(get_session),
) -> MatchResponse:
    match = MatchRepository(session).update_decision(
        match_id,
        payload.decision,
        payload.reason,
    )
    session.commit()
    return MatchResponse.model_validate(match)


@router.get("/profiles/{profile_id}/matches", response_model=list[MatchWithOfferResponse])
def list_profile_matches(
    profile_id: UUID,
    limit: int = 50,
    session: Session = Depends(get_session),
) -> list[MatchWithOfferResponse]:
    matches = MatchRepository(session).list_by_profile(profile_id, limit=limit)
    offer_repo = OfferRepository(session)
    results: list[MatchWithOfferResponse] = []
    for match in matches:
        offer = offer_repo.get(match.offer_id)
        if offer is None:
            continue
        results.append(
            MatchWithOfferResponse(
                match=MatchResponse.model_validate(match),
                offer=OfferResponse.model_validate(offer),
            )
        )
    return results

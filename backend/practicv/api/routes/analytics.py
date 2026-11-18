from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from practicv.adapters.db.repositories import AnalyticsRepository
from practicv.adapters.db.session import get_session

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/offer-ranking/{profile_id}")
def offer_ranking(
    profile_id: UUID,
    limit: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[dict]:
    return AnalyticsRepository(session).offer_ranking(profile_id, limit)


@router.get("/application-funnel/{profile_id}")
def application_funnel(
    profile_id: UUID,
    session: Session = Depends(get_session),
) -> list[dict]:
    return AnalyticsRepository(session).application_funnel(profile_id)


@router.get("/top-offers/{profile_id}")
def top_offers(
    profile_id: UUID,
    limit: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[dict]:
    return AnalyticsRepository(session).top_offers_via_function(profile_id, limit)

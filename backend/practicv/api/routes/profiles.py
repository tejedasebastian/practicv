from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from practicv.adapters.db.repositories import ProfileRepository
from practicv.adapters.db.session import get_session
from practicv.api.schemas import ProfileResponse
from practicv.domain.errors import NotFoundError

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: UUID,
    session: Session = Depends(get_session),
) -> ProfileResponse:
    profile = ProfileRepository(session).get(profile_id)
    if profile is None:
        raise NotFoundError("Profile not found", {"profile_id": str(profile_id)})
    return ProfileResponse.model_validate(profile)

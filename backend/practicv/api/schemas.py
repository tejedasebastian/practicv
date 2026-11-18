from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str | None
    phone: str | None
    university: str | None
    career: str | None
    cycle: int | None
    location: str | None
    target_roles: list[str]
    preferred_modality: str | None
    salary_expectation: float | None
    availability: str | None
    locale: str
    created_at: datetime
    updated_at: datetime

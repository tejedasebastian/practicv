from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProfileCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: str | None = None
    phone: str | None = None
    university: str | None = None
    career: str | None = None
    cycle: int | None = Field(default=None, ge=1, le=20)
    location: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    preferred_modality: str | None = None
    salary_expectation: float | None = Field(default=None, ge=0)
    availability: str | None = None
    locale: str = "es"


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    email: str | None = None
    phone: str | None = None
    university: str | None = None
    career: str | None = None
    cycle: int | None = Field(default=None, ge=1, le=20)
    location: str | None = None
    target_roles: list[str] | None = None
    preferred_modality: str | None = None
    salary_expectation: float | None = Field(default=None, ge=0)
    availability: str | None = None
    locale: str | None = None


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


class CVSkillResponse(BaseModel):
    skill_id: UUID
    canonical_name: str
    category: str
    level: int = 1
    evidence: str | None = None
    confidence: float | None = None
    confirmed: bool = False


class CVContact(BaseModel):
    email: str | None = None
    phone: str | None = None


class CVUploadResponse(BaseModel):
    cv_id: UUID
    filename: str
    mime_type: str
    raw_text: str
    sections: dict[str, str]
    skills: list[CVSkillResponse]
    contact: CVContact
    warnings: list[str]
    redacted_text: str


class ProfileSkillUpdateItem(BaseModel):
    skill_id: UUID
    level: int = Field(ge=0, le=3)
    evidence: str | None = None
    confirmed: bool = True


class ProfileSkillUpdate(BaseModel):
    skills: list[ProfileSkillUpdateItem]


class ProfileSkillListResponse(BaseModel):
    skills: list[CVSkillResponse]


class AnalyzeAIRequest(BaseModel):
    text: str = Field(min_length=20)
    consent: bool = False


class AnalyzeAIResponse(BaseModel):
    provider: str
    redacted_text: str
    pii_removed: bool
    suggestions: list[str]

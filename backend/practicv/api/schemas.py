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


class OfferCreate(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    company: str = Field(min_length=2, max_length=200)
    source_url: str | None = None
    external_id: str | None = None
    location: str | None = None
    modality: str | None = None
    salary_text: str | None = None
    salary_amount: float | None = Field(default=None, ge=0)
    salary_currency: str | None = None
    description: str | None = None
    requirements_text: str | None = None
    published_at: datetime | None = None
    deadline_at: datetime | None = None
    parse_confidence: float | None = None


class OfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_type: str
    external_id: str | None
    source_url: str | None
    captured_at: datetime
    title: str
    company: str
    location: str | None
    modality: str | None
    salary_text: str | None
    salary_amount: float | None
    salary_currency: str | None
    description: str | None
    requirements_text: str | None
    published_at: datetime | None
    deadline_at: datetime | None
    parse_confidence: float | None
    dedupe_hash: str | None


class OfferMutationResponse(BaseModel):
    offer: OfferResponse
    duplicate: bool


class OfferImportResponse(BaseModel):
    created: int
    duplicates: int
    errors: list[dict]
    warnings: list[str]
    total_rows: int
    preview: list[dict]
    offer_ids: list[str]


class UrlCaptureRequest(BaseModel):
    url: str = Field(min_length=5)


class MCPSearchRequest(BaseModel):
    q: str = ""
    modality: str = "preprofesional"
    career: str | None = None
    department: str | None = None
    order: str = "recientes"
    page: int = Field(default=1, ge=1)
    pages: int = Field(default=1, ge=1, le=5)
    limit: int = Field(default=30, ge=1, le=100)


class MCPSearchResponse(BaseModel):
    results: list[dict]
    total: int
    warning: str | None = None


class MCPImportRequest(BaseModel):
    urls: list[str] = Field(min_length=1, max_length=50)


class SourceStatusResponse(BaseModel):
    mcp: str
    detail: str | None = None
    filters: dict | None = None

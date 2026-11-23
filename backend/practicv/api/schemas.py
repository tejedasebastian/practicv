from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from practicv.domain.enums import (
    ApplicationStatus,
    MatchDecision,
    ReminderChannel,
    ReminderStatus,
)


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


class BookmarkletPreviewRequest(BaseModel):
    url: str = Field(min_length=5)
    title: str | None = Field(default=None, max_length=300)
    company: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    salary_text: str | None = Field(default=None, max_length=100)
    deadline_at: datetime | None = None
    published_at: datetime | None = None
    og_site_name: str | None = Field(default=None, max_length=200)
    jsonld: list[str] = Field(default_factory=list, max_length=20)
    text: str = Field(default="", max_length=50_000)


class BookmarkletPreviewResponse(BaseModel):
    title: str
    company: str
    source_url: str
    location: str | None
    modality: str | None
    salary_text: str | None
    salary_amount: float | None
    salary_currency: str | None
    description: str | None
    requirements_text: str | None
    published_at: datetime | None
    deadline_at: datetime | None
    confidence: float
    warnings: list[str]


class EmailCandidateResponse(BaseModel):
    url: str
    title: str
    source: str


class EmailPreviewResponse(BaseModel):
    subject: str
    candidates: list[EmailCandidateResponse]
    warnings: list[str]


class EmailImportRequest(BaseModel):
    urls: list[str] = Field(min_length=1, max_length=30)


class PractilizateStatusResponse(BaseModel):
    enabled: bool
    detail: str


class GoogleStatusResponse(BaseModel):
    configured: bool
    connected: bool
    email: str | None
    detail: str


class GoogleAuthorizeResponse(BaseModel):
    auth_url: str


class GmailMessageResponse(BaseModel):
    id: str
    subject: str
    sender: str
    date: str
    snippet: str


class GmailMessageListResponse(BaseModel):
    messages: list[GmailMessageResponse]
    warnings: list[str] = Field(default_factory=list)


class GmailMessageRequest(BaseModel):
    message_id: str = Field(min_length=1, max_length=200)


class GmailImportRequest(BaseModel):
    message_id: str = Field(min_length=1, max_length=200)
    urls: list[str] = Field(min_length=1, max_length=30)


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


class MatchRequest(BaseModel):
    profile_id: UUID
    offer_id: UUID


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    offer_id: UUID
    overall_score: float
    must_have_score: float
    confidence: float
    decision: MatchDecision
    gaps_json: list[dict]
    explanation_json: list[dict]
    overridden: bool
    override_reason: str | None
    created_at: datetime


class MatchWithOfferResponse(BaseModel):
    match: MatchResponse
    offer: OfferResponse


class MatchOverrideRequest(BaseModel):
    decision: MatchDecision
    reason: str | None = None


class ApplicationCreate(BaseModel):
    profile_id: UUID
    offer_id: UUID
    status: ApplicationStatus = ApplicationStatus.SAVED
    applied_at: datetime | None = None
    next_action_at: datetime | None = None
    next_action_note: str | None = None
    notes: str | None = None
    cv_document_id: UUID | None = None


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    next_action_at: datetime | None = None
    next_action_note: str | None = None
    notes: str | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    offer_id: UUID
    status: ApplicationStatus
    applied_at: datetime | None
    next_action_at: datetime | None
    next_action_note: str | None
    notes: str | None
    cv_document_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ApplicationWithOfferResponse(BaseModel):
    application: ApplicationResponse
    offer: OfferResponse
    match: MatchResponse | None = None


class ApplicationMutationResponse(BaseModel):
    application: ApplicationResponse
    duplicate: bool


class ApplicationEventCreate(BaseModel):
    event_type: str = Field(min_length=2, max_length=50)
    event_at: datetime
    notes: str | None = None


class ApplicationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    event_type: str
    event_at: datetime
    notes: str | None


class ReminderCreate(BaseModel):
    due_at: datetime
    channel: ReminderChannel = ReminderChannel.IN_APP
    message: str | None = None


class ReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    due_at: datetime
    channel: ReminderChannel
    message: str | None
    status: ReminderStatus

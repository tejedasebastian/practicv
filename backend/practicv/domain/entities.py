from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from practicv.domain.enums import (
    ApplicationStatus,
    MatchDecision,
    OfferLinkKind,
    ReminderChannel,
    ReminderStatus,
    RequirementType,
    SkillSource,
    SourceType,
)


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Profile:
    full_name: str
    email: str | None = None
    phone: str | None = None
    university: str | None = None
    career: str | None = None
    cycle: int | None = None
    location: str | None = None
    target_roles: list[str] = field(default_factory=list)
    preferred_modality: str | None = None
    salary_expectation: float | None = None
    availability: str | None = None
    locale: str = "es"
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class CVDocument:
    profile_id: UUID
    filename: str
    mime_type: str
    raw_text: str | None = None
    parsed_json: dict | None = None
    file_bytes: bytes | None = None
    is_active: bool = True
    id: UUID = field(default_factory=uuid4)
    uploaded_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Skill:
    canonical_name: str
    category: str
    aliases: list[str] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class ProfileSkill:
    profile_id: UUID
    skill_id: UUID
    level: int
    evidence: str | None = None
    source: SkillSource = SkillSource.MANUAL
    confirmed: bool = False


@dataclass(slots=True)
class Offer:
    title: str
    company: str
    source_type: SourceType = SourceType.MANUAL
    external_id: str | None = None
    source_url: str | None = None
    captured_at: datetime = field(default_factory=utcnow)
    location: str | None = None
    modality: str | None = None
    salary_text: str | None = None
    salary_amount: float | None = None
    salary_currency: str | None = None
    description: str | None = None
    requirements_text: str | None = None
    published_at: datetime | None = None
    deadline_at: datetime | None = None
    raw_text: str | None = None
    parse_confidence: float | None = None
    dedupe_hash: str | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class OfferSkill:
    offer_id: UUID
    skill_id: UUID
    requirement_type: RequirementType = RequirementType.UNKNOWN
    required_level: int = 2
    evidence_text: str | None = None
    confidence: float | None = None


@dataclass(slots=True)
class OfferLink:
    offer_id: UUID
    kind: OfferLinkKind
    label: str
    url: str
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class Match:
    profile_id: UUID
    offer_id: UUID
    overall_score: float
    must_have_score: float
    decision: MatchDecision
    gaps_json: list[dict] = field(default_factory=list)
    explanation_json: list[dict] = field(default_factory=list)
    overridden: bool = False
    override_reason: str | None = None
    confidence: float = 0.0
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Application:
    profile_id: UUID
    offer_id: UUID
    status: ApplicationStatus = ApplicationStatus.SAVED
    applied_at: datetime | None = None
    next_action_at: datetime | None = None
    next_action_note: str | None = None
    notes: str | None = None
    cv_document_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class ApplicationEvent:
    application_id: UUID
    event_type: str
    event_at: datetime = field(default_factory=utcnow)
    notes: str | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class Reminder:
    application_id: UUID
    due_at: datetime
    channel: ReminderChannel = ReminderChannel.IN_APP
    message: str | None = None
    status: ReminderStatus = ReminderStatus.PENDING
    id: UUID = field(default_factory=uuid4)

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from practicv.adapters.db.base import Base
from practicv.domain.entities import utcnow
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


def _enum(enum_type: type, name: str) -> SAEnum:
    return SAEnum(
        enum_type,
        name=name,
        native_enum=False,
        length=32,
        values_callable=lambda enum: [member.value for member in enum],
    )


class ProfileModel(Base):
    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    phone: Mapped[str | None] = mapped_column(String(40))
    university: Mapped[str | None] = mapped_column(String(200))
    career: Mapped[str | None] = mapped_column(String(200))
    cycle: Mapped[int | None] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(String(200))
    target_roles: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    preferred_modality: Mapped[str | None] = mapped_column(String(50))
    salary_expectation: Mapped[float | None] = mapped_column(Float)
    availability: Mapped[str | None] = mapped_column(String(100))
    locale: Mapped[str] = mapped_column(String(5), default="es", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint("cycle IS NULL OR cycle > 0", name="profiles_cycle_positive"),
    )


class CVDocumentModel(Base):
    __tablename__ = "cv_documents"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text)
    parsed_json: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (Index("ix_cv_documents_profile_active", "profile_id", "is_active"),)


class SkillModel(Base):
    __tablename__ = "skills"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    canonical_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)


class ProfileSkillModel(Base):
    __tablename__ = "profile_skills"

    profile_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)
    source: Mapped[SkillSource] = mapped_column(
        _enum(SkillSource, "skill_source_enum"),
        default=SkillSource.MANUAL,
        nullable=False,
    )
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (CheckConstraint("level BETWEEN 0 AND 3", name="profile_skills_level_range"),)


class OfferModel(Base):
    __tablename__ = "offers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source_type: Mapped[SourceType] = mapped_column(
        _enum(SourceType, "source_type_enum"),
        default=SourceType.MANUAL,
        nullable=False,
    )
    external_id: Mapped[str | None] = mapped_column(String(100))
    source_url: Mapped[str | None] = mapped_column(Text)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    modality: Mapped[str | None] = mapped_column(String(50))
    salary_text: Mapped[str | None] = mapped_column(String(100))
    salary_amount: Mapped[float | None] = mapped_column(Float)
    salary_currency: Mapped[str | None] = mapped_column(String(3))
    description: Mapped[str | None] = mapped_column(Text)
    requirements_text: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_text: Mapped[str | None] = mapped_column(Text)
    parse_confidence: Mapped[float | None] = mapped_column(Float)
    dedupe_hash: Mapped[str | None] = mapped_column(String(64), unique=True)

    __table_args__ = (
        CheckConstraint(
            "salary_amount IS NULL OR salary_amount >= 0",
            name="offers_salary_non_negative",
        ),
        Index("ix_offers_source_url", "source_url"),
        Index("ix_offers_deadline_at", "deadline_at"),
        Index("ix_offers_company", "company"),
        Index("ix_offers_source_type", "source_type"),
    )


class OfferSkillModel(Base):
    __tablename__ = "offer_skills"

    offer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("offers.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    requirement_type: Mapped[RequirementType] = mapped_column(
        _enum(RequirementType, "requirement_type_enum"),
        default=RequirementType.UNKNOWN,
        nullable=False,
    )
    required_level: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    evidence_text: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        CheckConstraint(
            "required_level BETWEEN 1 AND 3",
            name="offer_skills_required_level_range",
        ),
    )


class OfferLinkModel(Base):
    __tablename__ = "offer_links"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    offer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("offers.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[OfferLinkKind] = mapped_column(
        _enum(OfferLinkKind, "offer_link_kind_enum"),
        default=OfferLinkKind.OTHER,
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (Index("ix_offer_links_offer", "offer_id"),)


class MatchModel(Base):
    __tablename__ = "matches"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    offer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("offers.id", ondelete="CASCADE"), nullable=False
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    must_have_score: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[MatchDecision] = mapped_column(
        _enum(MatchDecision, "match_decision_enum"),
        nullable=False,
    )
    gaps_json: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    explanation_json: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "overall_score BETWEEN 0 AND 100",
            name="matches_overall_score_range",
        ),
        CheckConstraint(
            "must_have_score BETWEEN 0 AND 100",
            name="matches_must_have_score_range",
        ),
        Index("ix_matches_profile_score", "profile_id", "overall_score"),
        Index("ix_matches_offer", "offer_id"),
    )


class ApplicationModel(Base):
    __tablename__ = "applications"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    offer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("offers.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        _enum(ApplicationStatus, "application_status_enum"),
        default=ApplicationStatus.SAVED,
        nullable=False,
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_action_note: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    cv_document_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("cv_documents.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("profile_id", "offer_id", name="uq_applications_profile_offer"),
        Index("ix_applications_profile_status", "profile_id", "status"),
        Index("ix_applications_next_action", "next_action_at"),
    )


class ApplicationEventModel(Base):
    __tablename__ = "application_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_application_events_application", "application_id", "event_at"),)


class ReminderModel(Base):
    __tablename__ = "reminders"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    channel: Mapped[ReminderChannel] = mapped_column(
        _enum(ReminderChannel, "reminder_channel_enum"),
        default=ReminderChannel.IN_APP,
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ReminderStatus] = mapped_column(
        _enum(ReminderStatus, "reminder_status_enum"),
        default=ReminderStatus.PENDING,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_reminders_due_status", "due_at", "status"),
        Index("ix_reminders_application", "application_id"),
    )


class SourceConfigModel(Base):
    __tablename__ = "source_configs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source_type: Mapped[SourceType] = mapped_column(
        _enum(SourceType, "source_config_type_enum"),
        unique=True,
        nullable=False,
    )
    config_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

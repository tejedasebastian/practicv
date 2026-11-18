from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from practicv.adapters.db.models import (
    ApplicationEventModel,
    ApplicationModel,
    CVDocumentModel,
    MatchModel,
    OfferModel,
    OfferSkillModel,
    ProfileModel,
    ProfileSkillModel,
    ReminderModel,
    SkillModel,
)
from practicv.domain.entities import (
    Application,
    ApplicationEvent,
    CVDocument,
    Match,
    Offer,
    Profile,
    Reminder,
    Skill,
    utcnow,
)
from practicv.domain.enums import (
    ApplicationStatus,
    MatchDecision,
    ReminderStatus,
    RequirementType,
    SkillSource,
    SourceType,
)
from practicv.domain.errors import ConflictError, NotFoundError


def _profile(row: ProfileModel) -> Profile:
    return Profile(
        id=row.id,
        full_name=row.full_name,
        email=row.email,
        phone=row.phone,
        university=row.university,
        career=row.career,
        cycle=row.cycle,
        location=row.location,
        target_roles=list(row.target_roles or []),
        preferred_modality=row.preferred_modality,
        salary_expectation=row.salary_expectation,
        availability=row.availability,
        locale=row.locale,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _cv(row: CVDocumentModel) -> CVDocument:
    return CVDocument(
        id=row.id,
        profile_id=row.profile_id,
        filename=row.filename,
        mime_type=row.mime_type,
        raw_text=row.raw_text,
        parsed_json=row.parsed_json,
        file_bytes=row.file_bytes,
        is_active=row.is_active,
        uploaded_at=row.uploaded_at,
    )


def _skill(row: SkillModel) -> Skill:
    return Skill(
        id=row.id,
        canonical_name=row.canonical_name,
        category=row.category,
        aliases=list(row.aliases or []),
    )


def _offer(row: OfferModel) -> Offer:
    return Offer(
        id=row.id,
        source_type=row.source_type,
        external_id=row.external_id,
        source_url=row.source_url,
        captured_at=row.captured_at,
        title=row.title,
        company=row.company,
        location=row.location,
        modality=row.modality,
        salary_text=row.salary_text,
        salary_amount=row.salary_amount,
        salary_currency=row.salary_currency,
        description=row.description,
        requirements_text=row.requirements_text,
        published_at=row.published_at,
        deadline_at=row.deadline_at,
        raw_text=row.raw_text,
        parse_confidence=row.parse_confidence,
        dedupe_hash=row.dedupe_hash,
    )


def _match(row: MatchModel) -> Match:
    return Match(
        id=row.id,
        profile_id=row.profile_id,
        offer_id=row.offer_id,
        overall_score=row.overall_score,
        must_have_score=row.must_have_score,
        confidence=row.confidence,
        decision=row.decision,
        gaps_json=list(row.gaps_json or []),
        explanation_json=list(row.explanation_json or []),
        overridden=row.overridden,
        override_reason=row.override_reason,
        created_at=row.created_at,
    )


def _application(row: ApplicationModel) -> Application:
    return Application(
        id=row.id,
        profile_id=row.profile_id,
        offer_id=row.offer_id,
        status=row.status,
        applied_at=row.applied_at,
        next_action_at=row.next_action_at,
        next_action_note=row.next_action_note,
        notes=row.notes,
        cv_document_id=row.cv_document_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _reminder(row: ReminderModel) -> Reminder:
    return Reminder(
        id=row.id,
        application_id=row.application_id,
        due_at=row.due_at,
        channel=row.channel,
        message=row.message,
        status=row.status,
    )


def _event(row: ApplicationEventModel) -> ApplicationEvent:
    return ApplicationEvent(
        id=row.id,
        application_id=row.application_id,
        event_type=row.event_type,
        event_at=row.event_at,
        notes=row.notes,
    )


class ProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, profile: Profile) -> Profile:
        row = ProfileModel(
            full_name=profile.full_name,
            email=profile.email,
            phone=profile.phone,
            university=profile.university,
            career=profile.career,
            cycle=profile.cycle,
            location=profile.location,
            target_roles=profile.target_roles,
            preferred_modality=profile.preferred_modality,
            salary_expectation=profile.salary_expectation,
            availability=profile.availability,
            locale=profile.locale,
        )
        self.session.add(row)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError(
                "A profile with that email already exists",
                {"email": profile.email},
            ) from exc
        return _profile(row)

    def get(self, profile_id: UUID) -> Profile | None:
        row = self.session.get(ProfileModel, profile_id)
        return _profile(row) if row else None

    def get_by_email(self, email: str) -> Profile | None:
        row = self.session.scalar(select(ProfileModel).where(ProfileModel.email == email))
        return _profile(row) if row else None

    def list(self) -> list[Profile]:
        rows = self.session.scalars(select(ProfileModel).order_by(ProfileModel.full_name)).all()
        return [_profile(row) for row in rows]

    def update(self, profile_id: UUID, **fields: object) -> Profile:
        row = self.session.get(ProfileModel, profile_id)
        if row is None:
            raise NotFoundError("Profile not found", {"profile_id": str(profile_id)})
        for key, value in fields.items():
            if value is not None and hasattr(row, key):
                setattr(row, key, value)
        row.updated_at = utcnow()
        self.session.flush()
        return _profile(row)

    def delete(self, profile_id: UUID) -> None:
        row = self.session.get(ProfileModel, profile_id)
        if row is None:
            raise NotFoundError("Profile not found", {"profile_id": str(profile_id)})
        self.session.delete(row)
        self.session.flush()


class CVDocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, document: CVDocument) -> CVDocument:
        row = CVDocumentModel(
            profile_id=document.profile_id,
            filename=document.filename,
            mime_type=document.mime_type,
            raw_text=document.raw_text,
            parsed_json=document.parsed_json,
            file_bytes=document.file_bytes,
            is_active=document.is_active,
        )
        self.session.add(row)
        self.session.flush()
        return _cv(row)

    def deactivate_all(self, profile_id: UUID) -> None:
        rows = self.session.scalars(
            select(CVDocumentModel).where(
                CVDocumentModel.profile_id == profile_id,
                CVDocumentModel.is_active.is_(True),
            )
        ).all()
        for row in rows:
            row.is_active = False
        self.session.flush()

    def get_active(self, profile_id: UUID) -> CVDocument | None:
        row = self.session.scalar(
            select(CVDocumentModel)
            .where(
                CVDocumentModel.profile_id == profile_id,
                CVDocumentModel.is_active.is_(True),
            )
            .order_by(CVDocumentModel.uploaded_at.desc())
        )
        return _cv(row) if row else None


class SkillRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, skill: Skill) -> Skill:
        row = SkillModel(
            canonical_name=skill.canonical_name,
            category=skill.category,
            aliases=skill.aliases,
        )
        self.session.add(row)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError(
                "A skill with that canonical name already exists",
                {"canonical_name": skill.canonical_name},
            ) from exc
        return _skill(row)

    def get(self, skill_id: UUID) -> Skill | None:
        row = self.session.get(SkillModel, skill_id)
        return _skill(row) if row else None

    def get_by_canonical_name(self, canonical_name: str) -> Skill | None:
        row = self.session.scalar(
            select(SkillModel).where(SkillModel.canonical_name == canonical_name)
        )
        return _skill(row) if row else None

    def list(self) -> list[Skill]:
        rows = self.session.scalars(select(SkillModel).order_by(SkillModel.canonical_name)).all()
        return [_skill(row) for row in rows]


class ProfileSkillRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def replace_for_profile(
        self,
        profile_id: UUID,
        items: list[tuple[UUID, int, str | None, bool]],
    ) -> list[dict]:
        self.session.execute(
            delete(ProfileSkillModel).where(ProfileSkillModel.profile_id == profile_id)
        )
        for skill_id, level, evidence, confirmed in items:
            self.session.add(
                ProfileSkillModel(
                    profile_id=profile_id,
                    skill_id=skill_id,
                    level=level,
                    evidence=evidence,
                    source=SkillSource.CV,
                    confirmed=confirmed,
                )
            )
        self.session.flush()
        return self.list_for_profile(profile_id)

    def list_for_profile(self, profile_id: UUID) -> list[dict]:
        rows = self.session.execute(
            select(ProfileSkillModel, SkillModel)
            .join(SkillModel, SkillModel.id == ProfileSkillModel.skill_id)
            .where(ProfileSkillModel.profile_id == profile_id)
            .order_by(SkillModel.canonical_name)
        ).all()
        return [
            {
                "skill_id": profile_skill.skill_id,
                "canonical_name": skill.canonical_name,
                "category": skill.category,
                "level": profile_skill.level,
                "evidence": profile_skill.evidence,
                "confirmed": profile_skill.confirmed,
            }
            for profile_skill, skill in rows
        ]


class OfferSkillRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def replace_for_offer(
        self,
        offer_id: UUID,
        items: list[tuple[UUID, RequirementType, int, str | None, float | None]],
    ) -> list[dict]:
        self.session.execute(delete(OfferSkillModel).where(OfferSkillModel.offer_id == offer_id))
        for skill_id, requirement_type, required_level, evidence, confidence in items:
            self.session.add(
                OfferSkillModel(
                    offer_id=offer_id,
                    skill_id=skill_id,
                    requirement_type=requirement_type,
                    required_level=required_level,
                    evidence_text=evidence,
                    confidence=confidence,
                )
            )
        self.session.flush()
        return self.list_for_offer(offer_id)

    def list_for_offer(self, offer_id: UUID) -> list[dict]:
        rows = self.session.execute(
            select(OfferSkillModel, SkillModel)
            .join(SkillModel, SkillModel.id == OfferSkillModel.skill_id)
            .where(OfferSkillModel.offer_id == offer_id)
            .order_by(SkillModel.canonical_name)
        ).all()
        return [
            {
                "skill_id": offer_skill.skill_id,
                "canonical_name": skill.canonical_name,
                "category": skill.category,
                "requirement_type": offer_skill.requirement_type,
                "required_level": offer_skill.required_level,
                "evidence_text": offer_skill.evidence_text,
                "confidence": offer_skill.confidence,
            }
            for offer_skill, skill in rows
        ]


class OfferRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, offer: Offer) -> Offer:
        row = OfferModel(
            source_type=offer.source_type,
            external_id=offer.external_id,
            source_url=offer.source_url,
            captured_at=offer.captured_at,
            title=offer.title,
            company=offer.company,
            location=offer.location,
            modality=offer.modality,
            salary_text=offer.salary_text,
            salary_amount=offer.salary_amount,
            salary_currency=offer.salary_currency,
            description=offer.description,
            requirements_text=offer.requirements_text,
            published_at=offer.published_at,
            deadline_at=offer.deadline_at,
            raw_text=offer.raw_text,
            parse_confidence=offer.parse_confidence,
            dedupe_hash=offer.dedupe_hash,
        )
        self.session.add(row)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError(
                "An offer with that dedupe hash already exists",
                {"dedupe_hash": offer.dedupe_hash},
            ) from exc
        return _offer(row)

    def get(self, offer_id: UUID) -> Offer | None:
        row = self.session.get(OfferModel, offer_id)
        return _offer(row) if row else None

    def get_by_dedupe_hash(self, dedupe_hash: str) -> Offer | None:
        row = self.session.scalar(select(OfferModel).where(OfferModel.dedupe_hash == dedupe_hash))
        return _offer(row) if row else None

    def list(self, limit: int = 50, source_type: SourceType | None = None) -> list[Offer]:
        statement = select(OfferModel).order_by(OfferModel.captured_at.desc()).limit(limit)
        if source_type is not None:
            statement = statement.where(OfferModel.source_type == source_type)
        rows = self.session.scalars(statement).all()
        return [_offer(row) for row in rows]

    def count(self) -> int:
        return int(self.session.scalar(select(func.count()).select_from(OfferModel)) or 0)


class MatchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, match: Match) -> Match:
        row = MatchModel(
            profile_id=match.profile_id,
            offer_id=match.offer_id,
            overall_score=match.overall_score,
            must_have_score=match.must_have_score,
            confidence=match.confidence,
            decision=match.decision,
            gaps_json=match.gaps_json,
            explanation_json=match.explanation_json,
            overridden=match.overridden,
            override_reason=match.override_reason,
        )
        self.session.add(row)
        self.session.flush()
        return _match(row)

    def get(self, match_id: UUID) -> Match | None:
        row = self.session.get(MatchModel, match_id)
        return _match(row) if row else None

    def list_by_profile(self, profile_id: UUID, limit: int = 50) -> list[Match]:
        rows = self.session.scalars(
            select(MatchModel)
            .where(MatchModel.profile_id == profile_id)
            .order_by(MatchModel.created_at.desc())
            .limit(limit)
        ).all()
        return [_match(row) for row in rows]

    def get_latest(self, profile_id: UUID, offer_id: UUID) -> Match | None:
        row = self.session.scalar(
            select(MatchModel)
            .where(
                MatchModel.profile_id == profile_id,
                MatchModel.offer_id == offer_id,
            )
            .order_by(MatchModel.created_at.desc())
            .limit(1)
        )
        return _match(row) if row else None

    def update_decision(
        self,
        match_id: UUID,
        decision: MatchDecision,
        reason: str | None,
    ) -> Match:
        row = self.session.get(MatchModel, match_id)
        if row is None:
            raise NotFoundError("Match not found", {"match_id": str(match_id)})
        row.decision = decision
        row.overridden = True
        row.override_reason = reason
        self.session.flush()
        return _match(row)


class ApplicationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, application: Application) -> Application:
        row = ApplicationModel(
            profile_id=application.profile_id,
            offer_id=application.offer_id,
            status=application.status,
            applied_at=application.applied_at,
            next_action_at=application.next_action_at,
            next_action_note=application.next_action_note,
            notes=application.notes,
            cv_document_id=application.cv_document_id,
        )
        self.session.add(row)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError(
                "This offer is already tracked for that profile",
                {"profile_id": str(application.profile_id), "offer_id": str(application.offer_id)},
            ) from exc
        return _application(row)

    def get_by_profile_offer(
        self,
        profile_id: UUID,
        offer_id: UUID,
    ) -> Application | None:
        row = self.session.scalar(
            select(ApplicationModel).where(
                ApplicationModel.profile_id == profile_id,
                ApplicationModel.offer_id == offer_id,
            )
        )
        return _application(row) if row else None

    def get(self, application_id: UUID) -> Application | None:
        row = self.session.get(ApplicationModel, application_id)
        return _application(row) if row else None

    def list_by_profile(self, profile_id: UUID) -> list[Application]:
        rows = self.session.scalars(
            select(ApplicationModel)
            .where(ApplicationModel.profile_id == profile_id)
            .order_by(ApplicationModel.updated_at.desc())
        ).all()
        return [_application(row) for row in rows]

    def update(
        self,
        application_id: UUID,
        status: ApplicationStatus | None = None,
        next_action_at: datetime | None = None,
        next_action_note: str | None = None,
        notes: str | None = None,
    ) -> Application:
        row = self.session.get(ApplicationModel, application_id)
        if row is None:
            raise NotFoundError("Application not found", {"application_id": str(application_id)})
        if status is not None:
            row.status = status
            if (
                status
                in (
                    ApplicationStatus.APPLIED,
                    ApplicationStatus.INTERVIEW,
                    ApplicationStatus.OFFER,
                )
                and row.applied_at is None
            ):
                row.applied_at = utcnow()
        if next_action_at is not None:
            row.next_action_at = next_action_at
        if next_action_note is not None:
            row.next_action_note = next_action_note
        if notes is not None:
            row.notes = notes
        row.updated_at = utcnow()
        self.session.flush()
        return _application(row)

    def add_event(
        self,
        application_id: UUID,
        event_type: str,
        event_at: datetime,
        notes: str | None = None,
    ) -> ApplicationEvent:
        row = ApplicationEventModel(
            application_id=application_id,
            event_type=event_type,
            event_at=event_at,
            notes=notes,
        )
        self.session.add(row)
        self.session.flush()
        return _event(row)

    def list_events(self, application_id: UUID) -> list[ApplicationEvent]:
        rows = self.session.scalars(
            select(ApplicationEventModel)
            .where(ApplicationEventModel.application_id == application_id)
            .order_by(ApplicationEventModel.event_at.desc())
        ).all()
        return [_event(row) for row in rows]

    def list_events_by_profile(self, profile_id: UUID) -> list[ApplicationEvent]:
        rows = self.session.scalars(
            select(ApplicationEventModel)
            .join(
                ApplicationModel,
                ApplicationModel.id == ApplicationEventModel.application_id,
            )
            .where(ApplicationModel.profile_id == profile_id)
            .order_by(ApplicationEventModel.event_at.desc())
        ).all()
        return [_event(row) for row in rows]

    def update_status(
        self,
        application_id: UUID,
        status: ApplicationStatus,
        next_action_at: datetime | None = None,
        next_action_note: str | None = None,
    ) -> Application:
        row = self.session.get(ApplicationModel, application_id)
        if row is None:
            raise NotFoundError("Application not found", {"application_id": str(application_id)})
        row.status = status
        row.updated_at = utcnow()
        if (
            status
            in (
                ApplicationStatus.APPLIED,
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.OFFER,
            )
            and row.applied_at is None
        ):
            row.applied_at = utcnow()
        if next_action_at is not None:
            row.next_action_at = next_action_at
        if next_action_note is not None:
            row.next_action_note = next_action_note
        self.session.flush()
        return _application(row)


class ReminderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, reminder: Reminder) -> Reminder:
        row = ReminderModel(
            application_id=reminder.application_id,
            due_at=reminder.due_at,
            channel=reminder.channel,
            message=reminder.message,
            status=reminder.status,
        )
        self.session.add(row)
        self.session.flush()
        return _reminder(row)

    def list_pending(self, limit: int = 50) -> list[Reminder]:
        rows = self.session.scalars(
            select(ReminderModel)
            .where(ReminderModel.status == ReminderStatus.PENDING)
            .order_by(ReminderModel.due_at.asc())
            .limit(limit)
        ).all()
        return [_reminder(row) for row in rows]

    def list_by_application(self, application_id: UUID) -> list[Reminder]:
        rows = self.session.scalars(
            select(ReminderModel)
            .where(ReminderModel.application_id == application_id)
            .order_by(ReminderModel.due_at.asc())
        ).all()
        return [_reminder(row) for row in rows]

    def list_by_profile(self, profile_id: UUID) -> list[Reminder]:
        rows = self.session.scalars(
            select(ReminderModel)
            .join(
                ApplicationModel,
                ApplicationModel.id == ReminderModel.application_id,
            )
            .where(ApplicationModel.profile_id == profile_id)
            .order_by(ReminderModel.due_at.asc())
        ).all()
        return [_reminder(row) for row in rows]

    def mark_done(self, reminder_id: UUID) -> Reminder:
        row = self.session.get(ReminderModel, reminder_id)
        if row is None:
            raise NotFoundError("Reminder not found", {"reminder_id": str(reminder_id)})
        row.status = ReminderStatus.DONE
        self.session.flush()
        return _reminder(row)


class AnalyticsRepository:
    """Read-only analytical queries written in SQL, not ORM."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def offer_ranking(self, profile_id: UUID, limit: int = 10) -> list[dict]:
        query = text(
            """
            WITH scored AS (
                SELECT
                    o.id AS offer_id,
                    o.title,
                    o.company,
                    o.deadline_at,
                    m.overall_score,
                    m.must_have_score,
                    ROW_NUMBER() OVER (
                        ORDER BY m.overall_score DESC, o.deadline_at ASC NULLS LAST
                    ) AS rank
                FROM offers o
                JOIN matches m ON m.offer_id = o.id
                WHERE m.profile_id = :profile_id
            )
            SELECT offer_id, title, company, deadline_at, overall_score, must_have_score, rank
            FROM scored
            WHERE rank <= :limit
            ORDER BY rank
            """
        )
        rows = self.session.execute(query, {"profile_id": profile_id, "limit": limit}).mappings()
        return [dict(row) for row in rows]

    def application_funnel(self, profile_id: UUID) -> list[dict]:
        query = text(
            """
            SELECT status, COUNT(*) AS total
            FROM applications
            WHERE profile_id = :profile_id
            GROUP BY status
            ORDER BY status
            """
        )
        rows = self.session.execute(query, {"profile_id": profile_id}).mappings()
        return [dict(row) for row in rows]

    def top_offers_via_function(self, profile_id: UUID, limit: int = 10) -> list[dict]:
        query = text(
            """
            SELECT offer_id, title, company, overall_score, must_have_score, decision
            FROM fn_top_offers_for_profile(:profile_id)
            LIMIT :limit
            """
        )
        rows = self.session.execute(query, {"profile_id": profile_id, "limit": limit}).mappings()
        return [dict(row) for row in rows]

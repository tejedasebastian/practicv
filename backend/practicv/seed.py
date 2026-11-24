from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.orm import Session

from practicv.adapters.db.models import (
    ApplicationEventModel,
    MatchModel,
    OfferModel,
    ProfileModel,
    ProfileSkillModel,
)
from practicv.adapters.db.repositories import (
    ApplicationRepository,
    CVDocumentRepository,
    MatchRepository,
    OfferRepository,
    ProfileRepository,
    ReminderRepository,
    SkillRepository,
)
from practicv.domain.entities import (
    Application,
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
    ReminderChannel,
    SkillSource,
    SourceType,
)
from practicv.services.matching import sync_offer_skills

DEMO_EMAIL = "demo@practicv.local"
DEMO_HASH_PREFIX = "demo-"


@dataclass(slots=True)
class SeedResult:
    profile_id: UUID
    offer_ids: list[UUID]
    application_ids: list[UUID]
    offers_total: int
    matches_total: int
    applications_total: int
    reminders_total: int


def _get_or_create_skills(session: Session, skill_repo: SkillRepository) -> dict[str, Skill]:
    definitions = [
        ("Python", "programming", ["python", "py"]),
        ("SQL", "data", ["sql", "postgresql", "postgres", "mysql"]),
        ("Power BI", "bi", ["power bi", "powerbi", "pbi"]),
        ("Excel", "office", ["excel", "hojas de calculo", "spreadsheets"]),
        ("FastAPI", "backend", ["fastapi", "fast api"]),
        ("Docker", "devops", ["docker", "containers"]),
    ]
    existing = {skill.canonical_name: skill for skill in skill_repo.list()}
    for name, category, aliases in definitions:
        if name not in existing:
            existing[name] = skill_repo.create(
                Skill(canonical_name=name, category=category, aliases=aliases)
            )
    return existing


def _clear_demo_data(session: Session) -> None:
    session.execute(delete(ProfileModel).where(ProfileModel.email == DEMO_EMAIL))
    session.execute(delete(OfferModel).where(OfferModel.dedupe_hash.like(f"{DEMO_HASH_PREFIX}%")))
    session.flush()


def seed_demo(session: Session, volume: int = 1000) -> SeedResult:
    """Create deterministic synthetic data. No real PII is used."""
    _clear_demo_data(session)

    profile_repo = ProfileRepository(session)
    cv_repo = CVDocumentRepository(session)
    skill_repo = SkillRepository(session)
    offer_repo = OfferRepository(session)
    match_repo = MatchRepository(session)
    application_repo = ApplicationRepository(session)
    reminder_repo = ReminderRepository(session)

    now = utcnow()

    profile = profile_repo.create(
        Profile(
            full_name="Estudiante Demo",
            email=DEMO_EMAIL,
            university="Universidad Demo",
            career="Ingeniería de Software",
            cycle=8,
            location="Lima",
            target_roles=["Data Analyst", "BI Analyst", "Backend Developer"],
            preferred_modality="Híbrido",
            salary_expectation=1200,
            availability="Lunes a viernes",
            locale="es",
        )
    )

    cv_repo.create(
        CVDocument(
            profile_id=profile.id,
            filename="cv-demo.pdf",
            mime_type="application/pdf",
            raw_text=(
                "Estudiante de Ingeniería de Software con experiencia en Python, SQL, "
                "Power BI, Excel y FastAPI. Proyectos académicos de análisis de datos."
            ),
            parsed_json={
                "skills": ["Python", "SQL", "Power BI", "Excel", "FastAPI"],
                "education": "Universidad Demo",
            },
        )
    )

    skills = _get_or_create_skills(session, skill_repo)
    session.add_all(
        [
            ProfileSkillModel(
                profile_id=profile.id,
                skill_id=skills["Python"].id,
                level=3,
                evidence="Proyectos con FastAPI y análisis de datos",
                source=SkillSource.CV,
                confirmed=True,
            ),
            ProfileSkillModel(
                profile_id=profile.id,
                skill_id=skills["SQL"].id,
                level=3,
                evidence="PostgreSQL y consultas analíticas",
                source=SkillSource.CV,
                confirmed=True,
            ),
            ProfileSkillModel(
                profile_id=profile.id,
                skill_id=skills["Power BI"].id,
                level=2,
                evidence="Dashboard de prácticas",
                source=SkillSource.CV,
                confirmed=True,
            ),
            ProfileSkillModel(
                profile_id=profile.id,
                skill_id=skills["Excel"].id,
                level=3,
                evidence="Tablas dinámicas y BUSCARX",
                source=SkillSource.CV,
                confirmed=True,
            ),
            ProfileSkillModel(
                profile_id=profile.id,
                skill_id=skills["FastAPI"].id,
                level=2,
                evidence="Proyecto Bustoke",
                source=SkillSource.CV,
                confirmed=True,
            ),
            ProfileSkillModel(
                profile_id=profile.id,
                skill_id=skills["Docker"].id,
                level=1,
                evidence="Uso básico en laboratorios",
                source=SkillSource.CV,
                confirmed=True,
            ),
        ]
    )
    session.flush()

    offer_specs = [
        {
            "title": "Practicante de Data Analytics",
            "company": "Banco Andino",
            "salary": 1400,
            "days": 6,
            "description": "Análisis de datos para el área de riesgos.",
            "requirements": "SQL intermedio, Power BI intermedio, Excel intermedio.",
            "score": 88.0,
            "must": 92.0,
            "decision": MatchDecision.APPLY,
            "gaps": [],
        },
        {
            "title": "Practicante de Ingeniería de Datos",
            "company": "Retail Perú",
            "salary": 1600,
            "days": 9,
            "description": "Construcción de pipelines y modelos de datos.",
            "requirements": "Python intermedio, SQL intermedio, Docker deseable.",
            "score": 76.0,
            "must": 84.0,
            "decision": MatchDecision.APPLY_WITH_GAPS,
            "gaps": [{"skill": "Docker", "required_level": 2, "user_level": 1}],
        },
        {
            "title": "Practicante de BI",
            "company": "Seguros Lima",
            "salary": 1200,
            "days": 12,
            "description": "Dashboards y reportes para comité comercial.",
            "requirements": "Power BI intermedio, SQL básico, Excel deseable.",
            "score": 92.0,
            "must": 95.0,
            "decision": MatchDecision.APPLY,
            "gaps": [],
        },
        {
            "title": "Practicante Backend",
            "company": "Fintech Pacífico",
            "salary": 1800,
            "days": 4,
            "description": "APIs para productos de pagos.",
            "requirements": "Python intermedio, FastAPI intermedio, SQL deseable.",
            "score": 80.0,
            "must": 88.0,
            "decision": MatchDecision.APPLY_WITH_GAPS,
            "gaps": [{"skill": "FastAPI avanzado", "required_level": 3, "user_level": 2}],
        },
        {
            "title": "Practicante de Datos",
            "company": "Municipalidad de Lima",
            "salary": 1100,
            "days": 15,
            "description": "Apoyo en indicadores de gestión municipal.",
            "requirements": "Excel intermedio, SQL deseable.",
            "score": 95.0,
            "must": 100.0,
            "decision": MatchDecision.APPLY,
            "gaps": [],
        },
    ]

    offers: list[Offer] = []
    for index, spec in enumerate(offer_specs, start=1):
        offer = offer_repo.create(
            Offer(
                title=spec["title"],
                company=spec["company"],
                source_type=SourceType.MANUAL,
                source_url=f"https://example.com/ofertas/demo-{index}",
                location="Lima",
                modality="Híbrido",
                salary_text=f"S/ {spec['salary']}",
                salary_amount=float(spec["salary"]),
                salary_currency="PEN",
                description=spec["description"],
                requirements_text=spec["requirements"],
                published_at=now - timedelta(days=2),
                deadline_at=now + timedelta(days=int(spec["days"])),
                parse_confidence=0.95,
                dedupe_hash=f"{DEMO_HASH_PREFIX}main-{index}",
            )
        )
        offers.append(offer)
        sync_offer_skills(session, offer)
        match_repo.create(
            Match(
                profile_id=profile.id,
                offer_id=offer.id,
                overall_score=float(spec["score"]),
                must_have_score=float(spec["must"]),
                decision=spec["decision"],
                gaps_json=list(spec["gaps"]),
                explanation_json=[
                    {"summary": "Match calculado sobre requisitos sintéticos de demo."},
                ],
            )
        )

    applications: list[Application] = []
    for index, status in enumerate(
        [ApplicationStatus.APPLIED, ApplicationStatus.INTERVIEW, ApplicationStatus.SAVED],
        start=1,
    ):
        application = application_repo.create(
            Application(
                profile_id=profile.id,
                offer_id=offers[index - 1].id,
                status=status,
                applied_at=now - timedelta(days=1) if status != ApplicationStatus.SAVED else None,
                next_action_at=now + timedelta(days=index + 1),
                next_action_note="Revisar requisitos y preparar CV adaptado.",
                notes="Postulación de demo.",
            )
        )
        applications.append(application)

    session.add(
        ApplicationEventModel(
            application_id=applications[0].id,
            event_type="applied",
            event_at=now - timedelta(days=1),
            notes="Postulación enviada en la demo.",
        )
    )

    reminder_repo.create(
        Reminder(
            application_id=applications[0].id,
            due_at=now + timedelta(days=3),
            channel=ReminderChannel.IN_APP,
            message="Hacer seguimiento a Banco Andino.",
        )
    )
    reminder_repo.create(
        Reminder(
            application_id=applications[1].id,
            due_at=now + timedelta(days=5),
            channel=ReminderChannel.ICS,
            message="Preparar entrevista en Retail Perú.",
        )
    )

    if volume > 0:
        bulk_matches_total = 0
        for batch_start in range(0, volume, 250):
            batch = []
            for index in range(batch_start, min(batch_start + 250, volume)):
                batch.append(
                    OfferModel(
                        source_type=SourceType.CSV,
                        title=f"Oferta demo {index:04d}",
                        company=f"Empresa Demo {index % 50:02d}",
                        location="Lima",
                        modality="Híbrido" if index % 2 == 0 else "Presencial",
                        salary_text=f"S/ {1000 + (index % 10) * 100}",
                        salary_amount=float(1000 + (index % 10) * 100),
                        salary_currency="PEN",
                        description="Oferta sintética para probar volumen.",
                        requirements_text="Python, SQL, Excel.",
                        published_at=now - timedelta(days=index % 10),
                        deadline_at=now + timedelta(days=(index % 30) + 1),
                        parse_confidence=0.8,
                        dedupe_hash=f"{DEMO_HASH_PREFIX}bulk-{index:04d}",
                    )
                )
            session.add_all(batch)
            session.flush()

            bulk_matches = [
                MatchModel(
                    profile_id=profile.id,
                    offer_id=model.id,
                    overall_score=float(50 + (index % 50)),
                    must_have_score=float(55 + (index % 40)),
                    decision=MatchDecision.APPLY_WITH_GAPS,
                    gaps_json=[{"skill": "Docker", "required_level": 2, "user_level": 1}],
                    explanation_json=[{"summary": "Match sintético de volumen."}],
                )
                for index, model in enumerate(batch, start=batch_start)
                if index < 500
            ]
            if bulk_matches:
                session.add_all(bulk_matches)
                session.flush()
                bulk_matches_total += len(bulk_matches)
    else:
        bulk_matches_total = 0

    session.flush()
    return SeedResult(
        profile_id=profile.id,
        offer_ids=[offer.id for offer in offers],
        application_ids=[application.id for application in applications],
        offers_total=len(offers) + volume,
        matches_total=len(offers) + bulk_matches_total,
        applications_total=len(applications),
        reminders_total=2,
    )

from __future__ import annotations

import csv
import io
from datetime import datetime
from uuid import UUID

from ics import Calendar, Event
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session

from practicv.adapters.db.repositories import (
    ApplicationRepository,
    MatchRepository,
    OfferRepository,
    ProfileRepository,
    ProfileSkillRepository,
    ReminderRepository,
)
from practicv.domain.entities import Application, Match, Offer
from practicv.domain.enums import MatchDecision
from practicv.domain.errors import NotFoundError


def _profile_or_404(session: Session, profile_id: UUID):
    profile = ProfileRepository(session).get(profile_id)
    if profile is None:
        raise NotFoundError("Profile not found", {"profile_id": str(profile_id)})
    return profile


def _application_rows(
    session: Session,
    profile_id: UUID,
) -> list[tuple[Application, Offer, Match | None]]:
    applications = ApplicationRepository(session).list_by_profile(profile_id)
    offer_repo = OfferRepository(session)
    matches = MatchRepository(session).list_by_profile(profile_id)
    latest_matches: dict[UUID, Match] = {}
    for match in matches:
        latest_matches.setdefault(match.offer_id, match)
    rows: list[tuple[Application, Offer, Match | None]] = []
    for application in applications:
        offer = offer_repo.get(application.offer_id)
        if offer is None:
            continue
        rows.append((application, offer, latest_matches.get(offer.id)))
    return rows


def _decision_label(decision: MatchDecision | None) -> str:
    if decision is None:
        return ""
    return {
        MatchDecision.APPLY: "Aplicar",
        MatchDecision.APPLY_WITH_GAPS: "Aplicar con brechas",
        MatchDecision.IMPROVE_CV: "Preparar CV",
    }.get(decision, decision.value)


def build_applications_workbook(session: Session, profile_id: UUID) -> bytes:
    _profile_or_404(session, profile_id)
    rows = _application_rows(session, profile_id)
    events = ApplicationRepository(session).list_events_by_profile(profile_id)
    reminders = ReminderRepository(session).list_by_profile(profile_id)
    offers = OfferRepository(session).list(limit=500)
    profile_skills = ProfileSkillRepository(session).list_for_profile(profile_id)

    workbook = Workbook()
    header_fill = PatternFill("solid", fgColor="14532D")
    header_font = Font(color="FFFFFF", bold=True)

    def prepare(sheet, headers: list[str]) -> None:
        sheet.append(headers)
        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
        sheet.freeze_panes = "A2"
        for index, header in enumerate(headers, start=1):
            sheet.column_dimensions[get_column_letter(index)].width = max(16, len(header) + 4)

    sheet = workbook.active
    sheet.title = "Postulaciones"
    prepare(
        sheet,
        [
            "Empresa",
            "Puesto",
            "Estado",
            "Match",
            "Must-have",
            "Decisión",
            "Postulada",
            "Próxima acción",
            "Nota",
        ],
    )
    for application, offer, match in rows:
        sheet.append(
            [
                offer.company,
                offer.title,
                application.status.value,
                match.overall_score if match else None,
                match.must_have_score if match else None,
                _decision_label(match.decision if match else None),
                application.applied_at.isoformat() if application.applied_at else "",
                application.next_action_at.isoformat() if application.next_action_at else "",
                application.next_action_note or application.notes or "",
            ]
        )

    offers_sheet = workbook.create_sheet("Ofertas")
    prepare(
        offers_sheet,
        [
            "Título",
            "Empresa",
            "Ubicación",
            "Modalidad",
            "Sueldo",
            "Moneda",
            "Vence",
            "Fuente",
            "URL",
        ],
    )
    for offer in offers:
        offers_sheet.append(
            [
                offer.title,
                offer.company,
                offer.location or "",
                offer.modality or "",
                offer.salary_amount,
                offer.salary_currency or "",
                offer.deadline_at.isoformat() if offer.deadline_at else "",
                offer.source_type.value,
                offer.source_url or "",
            ]
        )

    matches_sheet = workbook.create_sheet("Matches")
    prepare(matches_sheet, ["Oferta", "Overall", "Must-have", "Decisión", "Override", "Razón"])
    for _application, offer, match in rows:
        if match is None:
            continue
        matches_sheet.append(
            [
                f"{offer.company} · {offer.title}",
                match.overall_score,
                match.must_have_score,
                _decision_label(match.decision),
                "Sí" if match.overridden else "No",
                match.override_reason or "",
            ]
        )

    gaps_sheet = workbook.create_sheet("Brechas")
    prepare(
        gaps_sheet,
        ["Oferta", "Habilidad", "Tipo", "Nivel requerido", "Nivel usuario", "Sugerencia"],
    )
    for _application, offer, match in rows:
        if match is None:
            continue
        for gap in match.gaps_json:
            gaps_sheet.append(
                [
                    f"{offer.company} · {offer.title}",
                    gap.get("skill", ""),
                    gap.get("requirement_type", ""),
                    gap.get("required_level", ""),
                    gap.get("user_level", ""),
                    gap.get("suggestion", ""),
                ]
            )

    timeline_sheet = workbook.create_sheet("Timeline")
    prepare(timeline_sheet, ["Aplicación", "Evento", "Fecha", "Notas"])
    for event in events:
        timeline_sheet.append(
            [
                str(event.application_id),
                event.event_type,
                event.event_at.isoformat(),
                event.notes or "",
            ]
        )
    for reminder in reminders:
        timeline_sheet.append(
            [
                str(reminder.application_id),
                "reminder",
                reminder.due_at.isoformat(),
                reminder.message or "",
            ]
        )

    skills_sheet = workbook.create_sheet("Habilidades")
    prepare(skills_sheet, ["Habilidad", "Categoría", "Nivel", "Confirmada", "Evidencia"])
    for skill in profile_skills:
        skills_sheet.append(
            [
                skill["canonical_name"],
                skill["category"],
                skill["level"],
                "Sí" if skill["confirmed"] else "No",
                skill.get("evidence") or "",
            ]
        )

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def build_applications_csv(session: Session, profile_id: UUID) -> str:
    _profile_or_404(session, profile_id)
    rows = _application_rows(session, profile_id)
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        [
            "empresa",
            "puesto",
            "estado",
            "match",
            "must_have",
            "decision",
            "postulada",
            "proxima_accion",
            "nota",
        ]
    )
    for application, offer, match in rows:
        writer.writerow(
            [
                offer.company,
                offer.title,
                application.status.value,
                match.overall_score if match else "",
                match.must_have_score if match else "",
                _decision_label(match.decision if match else None),
                application.applied_at.isoformat() if application.applied_at else "",
                application.next_action_at.isoformat() if application.next_action_at else "",
                application.next_action_note or application.notes or "",
            ]
        )
    return output.getvalue()


def build_calendar_ics(session: Session, profile_id: UUID) -> str:
    _profile_or_404(session, profile_id)
    rows = _application_rows(session, profile_id)
    reminders = ReminderRepository(session).list_by_profile(profile_id)
    calendar = Calendar()

    def add_event(name: str, begin: datetime, description: str) -> None:
        event = Event(name=name, begin=begin, description=description)
        calendar.events.add(event)

    for application, offer, _ in rows:
        if application.next_action_at is not None:
            add_event(
                f"Próxima acción: {offer.title}",
                application.next_action_at,
                application.next_action_note or f"{offer.company} · {offer.title}",
            )
        if offer.deadline_at is not None:
            add_event(
                f"Vence: {offer.title}",
                offer.deadline_at,
                f"Fecha límite de {offer.company}.",
            )
    for reminder in reminders:
        add_event(
            reminder.message or "Recordatorio de postulación",
            reminder.due_at,
            f"Recordatorio {reminder.channel.value}.",
        )
    return str(calendar)

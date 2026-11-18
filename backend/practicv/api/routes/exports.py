from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from practicv.adapters.db.session import get_session
from practicv.services.exports import (
    build_applications_csv,
    build_applications_workbook,
    build_calendar_ics,
)

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/applications.xlsx")
def export_applications_xlsx(
    profile_id: UUID = Query(...),
    session: Session = Depends(get_session),
) -> Response:
    content = build_applications_workbook(session, profile_id)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="practicv-postulaciones.xlsx"',
        },
    )


@router.get("/applications.csv")
def export_applications_csv(
    profile_id: UUID = Query(...),
    session: Session = Depends(get_session),
) -> Response:
    content = build_applications_csv(session, profile_id)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="practicv-postulaciones.csv"',
        },
    )


@router.get("/calendar.ics")
def export_calendar(
    profile_id: UUID = Query(...),
    session: Session = Depends(get_session),
) -> Response:
    content = build_calendar_ics(session, profile_id)
    return Response(
        content=content,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="practicv-calendario.ics"',
        },
    )

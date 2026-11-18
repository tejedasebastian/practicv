import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from practicv.adapters.db.session import get_session
from practicv.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health(session: Session = Depends(get_session)) -> JSONResponse:
    settings = get_settings()
    try:
        session.execute(text("SELECT 1"))
        database = "ok"
        status_code = 200
    except SQLAlchemyError:
        logging.getLogger("practicv.health").warning(
            "database_unavailable",
            exc_info=True,
        )
        database = "unavailable"
        status_code = 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if database == "ok" else "degraded",
            "service": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "database": database,
        },
    )

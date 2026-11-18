from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from practicv.api.errors import domain_error_handler
from practicv.api.routes.analytics import router as analytics_router
from practicv.api.routes.health import router as health_router
from practicv.api.routes.offers import router as offers_router
from practicv.api.routes.profiles import router as profiles_router
from practicv.config import get_settings
from practicv.domain.errors import DomainError
from practicv.observability import RequestContextMiddleware, configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Copiloto de postulaciones para estudiantes.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)

app.add_exception_handler(DomainError, domain_error_handler)

app.include_router(health_router)
app.include_router(profiles_router, prefix="/api/v1")
app.include_router(offers_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.version,
        "docs": "/docs",
        "health": "/health",
    }

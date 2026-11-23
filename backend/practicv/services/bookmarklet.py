from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from practicv.services.offers import (
    _location_from_job,
    _salary_from_job,
    jobposting_from_jsonld,
    normalize_url,
    parse_datetime,
    parse_money,
)

MAX_TEXT_CHARS = 20_000
MAX_DESCRIPTION_CHARS = 8_000


def _clean(value: Any, limit: int = 500) -> str | None:
    if value is None:
        return None
    text = str(value)
    if "<" in text and ">" in text:
        text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    text = " ".join(text.split())
    return text[:limit] or None


def extract_bookmarklet(payload: dict) -> dict:
    """Turn a browser capture into editable offer fields.

    The browser sends JSON-LD blocks plus visible text. Nothing is persisted
    here; the user confirms the preview in the local app.
    """
    raw_jsonld = payload.get("jsonld") or []
    jsonld = [str(item) for item in raw_jsonld if item]
    job = jobposting_from_jsonld(jsonld)
    raw_text = str(payload.get("text") or "")
    warnings: list[str] = []

    title = _clean(job.get("title"), 300) or _clean(payload.get("title"), 300)
    organization = job.get("hiringOrganization") or {}
    company = _clean(organization.get("name") if isinstance(organization, dict) else None, 200)
    if not company:
        company = _clean(payload.get("company"), 200) or _clean(payload.get("og_site_name"), 200)

    description = _clean(job.get("description"), MAX_DESCRIPTION_CHARS)
    if not description and raw_text:
        description = _clean(raw_text, MAX_DESCRIPTION_CHARS)

    location = _location_from_job(job) or _clean(payload.get("location"), 200)
    modality = _clean(job.get("employmentType"), 50)
    salary_amount, salary_currency = _salary_from_job(job)
    if salary_amount is None:
        salary_text = _clean(payload.get("salary_text"), 100)
        salary_amount = parse_money(salary_text)
    else:
        salary_text = None
    deadline_at = parse_datetime(job.get("validThrough") or payload.get("deadline_at"))
    published_at = parse_datetime(job.get("datePosted") or payload.get("published_at"))
    source_url = normalize_url(job.get("url") or payload.get("url"))

    if not job:
        warnings.append("No se encontro JSON-LD JobPosting; revisa los campos.")
    if not title:
        warnings.append("Falta el titulo; completalo antes de guardar.")
    if not company:
        warnings.append("Falta la empresa; completala antes de guardar.")
    if len(raw_text) > MAX_TEXT_CHARS:
        warnings.append(f"El texto visible se recorto a {MAX_TEXT_CHARS} caracteres.")
    if not source_url:
        warnings.append("Falta la URL de la oferta.")

    if job:
        confidence = 0.9
    elif title and company:
        confidence = 0.55
    else:
        confidence = 0.3

    return {
        "title": title or "",
        "company": company or "",
        "source_url": source_url or "",
        "location": location,
        "modality": modality,
        "salary_text": salary_text,
        "salary_amount": salary_amount,
        "salary_currency": salary_currency,
        "description": description,
        "requirements_text": description,
        "published_at": published_at,
        "deadline_at": deadline_at,
        "confidence": confidence,
        "warnings": warnings,
    }

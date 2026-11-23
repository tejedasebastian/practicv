from __future__ import annotations

from sqlalchemy.orm import Session

from practicv.domain.errors import ValidationError
from practicv.services.offers import ImportResult, capture_url, normalize_url


def import_email_urls(
    session: Session,
    urls: list[str],
    user_agent: str,
) -> ImportResult:
    unique: list[str] = []
    for url in urls:
        normalized = normalize_url(url)
        if normalized and normalized not in unique:
            unique.append(normalized)

    result = ImportResult(total_rows=len(unique))
    for index, url in enumerate(unique, start=1):
        try:
            offer, duplicate = capture_url(session, url, user_agent)
            if duplicate:
                result.duplicates += 1
            else:
                result.created += 1
                result.offer_ids.append(str(offer.id))
            if index <= 5:
                result.preview.append(
                    {
                        "title": offer.title,
                        "company": offer.company,
                        "salary_amount": offer.salary_amount,
                        "source_url": offer.source_url,
                        "duplicate": duplicate,
                    }
                )
            if offer.salary_amount is None:
                result.warnings.append(f"Oferta {index}: sin sueldo/subvencion.")
        except ValidationError as exc:
            result.errors.append({"row": index, "message": exc.message, "details": exc.details})
    return result

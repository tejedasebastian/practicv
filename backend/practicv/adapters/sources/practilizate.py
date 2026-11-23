from __future__ import annotations

import csv
import io

from practicv.domain.errors import ValidationError
from practicv.services.offers import MAX_IMPORT_ROWS, normalize_key

REQUIRED_COLUMNS = ("title", "company", "url")


def parse_practilizate_csv(content: bytes) -> list[dict]:
    if not content:
        raise ValidationError("The Practilizate CSV is empty.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError("The Practilizate CSV must be UTF-8.") from exc

    reader = csv.DictReader(io.StringIO(text))
    headers = [normalize_key(header) for header in (reader.fieldnames or [])]
    missing = [column for column in REQUIRED_COLUMNS if column not in headers]
    if missing:
        raise ValidationError(
            "The Practilizate CSV is missing required columns.",
            {"missing": missing, "headers": headers},
        )

    rows: list[dict] = []
    for raw in reader:
        row = {normalize_key(key): value for key, value in raw.items()}
        if not any(value not in (None, "") for value in row.values()):
            continue
        rows.append(
            {
                "title": row.get("title"),
                "company": row.get("company"),
                "url": row.get("url"),
                "external_id": row.get("offer_id"),
                "location": row.get("location") or row.get("district"),
                "modality": row.get("modality") or row.get("attendance"),
                "salary_amount": row.get("salary_amount"),
                "salary_currency": row.get("salary_currency"),
                "published_at": row.get("published_at"),
                "deadline_at": row.get("deadline_at"),
                "description": row.get("requirements_text") or row.get("description"),
                "requirements_text": row.get("requirements_text"),
            }
        )

    if not rows:
        raise ValidationError("The Practilizate CSV has no data rows.")
    if len(rows) > MAX_IMPORT_ROWS:
        raise ValidationError(
            f"The import exceeds the {MAX_IMPORT_ROWS} row limit.",
            {"rows": len(rows), "max_rows": MAX_IMPORT_ROWS},
        )
    return rows

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from openpyxl import load_workbook
from sqlalchemy.orm import Session

from practicv.adapters.db.repositories import OfferRepository
from practicv.domain.entities import Offer, utcnow
from practicv.domain.enums import SourceType
from practicv.domain.errors import ConflictError, ValidationError
from practicv.services.matching import sync_offer_skills

MAX_IMPORT_ROWS = 500
MONEY_RE = re.compile(r"(\d[\d.,]*)")


@dataclass(slots=True)
class ImportResult:
    created: int = 0
    duplicates: int = 0
    errors: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_rows: int = 0
    preview: list[dict] = field(default_factory=list)
    offer_ids: list[str] = field(default_factory=list)


def normalize_key(value: str | None) -> str:
    if value is None:
        return ""
    decomposed = unicodedata.normalize("NFD", str(value))
    without_accents = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", without_accents.lower()).strip("_")


def normalize_url(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    parsed = urlparse(text)
    if not parsed.scheme or not parsed.netloc:
        return text
    query = [
        (key, item)
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    query.sort()
    path = parsed.path.rstrip("/") or "/"
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",
            urlencode(query),
            "",
        )
    )


def dedupe_hash_for(
    source_url: str | None,
    title: str,
    company: str,
    deadline_at: datetime | None,
) -> str:
    if source_url:
        basis = f"url:{source_url}"
    else:
        deadline = deadline_at.isoformat() if deadline_at else ""
        basis = f"text:{title.lower()}|{company.lower()}|{deadline}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def parse_datetime(value: object) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, date):
        result = datetime.combine(value, datetime.min.time(), tzinfo=UTC)
    else:
        try:
            result = date_parser.parse(str(value), dayfirst=True)
        except (ValueError, TypeError, OverflowError):
            return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


def parse_money(value: object) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value) if value >= 0 else None
    match = MONEY_RE.search(str(value))
    if not match:
        return None
    raw = match.group(1).strip(".,")
    if not raw:
        return None
    if "," in raw and "." in raw:
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "," in raw:
        raw = raw.replace(",", ".") if re.search(r",\d{1,2}$", raw) else raw.replace(",", "")
    elif "." in raw and not re.search(r"\.\d{1,2}$", raw):
        raw = raw.replace(".", "")
    try:
        amount = float(raw)
    except ValueError:
        return None
    return amount if amount >= 0 else None


def _pick(raw: dict, *keys: str) -> object | None:
    normalized = {normalize_key(key): value for key, value in raw.items()}
    for key in keys:
        value = normalized.get(normalize_key(key))
        if value is not None and value != "":
            return value
    return None


def _as_text(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return "; ".join(str(item).strip() for item in value if str(item).strip()) or None
    text = str(value).strip()
    return text or None


def normalize_offer(raw: dict, source_type: SourceType) -> Offer:
    title = _as_text(_pick(raw, "titulo", "title", "cargo", "puesto"))
    company = _as_text(_pick(raw, "empresa", "company", "entidad", "organizacion"))
    source_url = normalize_url(_as_text(_pick(raw, "url", "source_url", "link", "enlace")))
    if not title or not company:
        raise ValidationError(
            "Offer requires a title and a company.",
            {
                "missing": [
                    field for field, value in (("title", title), ("company", company)) if not value
                ]
            },
        )

    salary_text = _as_text(_pick(raw, "sueldo", "subvencion", "salary", "salary_text"))
    salary_amount = parse_money(_pick(raw, "subvencion_monto", "salary_amount", "monto", "sueldo"))
    if salary_amount is None:
        salary_amount = parse_money(salary_text)
    salary_currency = _as_text(_pick(raw, "moneda", "currency", "salary_currency"))
    if salary_amount is not None and not salary_currency:
        salary_currency = "PEN"

    description = _as_text(_pick(raw, "descripcion", "description"))
    requirements = _as_text(
        _pick(raw, "requisitos", "requirements", "requirements_text", "conocimientos")
    )
    deadline_at = parse_datetime(
        _pick(raw, "fecha_limite", "vence", "deadline_at", "deadline", "plazo_postular")
    )
    published_at = parse_datetime(
        _pick(raw, "publicado", "published_at", "datePosted", "fecha_publicacion")
    )
    location = _as_text(_pick(raw, "ubicacion", "location", "lugar_practicas", "distrito"))
    modality = _as_text(_pick(raw, "modalidad", "modality", "employmentType"))
    external_id = _as_text(_pick(raw, "id_oferta", "external_id", "id"))
    confidence = _pick(raw, "parse_confidence", "confidence")
    try:
        parse_confidence = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        parse_confidence = None

    raw_text = "\n\n".join(part for part in (description, requirements) if part) or None

    return Offer(
        title=title,
        company=company,
        source_type=source_type,
        external_id=external_id,
        source_url=source_url,
        captured_at=utcnow(),
        location=location,
        modality=modality,
        salary_text=salary_text,
        salary_amount=salary_amount,
        salary_currency=salary_currency,
        description=description,
        requirements_text=requirements,
        published_at=published_at,
        deadline_at=deadline_at,
        raw_text=raw_text,
        parse_confidence=parse_confidence,
        dedupe_hash=dedupe_hash_for(source_url, title, company, deadline_at),
    )


def save_offer(session: Session, raw: dict, source_type: SourceType) -> tuple[Offer, bool]:
    offer = normalize_offer(raw, source_type)
    repo = OfferRepository(session)
    existing = repo.get_by_dedupe_hash(offer.dedupe_hash) if offer.dedupe_hash else None
    if existing is not None:
        sync_offer_skills(session, existing)
        return existing, True
    try:
        created = repo.create(offer)
    except ConflictError:
        existing = repo.get_by_dedupe_hash(offer.dedupe_hash) if offer.dedupe_hash else None
        if existing is not None:
            sync_offer_skills(session, existing)
            return existing, True
        raise
    sync_offer_skills(session, created)
    return created, False


def parse_import_file(content: bytes, filename: str) -> list[dict]:
    lower = filename.lower()
    if lower.endswith(".csv"):
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = [
            {normalize_key(key): value for key, value in row.items()}
            for row in reader
            if any(value for value in row.values())
        ]
        headers = [normalize_key(key) for key in (reader.fieldnames or [])]
    elif lower.endswith(".xlsx"):
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        sheet = workbook.active
        raw_rows = list(sheet.iter_rows(values_only=True))
        if not raw_rows:
            raise ValidationError("The Excel file is empty.")
        headers = [normalize_key(str(value)) for value in raw_rows[0]]
        rows = [
            {header: value for header, value in zip(headers, row, strict=False) if header}
            for row in raw_rows[1:]
            if any(value is not None and value != "" for value in row)
        ]
    else:
        raise ValidationError(
            "Unsupported import format. Upload a CSV or XLSX file.",
            {"filename": filename},
        )

    if not rows:
        raise ValidationError("The import file has no data rows.")
    if len(rows) > MAX_IMPORT_ROWS:
        raise ValidationError(
            f"The import exceeds the {MAX_IMPORT_ROWS} row limit.",
            {"rows": len(rows), "max_rows": MAX_IMPORT_ROWS},
        )
    if "titulo" not in headers and "title" not in headers:
        raise ValidationError("Missing required column: titulo/title.", {"headers": headers})
    if "empresa" not in headers and "company" not in headers:
        raise ValidationError("Missing required column: empresa/company.", {"headers": headers})
    return rows


def import_rows(session: Session, rows: list[dict], source_type: SourceType) -> ImportResult:
    result = ImportResult(total_rows=len(rows))
    for index, row in enumerate(rows, start=2):
        try:
            offer, duplicate = save_offer(session, row, source_type)
            if duplicate:
                result.duplicates += 1
            else:
                result.created += 1
                result.offer_ids.append(str(offer.id))
            if index - 1 <= 5:
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
                result.warnings.append(f"Row {index}: offer has no salary/subvención.")
        except ValidationError as exc:
            result.errors.append({"row": index, "message": exc.message, "details": exc.details})
    return result


def _robots_allowed(url: str, user_agent: str) -> bool:
    parsed = urlparse(url)
    robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        response = httpx.get(
            robots_url,
            timeout=3.0,
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        )
        parser.parse(response.text.splitlines())
    except httpx.HTTPError:
        return True
    return parser.can_fetch(user_agent, url)


def jobposting_from_jsonld(raw_values: list[str]) -> dict:
    for raw in raw_values:
        if not raw:
            continue
        try:
            data = json.loads(raw, strict=False)
        except (json.JSONDecodeError, TypeError):
            continue
        candidates = data if isinstance(data, list) else [data]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            if candidate.get("@type") == "JobPosting":
                return candidate
            graph = candidate.get("@graph")
            if isinstance(graph, list):
                for item in graph:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        return item
    return {}


def _jsonld_jobposting(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    raw_values = [
        script.string or script.get_text()
        for script in soup.find_all("script", type="application/ld+json")
    ]
    return jobposting_from_jsonld(raw_values)


def _opengraph(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    values: dict[str, str] = {}
    for meta in soup.find_all("meta"):
        property_name = meta.get("property") or meta.get("name")
        content = meta.get("content")
        if property_name and content:
            values[property_name] = content
    return values


def _location_from_job(job: dict) -> str | None:
    location = job.get("jobLocation")
    if isinstance(location, list):
        location = location[0] if location else None
    if not isinstance(location, dict):
        return None
    address = location.get("address")
    if not isinstance(address, dict):
        return None
    parts = [
        address.get("addressLocality"),
        address.get("addressRegion"),
        address.get("addressCountry"),
    ]
    text = ", ".join(str(part) for part in parts if part)
    return text or None


def _salary_from_job(job: dict) -> tuple[float | None, str | None]:
    salary = job.get("baseSalary")
    if not isinstance(salary, dict):
        return None, None
    currency = salary.get("currency")
    value = salary.get("value")
    amount: object = value
    if isinstance(value, dict):
        amount = value.get("value") or value.get("minValue")
    try:
        return float(amount), str(currency) if currency else None
    except (TypeError, ValueError):
        return None, str(currency) if currency else None


def raw_offer_from_html(html: str, url: str) -> dict:
    job = _jsonld_jobposting(html)
    if job:
        description_html = job.get("description") or ""
        description = BeautifulSoup(description_html, "html.parser").get_text(" ", strip=True)
        salary_amount, salary_currency = _salary_from_job(job)
        organization = job.get("hiringOrganization") or {}
        company = organization.get("name") if isinstance(organization, dict) else None
        return {
            "titulo": job.get("title"),
            "empresa": company,
            "url": job.get("url") or url,
            "ubicacion": _location_from_job(job),
            "modalidad": job.get("employmentType"),
            "descripcion": description or None,
            "requisitos": description or None,
            "publicado": job.get("datePosted"),
            "fecha_limite": job.get("validThrough"),
            "subvencion_monto": salary_amount,
            "moneda": salary_currency,
            "parse_confidence": 0.9,
        }

    og = _opengraph(html)
    title = og.get("og:title")
    if not title:
        raise ValidationError(
            "Could not extract an offer from this URL. Paste the text manually.",
            {"url": url},
        )
    return {
        "titulo": title,
        "empresa": og.get("og:site_name") or "Empresa no identificada",
        "url": url,
        "descripcion": og.get("og:description"),
        "requisitos": og.get("og:description"),
        "parse_confidence": 0.4,
    }


def capture_url(session: Session, url: str, user_agent: str) -> tuple[Offer, bool]:
    if not _robots_allowed(url, user_agent):
        raise ValidationError(
            "robots.txt does not allow fetching this URL.",
            {"url": url},
        )
    try:
        response = httpx.get(
            url,
            timeout=10.0,
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValidationError(
            "Could not fetch the URL. Paste the offer text manually.",
            {"url": url},
        ) from exc
    raw = raw_offer_from_html(response.text, str(response.url))
    return save_offer(session, raw, SourceType.URL)

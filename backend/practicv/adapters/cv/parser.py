from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pdfplumber
import yaml
from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph
from rapidfuzz import process as fuzzy_process

from practicv.domain.errors import ValidationError

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
SUPPORTED_MIME_TYPES = {PDF_MIME, DOCX_MIME}
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SKILLS_PATH = DATA_DIR / "skills.yaml"

SECTION_ALIASES: dict[str, list[str]] = {
    "perfil": ["perfil", "perfil profesional", "resumen", "resumen profesional", "objetivo"],
    "contacto": ["contacto", "datos personales", "informacion personal"],
    "educacion": ["educacion", "formacion", "formacion academica", "estudios"],
    "experiencia": [
        "experiencia",
        "experiencia laboral",
        "experiencia profesional",
        "trayectoria",
    ],
    "proyectos": ["proyectos", "proyectos personales", "proyectos academicos"],
    "habilidades": [
        "habilidades",
        "habilidades tecnicas",
        "competencias",
        "conocimientos",
        "skills",
    ],
    "certificaciones": ["certificaciones", "cursos", "certificados", "capacitaciones"],
    "idiomas": ["idiomas", "languages"],
    "logros": ["logros", "reconocimientos", "premios"],
    "referencias": ["referencias"],
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?51[\s-]?)?9\d{2}[\s-]?\d{3}[\s-]?\d{3}")
GENERIC_PHONE_RE = re.compile(r"\+?\d[\d\s-]{7,}\d")


@dataclass(slots=True)
class ParsedCV:
    mime_type: str
    raw_text: str
    sections: dict[str, str]
    skills: list[dict]
    contact: dict[str, str | None]
    redacted_text: str
    warnings: list[str] = field(default_factory=list)


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    without_accents = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", without_accents).strip().lower()


def _normalize_line(text: str) -> str:
    return re.sub(r"[^a-z0-9+#./ ]+", " ", normalize_text(text)).strip()


@lru_cache
def load_skill_catalog() -> list[dict]:
    if not SKILLS_PATH.exists():
        raise FileNotFoundError(f"Skill catalog not found: {SKILLS_PATH}")
    with SKILLS_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or []
    if not isinstance(data, list):
        raise ValueError("skills.yaml must contain a list")
    return data


def _mime_type(filename: str, mime_type: str | None) -> str:
    if mime_type in SUPPORTED_MIME_TYPES:
        return mime_type
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return PDF_MIME
    if lower.endswith(".docx"):
        return DOCX_MIME
    raise ValidationError(
        "Unsupported CV format. Upload a PDF or DOCX file.",
        {"filename": filename, "mime_type": mime_type},
    )


def _extract_pdf_text(content: bytes) -> str:
    chunks: list[str] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text:
                chunks.append(text)
            for table in page.extract_tables() or []:
                for row in table:
                    cells = [str(cell).strip() for cell in row if cell]
                    if cells:
                        chunks.append(" | ".join(cells))
    return "\n".join(chunks)


def _extract_docx_text(content: bytes) -> str:
    document = DocxDocument(io.BytesIO(content))
    chunks: list[str] = []
    for block in document.element.body.iterchildren():
        if block.tag.endswith("}p"):
            paragraph = Paragraph(block, document)
            if paragraph.text.strip():
                chunks.append(paragraph.text)
        elif block.tag.endswith("}tbl"):
            table = Table(block, document)
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    chunks.append(" | ".join(cells))
    return "\n".join(chunks)


def extract_text(filename: str, mime_type: str | None, content: bytes) -> tuple[str, str]:
    resolved_mime = _mime_type(filename, mime_type)
    try:
        if resolved_mime == PDF_MIME:
            text = _extract_pdf_text(content)
        else:
            text = _extract_docx_text(content)
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(
            "Could not read the CV file. Check that it is a valid PDF or DOCX.",
            {"filename": filename},
        ) from exc
    text = text.strip()
    if len(text) < 40:
        raise ValidationError(
            "The CV does not contain enough text. If it is a scanned image, use a text-based PDF.",
            {"filename": filename, "characters": len(text)},
        )
    return text, resolved_mime


def _match_heading(line: str) -> str | None:
    normalized = _normalize_line(line)
    if not normalized or len(normalized) > 60 or len(normalized.split()) > 6:
        return None
    alias_to_section = {
        alias: section for section, aliases in SECTION_ALIASES.items() for alias in aliases
    }
    if normalized.rstrip(":") in alias_to_section:
        return alias_to_section[normalized.rstrip(":")]
    match = fuzzy_process.extractOne(
        normalized.rstrip(":"),
        alias_to_section.keys(),
        score_cutoff=92,
    )
    if match:
        return alias_to_section[match[0]]
    return None


def detect_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "otros"
    for line in text.splitlines():
        heading = _match_heading(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
            continue
        if line.strip():
            sections.setdefault(current, []).append(line.strip())
    if not sections:
        return {"otros": text.strip()}
    return {name: "\n".join(lines).strip() for name, lines in sections.items() if lines}


def _alias_pattern(alias: str) -> re.Pattern[str]:
    escaped = re.escape(normalize_text(alias))
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")


def extract_skills(text: str, catalog: list[dict]) -> list[dict]:
    matches: dict[str, dict] = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        normalized_line = normalize_text(line)
        intervals: list[tuple[int, int]] = []
        candidates: list[tuple[str, dict]] = []
        for skill in catalog:
            for alias in skill.get("aliases", []):
                if len(normalize_text(alias)) < 2:
                    continue
                candidates.append((alias, skill))
        candidates.sort(key=lambda item: len(item[0]), reverse=True)
        for alias, skill in candidates:
            pattern = _alias_pattern(alias)
            for match in pattern.finditer(normalized_line):
                start, end = match.span()
                if any(start < used_end and end > used_start for used_start, used_end in intervals):
                    continue
                intervals.append((start, end))
                skill_id = str(skill["id"])
                if skill_id not in matches:
                    matches[skill_id] = {
                        "skill_id": skill_id,
                        "canonical_name": skill["name"],
                        "category": skill.get("category", "other"),
                        "evidence": line[:240],
                        "confidence": 0.9,
                    }
    return list(matches.values())


def extract_contact(text: str) -> dict[str, str | None]:
    email = EMAIL_RE.search(text)
    phone = PHONE_RE.search(text) or GENERIC_PHONE_RE.search(text)
    return {
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None,
    }


def redact_pii(text: str) -> str:
    redacted = EMAIL_RE.sub("[EMAIL]", text)
    redacted = PHONE_RE.sub("[PHONE]", redacted)
    return redacted


def parse_cv(
    filename: str,
    mime_type: str | None,
    content: bytes,
    catalog: list[dict] | None = None,
) -> ParsedCV:
    text, resolved_mime = extract_text(filename, mime_type, content)
    skill_catalog = catalog or load_skill_catalog()
    sections = detect_sections(text)
    skills = extract_skills(text, skill_catalog)
    contact = extract_contact(text)
    warnings: list[str] = []
    if "experiencia" not in sections:
        warnings.append("No se detectó una sección de experiencia.")
    if "habilidades" not in sections:
        warnings.append("No se detectó una sección de habilidades.")
    if not skills:
        warnings.append("No se detectaron habilidades del catálogo.")
    if not contact["email"] and not contact["phone"]:
        warnings.append("No se detectaron datos de contacto.")
    return ParsedCV(
        mime_type=resolved_mime,
        raw_text=text,
        sections=sections,
        skills=skills,
        contact=contact,
        redacted_text=redact_pii(text),
        warnings=warnings,
    )

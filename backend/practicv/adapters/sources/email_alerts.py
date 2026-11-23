from __future__ import annotations

import re
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from practicv.domain.errors import ValidationError
from practicv.services.offers import normalize_url

MAX_EMAIL_BYTES = 2 * 1024 * 1024
MAX_CANDIDATES = 30
URL_RE = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)


@dataclass(slots=True)
class EmailCandidate:
    url: str
    title: str
    source: str


@dataclass(slots=True)
class EmailPreview:
    subject: str
    candidates: list[EmailCandidate]
    warnings: list[str]


def _clean(value: str | None, limit: int = 200) -> str:
    if not value:
        return ""
    return " ".join(value.split())[:limit]


def _canonical_offer_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path
    if "linkedin.com" in host and "/jobs/view/" in path:
        match = re.search(r"/jobs/view/(\d+)", path)
        if match:
            return f"https://www.linkedin.com/jobs/view/{match.group(1)}"
    return url


def _is_offer_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if host in {"apps.microsoft.com", "itunes.apple.com", "play.google.com"}:
        return False
    if any(token in path for token in ("unsubscribe", "preferences", "privacy", "terms")):
        return False
    if "linkedin.com" in host:
        return "/jobs/view/" in path
    return True


def _add_candidate(
    candidates: dict[str, EmailCandidate],
    url: str | None,
    title: str | None,
    source: str,
) -> None:
    if not url:
        return
    normalized = normalize_url(url.strip().rstrip(".,;)"))
    if not normalized or not normalized.startswith(("http://", "https://")):
        return
    normalized = _canonical_offer_url(normalized)
    if not _is_offer_url(normalized):
        return
    if normalized in candidates:
        existing = candidates[normalized]
        if title and (not existing.title or existing.title.startswith("Oferta en ")):
            existing.title = _clean(title)
        return
    host = urlparse(normalized).netloc
    candidates[normalized] = EmailCandidate(
        url=normalized,
        title=_clean(title) or f"Oferta en {host}",
        source=source,
    )


def parse_email(content: bytes) -> EmailPreview:
    if not content:
        raise ValidationError("The email file is empty.")
    if len(content) > MAX_EMAIL_BYTES:
        raise ValidationError(
            "The email file exceeds the 2 MB limit.",
            {"bytes": len(content), "max_bytes": MAX_EMAIL_BYTES},
        )

    message = BytesParser(policy=policy.default).parsebytes(content)
    subject = _clean(message.get("Subject"), 200)
    candidates: dict[str, EmailCandidate] = {}
    warnings: list[str] = []

    html_parts: list[str] = []
    text_parts: list[str] = []
    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        content_type = part.get_content_type()
        try:
            body = part.get_content()
        except (LookupError, UnicodeDecodeError):
            continue
        if not isinstance(body, str):
            continue
        if content_type == "text/html":
            html_parts.append(body)
        elif content_type == "text/plain":
            text_parts.append(body)

    for html in html_parts:
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.find_all("a", href=True):
            _add_candidate(candidates, anchor.get("href"), anchor.get_text(" ", strip=True), "html")

    for text in text_parts:
        lines = [line.strip() for line in text.splitlines()]
        for index, line in enumerate(lines):
            for match in URL_RE.finditer(line):
                title = ""
                for previous in reversed(lines[:index]):
                    if previous and not previous.startswith(("http://", "https://")):
                        title = previous
                        break
                _add_candidate(candidates, match.group(0), title, "text")

    if not html_parts and not text_parts:
        warnings.append("El correo no tiene cuerpo HTML ni texto plano.")
    if not candidates:
        warnings.append("No se encontraron enlaces de ofertas en el correo.")
    if len(candidates) > MAX_CANDIDATES:
        warnings.append(f"Se muestran los primeros {MAX_CANDIDATES} enlaces.")
        ordered = list(candidates.values())[:MAX_CANDIDATES]
    else:
        ordered = list(candidates.values())

    return EmailPreview(subject=subject, candidates=ordered, warnings=warnings)

from __future__ import annotations

from practicv.adapters.cv.parser import normalize_text


class StubLLM:
    """Deterministic local adapter. It never calls an external service."""

    name = "stub"

    def analyze(self, text: str) -> list[str]:
        normalized = normalize_text(text)
        suggestions: list[str] = []
        if "experiencia" not in normalized:
            suggestions.append("Agrega una sección de experiencia con logros medibles.")
        if "proyecto" not in normalized:
            suggestions.append("Incluye 1–2 proyectos con stack, tu rol y el resultado.")
        if "%" not in text and "logro" not in normalized:
            suggestions.append("Cuantifica al menos un logro con un número o porcentaje.")
        if "habilidad" not in normalized:
            suggestions.append("Agrupa las habilidades por categoría (datos, backend, BI).")
        if not suggestions:
            suggestions.append(
                "La estructura es clara; revisa ortografía y adapta el CV a cada oferta."
            )
        return suggestions

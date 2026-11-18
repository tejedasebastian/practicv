from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from practicv.adapters.cv.parser import extract_skills, load_skill_catalog, normalize_text
from practicv.adapters.db.repositories import (
    MatchRepository,
    OfferRepository,
    OfferSkillRepository,
    ProfileRepository,
    ProfileSkillRepository,
    SkillRepository,
)
from practicv.domain.entities import Match, Offer, Skill
from practicv.domain.enums import MatchDecision, RequirementType
from practicv.domain.errors import NotFoundError

MUST_KEYWORDS = ("indispensable", "excluyente", "obligatorio", "requerido", "requisito")
NICE_KEYWORDS = ("deseable", "plus", "valor agregado")
LEVEL_KEYWORDS = (("avanzado", 3), ("intermedio", 2), ("basico", 1))
WEIGHTS = {
    RequirementType.MUST: 3.0,
    RequirementType.NICE: 1.0,
    RequirementType.UNKNOWN: 1.5,
}


def _classify_requirement(evidence: str | None, default: RequirementType) -> RequirementType:
    normalized = normalize_text(evidence or "")
    if any(keyword in normalized for keyword in NICE_KEYWORDS):
        return RequirementType.NICE
    if any(keyword in normalized for keyword in MUST_KEYWORDS):
        return RequirementType.MUST
    return default


def _required_level(evidence: str | None) -> int:
    normalized = normalize_text(evidence or "")
    for keyword, level in LEVEL_KEYWORDS:
        if keyword in normalized:
            return level
    return 2


def sync_offer_skills(session: Session, offer: Offer) -> list[dict]:
    catalog = load_skill_catalog()
    catalog_by_id = {entry["id"]: entry for entry in catalog}
    merged: dict[str, dict] = {}
    sources = (
        (offer.requirements_text, RequirementType.MUST),
        (offer.description, RequirementType.UNKNOWN),
        (offer.title, RequirementType.UNKNOWN),
    )
    for text, default in sources:
        if not text:
            continue
        for extracted in extract_skills(text, catalog):
            catalog_entry = catalog_by_id.get(extracted["skill_id"], {})
            requirement_type = _classify_requirement(
                extracted.get("evidence"),
                default,
            )
            current = merged.get(extracted["skill_id"])
            if current is None or (
                current["requirement_type"] != RequirementType.MUST
                and requirement_type == RequirementType.MUST
            ):
                merged[extracted["skill_id"]] = {
                    "skill_id": extracted["skill_id"],
                    "canonical_name": extracted["canonical_name"],
                    "category": extracted.get("category", "other"),
                    "aliases": catalog_entry.get("aliases", []),
                    "requirement_type": requirement_type,
                    "required_level": _required_level(extracted.get("evidence")),
                    "evidence_text": extracted.get("evidence"),
                    "confidence": extracted.get("confidence"),
                }

    skill_repo = SkillRepository(session)
    items: list[tuple[UUID, RequirementType, int, str | None, float | None]] = []
    for entry in merged.values():
        skill = skill_repo.get_by_canonical_name(entry["canonical_name"])
        if skill is None:
            skill = skill_repo.create(
                Skill(
                    canonical_name=entry["canonical_name"],
                    category=entry["category"],
                    aliases=entry["aliases"],
                )
            )
        items.append(
            (
                skill.id,
                entry["requirement_type"],
                entry["required_level"],
                entry["evidence_text"],
                entry["confidence"],
            )
        )
    return OfferSkillRepository(session).replace_for_offer(offer.id, items)


def compute_match(session: Session, profile_id: UUID, offer_id: UUID) -> Match:
    profile = ProfileRepository(session).get(profile_id)
    if profile is None:
        raise NotFoundError("Profile not found", {"profile_id": str(profile_id)})
    offer = OfferRepository(session).get(offer_id)
    if offer is None:
        raise NotFoundError("Offer not found", {"offer_id": str(offer_id)})

    offer_skills = OfferSkillRepository(session).list_for_offer(offer_id)
    if not offer_skills:
        offer_skills = sync_offer_skills(session, offer)

    profile_levels = {
        str(item["skill_id"]): int(item["level"])
        for item in ProfileSkillRepository(session).list_for_profile(profile_id)
    }

    total_weight = 0.0
    weighted_score = 0.0
    must_weight = 0.0
    must_score = 0.0
    gaps: list[dict] = []
    explanation: list[dict] = []

    for requirement in offer_skills:
        requirement_type = RequirementType(requirement["requirement_type"])
        required_level = int(requirement["required_level"])
        user_level = profile_levels.get(str(requirement["skill_id"]), 0)
        weight = WEIGHTS[requirement_type]
        coverage = min(user_level, required_level) / required_level
        total_weight += weight
        weighted_score += weight * coverage
        if requirement_type == RequirementType.MUST:
            must_weight += weight
            must_score += weight * coverage

        status = "met" if user_level >= required_level else "gap"
        suggestion: str | None = None
        if status == "gap":
            if user_level == 0:
                suggestion = (
                    f"Agrega evidencia de {requirement['canonical_name']} (nivel {required_level})."
                )
            else:
                suggestion = (
                    f"Sube {requirement['canonical_name']} de nivel {user_level} "
                    f"a {required_level}."
                )
            gaps.append(
                {
                    "skill_id": str(requirement["skill_id"]),
                    "skill": requirement["canonical_name"],
                    "requirement_type": requirement_type.value,
                    "required_level": required_level,
                    "user_level": user_level,
                    "evidence": requirement.get("evidence_text"),
                    "suggestion": suggestion,
                }
            )
        explanation.append(
            {
                "skill_id": str(requirement["skill_id"]),
                "skill": requirement["canonical_name"],
                "requirement_type": requirement_type.value,
                "required_level": required_level,
                "user_level": user_level,
                "status": status,
                "evidence": requirement.get("evidence_text"),
                "suggestion": suggestion,
            }
        )

    overall_score = round(100 * weighted_score / total_weight, 2) if total_weight else 0.0
    must_have_score = round(100 * must_score / must_weight, 2) if must_weight else 100.0
    confidences = [float(requirement.get("confidence") or 0.7) for requirement in offer_skills]
    confidence = round(100 * sum(confidences) / len(confidences), 1) if confidences else 0.0

    if must_have_score >= 85 and overall_score >= 80:
        decision = MatchDecision.APPLY
    elif must_have_score >= 60:
        decision = MatchDecision.APPLY_WITH_GAPS
    else:
        decision = MatchDecision.IMPROVE_CV

    match = Match(
        profile_id=profile_id,
        offer_id=offer_id,
        overall_score=overall_score,
        must_have_score=must_have_score,
        confidence=confidence,
        decision=decision,
        gaps_json=gaps,
        explanation_json=explanation,
    )
    return MatchRepository(session).create(match)

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy.orm import Session

from practicv.adapters.cv.parser import load_skill_catalog, parse_cv, redact_pii
from practicv.adapters.db.repositories import (
    CVDocumentRepository,
    ProfileRepository,
    ProfileSkillRepository,
    SkillRepository,
)
from practicv.adapters.db.session import get_session
from practicv.adapters.llm.stub import StubLLM
from practicv.api.schemas import (
    AnalyzeAIRequest,
    AnalyzeAIResponse,
    CVContact,
    CVSkillResponse,
    CVUploadResponse,
    ProfileCreate,
    ProfileResponse,
    ProfileSkillListResponse,
    ProfileSkillUpdate,
    ProfileUpdate,
)
from practicv.domain.entities import CVDocument, Profile, Skill
from practicv.domain.errors import NotFoundError, ValidationError

router = APIRouter(prefix="/profiles", tags=["profiles"])

MAX_CV_BYTES = 5 * 1024 * 1024


def _get_profile_or_404(session: Session, profile_id: UUID) -> Profile:
    profile = ProfileRepository(session).get(profile_id)
    if profile is None:
        raise NotFoundError("Profile not found", {"profile_id": str(profile_id)})
    return profile


def _ensure_skills(session: Session, parsed_skills: list[dict]) -> dict[str, UUID]:
    catalog = {entry["id"]: entry for entry in load_skill_catalog()}
    repo = SkillRepository(session)
    mapping: dict[str, UUID] = {}
    for parsed in parsed_skills:
        entry = catalog.get(parsed["skill_id"])
        if entry is None:
            continue
        skill = repo.get_by_canonical_name(entry["name"])
        if skill is None:
            skill = repo.create(
                Skill(
                    canonical_name=entry["name"],
                    category=entry.get("category", "other"),
                    aliases=entry.get("aliases", []),
                )
            )
        mapping[parsed["skill_id"]] = skill.id
    return mapping


def _parsed_skill_responses(
    parsed_skills: list[dict],
    mapping: dict[str, UUID],
) -> list[CVSkillResponse]:
    responses: list[CVSkillResponse] = []
    for parsed in parsed_skills:
        skill_id = mapping.get(parsed["skill_id"])
        if skill_id is None:
            continue
        responses.append(
            CVSkillResponse(
                skill_id=skill_id,
                canonical_name=parsed["canonical_name"],
                category=parsed.get("category", "other"),
                level=1,
                evidence=parsed.get("evidence"),
                confidence=parsed.get("confidence"),
                confirmed=False,
            )
        )
    return responses


@router.post("", response_model=ProfileResponse, status_code=201)
def create_profile(
    payload: ProfileCreate,
    session: Session = Depends(get_session),
) -> ProfileResponse:
    profile = Profile(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        university=payload.university,
        career=payload.career,
        cycle=payload.cycle,
        location=payload.location,
        target_roles=payload.target_roles,
        preferred_modality=payload.preferred_modality,
        salary_expectation=payload.salary_expectation,
        availability=payload.availability,
        locale=payload.locale,
    )
    created = ProfileRepository(session).create(profile)
    session.commit()
    return ProfileResponse.model_validate(created)


@router.get("", response_model=list[ProfileResponse])
def list_profiles(session: Session = Depends(get_session)) -> list[ProfileResponse]:
    return [
        ProfileResponse.model_validate(profile) for profile in ProfileRepository(session).list()
    ]


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: UUID,
    session: Session = Depends(get_session),
) -> ProfileResponse:
    return ProfileResponse.model_validate(_get_profile_or_404(session, profile_id))


@router.patch("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: UUID,
    payload: ProfileUpdate,
    session: Session = Depends(get_session),
) -> ProfileResponse:
    _get_profile_or_404(session, profile_id)
    fields = payload.model_dump(exclude_unset=True)
    updated = ProfileRepository(session).update(profile_id, **fields)
    session.commit()
    return ProfileResponse.model_validate(updated)


@router.delete("/{profile_id}", status_code=204)
def delete_profile(
    profile_id: UUID,
    session: Session = Depends(get_session),
) -> Response:
    _get_profile_or_404(session, profile_id)
    ProfileRepository(session).delete(profile_id)
    session.commit()
    return Response(status_code=204)


@router.post("/{profile_id}/cv", response_model=CVUploadResponse, status_code=201)
async def upload_cv(
    profile_id: UUID,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> CVUploadResponse:
    _get_profile_or_404(session, profile_id)
    content = await file.read()
    if not content:
        raise ValidationError("The uploaded file is empty.")
    if len(content) > MAX_CV_BYTES:
        raise ValidationError(
            "The CV exceeds the 5 MB limit.",
            {"bytes": len(content), "max_bytes": MAX_CV_BYTES},
        )

    filename = Path(file.filename or "cv.pdf").name
    parsed = parse_cv(filename, file.content_type, content)
    mapping = _ensure_skills(session, parsed.skills)
    profile_skill_repo = ProfileSkillRepository(session)
    profile_skill_repo.replace_for_profile(
        profile_id,
        [
            (mapping[parsed_skill["skill_id"]], 1, parsed_skill.get("evidence"), False)
            for parsed_skill in parsed.skills
            if parsed_skill["skill_id"] in mapping
        ],
    )

    cv_repo = CVDocumentRepository(session)
    cv_repo.deactivate_all(profile_id)
    document = cv_repo.create(
        CVDocument(
            profile_id=profile_id,
            filename=filename,
            mime_type=parsed.mime_type,
            raw_text=parsed.raw_text,
            parsed_json={
                "mime_type": parsed.mime_type,
                "sections": parsed.sections,
                "skills": parsed.skills,
                "contact": parsed.contact,
                "warnings": parsed.warnings,
                "redacted_text": parsed.redacted_text,
            },
            file_bytes=content,
            is_active=True,
        )
    )
    session.commit()

    return CVUploadResponse(
        cv_id=document.id,
        filename=document.filename,
        mime_type=document.mime_type,
        raw_text=parsed.raw_text,
        sections=parsed.sections,
        skills=_parsed_skill_responses(parsed.skills, mapping),
        contact=CVContact(**parsed.contact),
        warnings=parsed.warnings,
        redacted_text=parsed.redacted_text,
    )


@router.get("/{profile_id}/cv", response_model=CVUploadResponse)
def get_cv(
    profile_id: UUID,
    session: Session = Depends(get_session),
) -> CVUploadResponse:
    _get_profile_or_404(session, profile_id)
    document = CVDocumentRepository(session).get_active(profile_id)
    if document is None:
        raise NotFoundError("CV not found", {"profile_id": str(profile_id)})

    parsed = document.parsed_json or {}
    stored_skills = ProfileSkillRepository(session).list_for_profile(profile_id)
    if stored_skills:
        skills = [CVSkillResponse(**item) for item in stored_skills]
    else:
        mapping: dict[str, UUID] = {}
        skill_repo = SkillRepository(session)
        for parsed_skill in parsed.get("skills", []):
            skill = skill_repo.get_by_canonical_name(parsed_skill["canonical_name"])
            if skill is not None:
                mapping[parsed_skill["skill_id"]] = skill.id
        skills = _parsed_skill_responses(parsed.get("skills", []), mapping)

    return CVUploadResponse(
        cv_id=document.id,
        filename=document.filename,
        mime_type=document.mime_type,
        raw_text=document.raw_text or "",
        sections=parsed.get("sections", {}),
        skills=skills,
        contact=CVContact(**parsed.get("contact", {})),
        warnings=parsed.get("warnings", []),
        redacted_text=parsed.get("redacted_text", ""),
    )


@router.patch("/{profile_id}/cv/skills", response_model=ProfileSkillListResponse)
def update_cv_skills(
    profile_id: UUID,
    payload: ProfileSkillUpdate,
    session: Session = Depends(get_session),
) -> ProfileSkillListResponse:
    _get_profile_or_404(session, profile_id)
    skill_repo = SkillRepository(session)
    items: list[tuple[UUID, int, str | None, bool]] = []
    for item in payload.skills:
        if skill_repo.get(item.skill_id) is None:
            raise ValidationError(
                "Skill not found in the catalog.",
                {"skill_id": str(item.skill_id)},
            )
        items.append((item.skill_id, item.level, item.evidence, item.confirmed))
    updated = ProfileSkillRepository(session).replace_for_profile(profile_id, items)
    session.commit()
    return ProfileSkillListResponse(
        skills=[CVSkillResponse(**item) for item in updated],
    )


@router.post("/{profile_id}/cv/analyze-ai", response_model=AnalyzeAIResponse)
def analyze_cv(
    profile_id: UUID,
    payload: AnalyzeAIRequest,
    session: Session = Depends(get_session),
) -> AnalyzeAIResponse:
    _get_profile_or_404(session, profile_id)
    if not payload.consent:
        raise ValidationError(
            "Consent is required before sending CV text to the AI adapter.",
            {"consent": False},
        )
    redacted = redact_pii(payload.text)
    llm = StubLLM()
    return AnalyzeAIResponse(
        provider=llm.name,
        redacted_text=redacted,
        pii_removed=redacted != payload.text,
        suggestions=llm.analyze(redacted),
    )

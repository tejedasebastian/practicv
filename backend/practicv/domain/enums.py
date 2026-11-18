from enum import StrEnum


class SourceType(StrEnum):
    MANUAL = "manual"
    CSV = "csv"
    URL = "url"
    BOOKMARKLET = "bookmarklet"
    EMAIL = "email"
    MCP_PRACTICAS_PE = "mcp_practicas_pe"
    PRACTILIZATE = "practilizate"
    ATS = "ats"


class RequirementType(StrEnum):
    MUST = "must"
    NICE = "nice"
    UNKNOWN = "unknown"


class MatchDecision(StrEnum):
    APPLY = "apply"
    APPLY_WITH_GAPS = "apply_with_gaps"
    IMPROVE_CV = "improve_cv"


class ApplicationStatus(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    OFFER = "offer"


class ReminderChannel(StrEnum):
    IN_APP = "in_app"
    ICS = "ics"


class ReminderStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"
    DISMISSED = "dismissed"


class SkillSource(StrEnum):
    CV = "cv"
    MANUAL = "manual"
    COURSE = "course"


class OfferLinkKind(StrEnum):
    APPLICATION = "application"
    BASES = "bases"
    OTHER = "other"

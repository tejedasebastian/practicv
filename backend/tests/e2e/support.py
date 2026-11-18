from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ApiContext:
    base_url: str
    profile_id: str
    offer_ids: list[str]
    application_ids: list[str]

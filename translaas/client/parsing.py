"""Parse JSON bodies from the Translaas SDK translation endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional, cast

from translaas.exceptions import TranslaasApiException
from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject

_PROJECT_META = frozenset(
    {"project", "lang", "version", "generatedAt", "groupEntryContext", "groups"}
)


def translation_group_from_response(data: Any) -> TranslationGroup:
    """Parse `GetGroupTranslationsResponse` or flat-json map."""
    if not isinstance(data, dict):
        raise TranslaasApiException(
            f"Invalid group response: expected object, got {type(data).__name__}",
            status_code=None,
        )
    if "entries" in data and isinstance(data["entries"], dict):
        ec_raw = data.get("entryContext")
        ec: Optional[dict[str, dict[str, str]]] = None
        if isinstance(ec_raw, dict):
            ec = cast(Dict[str, Dict[str, str]], ec_raw)
        ver = data.get("version")
        return TranslationGroup(
            entries=data["entries"],
            entry_context=ec,
            version=ver if isinstance(ver, int) else None,
            generated_at=data.get("generatedAt")
            if isinstance(data.get("generatedAt"), str)
            else None,
            project=data.get("project") if isinstance(data.get("project"), str) else None,
            lang=data.get("lang") if isinstance(data.get("lang"), str) else None,
        )
    return TranslationGroup(entries=dict(data))


def translation_project_from_response(data: Any) -> TranslationProject:
    """Parse nested project payload or legacy root map of groups."""
    if not isinstance(data, dict):
        raise TranslaasApiException(
            f"Invalid project response: expected object, got {type(data).__name__}",
            status_code=None,
        )
    gec = data.get("groupEntryContext")
    if "groups" in data and isinstance(data["groups"], dict):
        return TranslationProject(groups=data["groups"], group_entry_context=gec)
    groups_map = {k: v for k, v in data.items() if k not in _PROJECT_META}
    return TranslationProject(groups=groups_map, group_entry_context=gec)


def project_locales_from_response(data: Any) -> ProjectLocales:
    """Parse locales list or `GetProjectLocalesResponse` object."""
    if isinstance(data, list):
        if not all(isinstance(x, str) for x in data):
            raise TranslaasApiException(
                "Invalid locales response: list items must be strings",
                status_code=None,
            )
        return ProjectLocales(locales=data)
    if isinstance(data, dict) and "locales" in data:
        locales_list = data["locales"]
        if not isinstance(locales_list, list):
            raise TranslaasApiException(
                f"Invalid locales format: expected list, got {type(locales_list).__name__}",
                status_code=None,
            )
        if not all(isinstance(x, str) for x in locales_list):
            raise TranslaasApiException(
                "Invalid locales response: locale codes must be strings",
                status_code=None,
            )
        proj = data.get("project") if isinstance(data.get("project"), str) else None
        lm = data.get("lastModifiedUtc") if isinstance(data.get("lastModifiedUtc"), str) else None
        return ProjectLocales(locales=locales_list, project=proj, last_modified_utc=lm)
    raise TranslaasApiException(
        f"Invalid response format: expected dict with 'locales' or list, got {type(data).__name__}",
        status_code=None,
    )

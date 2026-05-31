"""SDK API request/response payloads aligned with the Translaas OpenAPI spec."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from translaas.exceptions import TranslaasConfigurationException


@dataclass(frozen=True)
class ReportMissingKeyItem:
    """Single missing translation key reported to the API."""

    group_key: str
    entry_key: str
    language_iso_code: str

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "groupKey": self.group_key,
            "entryKey": self.entry_key,
            "languageIsoCode": self.language_iso_code,
        }


@dataclass(frozen=True)
class ValidateApiKeyResult:
    """Response from `GET /api/v1/api-keys/validate`."""

    is_valid: bool
    tenant_id: str
    project_id: Optional[str]
    project_ids: tuple[str, ...]
    default_project_id: Optional[str]
    integration_name: Optional[str]
    authenticated_at: Optional[str]

    @classmethod
    def from_api_dict(cls, data: dict[str, Any]) -> ValidateApiKeyResult:
        def _str_or_none(val: Any) -> Optional[str]:
            if val is None:
                return None
            return str(val)

        raw_ids = data.get("projectIds") or []
        project_ids = tuple(str(item) for item in raw_ids) if isinstance(raw_ids, list) else ()

        return cls(
            is_valid=bool(data.get("isValid", False)),
            tenant_id=_str_or_none(data.get("tenantId")) or "",
            project_id=_str_or_none(data.get("projectId")),
            project_ids=project_ids,
            default_project_id=_str_or_none(data.get("defaultProjectId")),
            integration_name=_str_or_none(data.get("integrationName")),
            authenticated_at=_str_or_none(data.get("authenticatedAt")),
        )


def resolve_default_project_id(
    configured_project: Optional[str], validate: ValidateApiKeyResult
) -> str:
    """Resolve default project id from validate when not configured explicitly."""
    configured = (configured_project or "").strip()
    if configured:
        return configured

    if not validate.project_ids:
        raise TranslaasConfigurationException(
            "Tenant-level API key requires default_project in SDK configuration."
        )

    resolved = (
        (validate.default_project_id or "").strip()
        or (validate.project_id or "").strip()
        or validate.project_ids[0].strip()
    )
    if not resolved:
        raise TranslaasConfigurationException(
            "Could not resolve a default project from the validate API key response."
        )
    return resolved


def report_missing_keys_body(keys: list[ReportMissingKeyItem]) -> dict[str, Any]:
    """Build JSON body for `POST /sdk/v1/translations/report-missing`."""
    return {"keys": [k.to_api_dict() for k in keys]}

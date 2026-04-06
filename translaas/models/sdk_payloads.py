"""SDK API request/response payloads aligned with the Translaas OpenAPI spec."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ReportMissingKeyItem:
    """Single missing translation key reported to the API."""

    group_key: str
    entry_key: str
    language_iso_code: str

    def to_api_dict(self) -> Dict[str, Any]:
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
    integration_name: Optional[str]
    authenticated_at: Optional[str]

    @classmethod
    def from_api_dict(cls, data: Dict[str, Any]) -> ValidateApiKeyResult:
        def _str_or_none(val: Any) -> Optional[str]:
            if val is None:
                return None
            return str(val)

        return cls(
            is_valid=bool(data.get("isValid", False)),
            tenant_id=_str_or_none(data.get("tenantId")) or "",
            project_id=_str_or_none(data.get("projectId")),
            integration_name=_str_or_none(data.get("integrationName")),
            authenticated_at=_str_or_none(data.get("authenticatedAt")),
        )


def report_missing_keys_body(keys: List[ReportMissingKeyItem]) -> Dict[str, Any]:
    """Build JSON body for `POST /sdk/v1/translations/report-missing`."""
    return {"keys": [k.to_api_dict() for k in keys]}

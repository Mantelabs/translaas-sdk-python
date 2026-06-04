"""Tests for SDK JSON payload helpers."""

import pytest

from translaas.exceptions import TranslaasConfigurationException
from translaas.models.sdk_payloads import (
    ReportMissingKeyItem,
    ValidateApiKeyResult,
    report_missing_keys_body,
    resolve_default_project_id,
)


def test_report_missing_key_item_to_api_dict() -> None:
    item = ReportMissingKeyItem("grp", "ent", "en")
    assert item.to_api_dict() == {
        "groupKey": "grp",
        "entryKey": "ent",
        "languageIsoCode": "en",
    }


def test_report_missing_keys_body() -> None:
    body = report_missing_keys_body(
        [
            ReportMissingKeyItem("g1", "e1", "en"),
            ReportMissingKeyItem("g2", "e2", "fr"),
        ]
    )
    assert body == {
        "keys": [
            {"groupKey": "g1", "entryKey": "e1", "languageIsoCode": "en"},
            {"groupKey": "g2", "entryKey": "e2", "languageIsoCode": "fr"},
        ]
    }


def test_validate_api_key_result_from_api_dict_full() -> None:
    r = ValidateApiKeyResult.from_api_dict(
        {
            "isValid": True,
            "tenantId": "t1",
            "projectId": "p1",
            "projectIds": ["p1", "p2"],
            "defaultProjectId": "p1",
            "integrationName": "acme",
            "authenticatedAt": "2024-01-01T00:00:00Z",
        }
    )
    assert r.is_valid is True
    assert r.tenant_id == "t1"
    assert r.project_id == "p1"
    assert r.project_ids == ("p1", "p2")
    assert r.default_project_id == "p1"
    assert r.integration_name == "acme"
    assert r.authenticated_at == "2024-01-01T00:00:00Z"


def test_validate_api_key_result_from_api_dict_minimal() -> None:
    r = ValidateApiKeyResult.from_api_dict({})
    assert r.is_valid is False
    assert r.tenant_id == ""
    assert r.project_id is None
    assert r.project_ids == ()
    assert r.default_project_id is None


def test_resolve_default_project_id_uses_configured() -> None:
    validate = ValidateApiKeyResult(
        is_valid=True,
        tenant_id="t",
        project_id=None,
        project_ids=("p1", "p2"),
        default_project_id="p2",
        integration_name=None,
        authenticated_at=None,
    )
    assert resolve_default_project_id("configured", validate) == "configured"


def test_resolve_default_project_id_uses_default_from_validate() -> None:
    validate = ValidateApiKeyResult(
        is_valid=True,
        tenant_id="t",
        project_id="legacy",
        project_ids=("p1", "p2"),
        default_project_id="p2",
        integration_name=None,
        authenticated_at=None,
    )
    assert resolve_default_project_id(None, validate) == "p2"


def test_resolve_default_project_id_tenant_key_requires_config() -> None:
    validate = ValidateApiKeyResult(
        is_valid=True,
        tenant_id="t",
        project_id=None,
        project_ids=(),
        default_project_id=None,
        integration_name=None,
        authenticated_at=None,
    )
    with pytest.raises(TranslaasConfigurationException):
        resolve_default_project_id(None, validate)

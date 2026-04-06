"""Tests for SDK JSON payload helpers."""

from translaas.models.sdk_payloads import (
    ReportMissingKeyItem,
    ValidateApiKeyResult,
    report_missing_keys_body,
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
            "integrationName": "acme",
            "authenticatedAt": "2024-01-01T00:00:00Z",
        }
    )
    assert r.is_valid is True
    assert r.tenant_id == "t1"
    assert r.project_id == "p1"
    assert r.integration_name == "acme"
    assert r.authenticated_at == "2024-01-01T00:00:00Z"


def test_validate_api_key_result_from_api_dict_minimal() -> None:
    r = ValidateApiKeyResult.from_api_dict({})
    assert r.is_valid is False
    assert r.tenant_id == ""
    assert r.project_id is None

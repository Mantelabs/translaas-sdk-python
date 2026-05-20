"""Tests for offline ZIP bundle parsing."""

from __future__ import annotations

import io
import json
import zipfile

import pytest

from translaas.offline.zip_bundle import OfflineBundle, parse_offline_zip, resolve_project_key


def _build_zip() -> bytes:
    buffer = io.BytesIO()
    manifest = {
        "version": "1.0",
        "sdkVersion": "1.0.0",
        "createdAt": "2026-01-01T00:00:00+00:00",
        "projects": {
            "demo-project": {
                "languages": ["en", "de"],
                "status": "synced",
            }
        },
    }
    locales_wrapper = {
        "cachedAt": "2026-01-01T00:00:00+00:00",
        "expiresAt": None,
        "data": {"locales": ["en", "de"]},
    }
    en_project = {
        "cachedAt": "2026-01-01T00:00:00+00:00",
        "expiresAt": None,
        "data": {"common": {"hello": "Hello"}},
    }
    de_project = {
        "cachedAt": "2026-01-01T00:00:00+00:00",
        "expiresAt": None,
        "data": {"common": {"hello": "Hallo"}},
    }
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("demo-project/locales.json", json.dumps(locales_wrapper))
        archive.writestr("demo-project/en/project.json", json.dumps(en_project))
        archive.writestr("demo-project/de/project.json", json.dumps(de_project))
    return buffer.getvalue()


def test_parse_offline_zip() -> None:
    bundle = parse_offline_zip(_build_zip())
    assert isinstance(bundle, OfflineBundle)
    assert bundle.manifest.get("version") == "1.0"
    assert "demo-project" in bundle.locales_by_project
    assert bundle.locales_by_project["demo-project"].locales == ["en", "de"]
    assert bundle.projects_by_project_lang["demo-project"]["en"].groups["common"]["hello"] == "Hello"
    assert bundle.projects_by_project_lang["demo-project"]["de"].groups["common"]["hello"] == "Hallo"


def test_parse_offline_zip_empty_raises() -> None:
    with pytest.raises(ValueError):
        parse_offline_zip(b"")


def test_resolve_project_key() -> None:
    bundle = parse_offline_zip(_build_zip())
    assert resolve_project_key(bundle, "demo-project") == "demo-project"

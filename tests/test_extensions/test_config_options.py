"""Tests for extended framework configuration helpers."""

import os
from unittest.mock import patch

import pytest

from translaas.extensions.config import build_translaas_options, from_env
from translaas.models.enums import OfflineFallbackMode


def test_build_translaas_options_sdk_fields() -> None:
    options = build_translaas_options(
        {
            "api_key": "key",
            "base_url": "https://api.example.com",
            "default_project": "my-project",
            "channel": "beta",
            "snapshot_version": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "include_context": "true",
            "use_conditional_requests": "1",
            "offline_cache_enabled": "true",
            "offline_cache_directory": ".cache",
            "offline_fallback_mode": "CACHE_ONLY",
            "offline_default_project_id": "my-project",
        }
    )
    assert options.default_project == "my-project"
    assert options.channel == "beta"
    assert options.snapshot_version == "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    assert options.include_context is True
    assert options.use_conditional_requests is True
    assert options.offline_cache is not None
    assert options.offline_cache.enabled is True
    assert options.offline_cache.fallback_mode == OfflineFallbackMode.CACHE_ONLY


def test_from_env_reads_extended_variables() -> None:
    env = {
        "TRANSLAAS_API_KEY": "key",
        "TRANSLAAS_BASE_URL": "https://api.example.com",
        "TRANSLAAS_DEFAULT_PROJECT": "proj",
        "TRANSLAAS_CHANNEL": "stable",
        "TRANSLAAS_OFFLINE_CACHE_ENABLED": "true",
        "TRANSLAAS_OFFLINE_FALLBACK_MODE": "API_FIRST",
    }
    with patch.dict(os.environ, env, clear=False):
        options = from_env()
    assert options.default_project == "proj"
    assert options.channel == "stable"
    assert options.offline_cache is not None
    assert options.offline_cache.fallback_mode == OfflineFallbackMode.API_FIRST


def test_build_translaas_options_requires_api_key() -> None:
    with pytest.raises(ValueError):
        build_translaas_options({"base_url": "https://api.example.com"})

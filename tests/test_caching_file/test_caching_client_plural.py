"""Cache-only/cache-first get_entry CLDR plural selection."""

from __future__ import annotations

from typing import Dict, Optional
from unittest.mock import AsyncMock

import pytest

from tests.test_i18n.plural_table_data import GOLDEN_GET_ENTRY_ROWS
from translaas.caching_file.caching_client import CachingTranslaasClient
from translaas.models.enums import OfflineFallbackMode, PluralCategory
from translaas.models.options import OfflineCacheOptions
from translaas.models.responses import TranslationGroup, TranslationProject
from translaas.models.sdk_payloads import ValidateApiKeyResult

DEFAULT_PROJECT = "test-project"

_DEFAULT_PLURAL_FORMS = {
    category.value: f"FORM:{category.value}" for category in PluralCategory
}


class _MockOfflineCache:
    def __init__(self) -> None:
        self.groups: Dict[str, TranslationGroup] = {}
        self.projects: Dict[str, TranslationProject] = {}
        self.locales: Dict[str, object] = {}

    def get_group(self, project: str, group: str, lang: str) -> Optional[TranslationGroup]:
        return self.groups.get(f"{project}:{group}:{lang}")

    def get_project(self, project: str, lang: str) -> Optional[TranslationProject]:
        return self.projects.get(f"{project}:{lang}")

    def get_project_locales(self, project: str):
        return self.locales.get(project)

    def save_project(self, project: str, lang: str, data: TranslationProject) -> None:
        pass

    def save_project_locales(self, project: str, locales) -> None:
        pass

    def is_cached(self, project: str, lang: str) -> bool:
        return False

    def clear_all(self) -> None:
        pass

    def clear_project(self, project: str) -> None:
        pass

    def get_manifest(self):
        from translaas.caching_file.offline_models import CacheManifest

        return CacheManifest()


@pytest.fixture
def inner_client() -> AsyncMock:
    client = AsyncMock()
    client.get_entry = AsyncMock(return_value="from-api")
    client.get_group = AsyncMock(return_value=TranslationGroup(entries={}))
    client.get_project = AsyncMock()
    client.get_project_locales = AsyncMock()
    client.report_missing_keys = AsyncMock()
    client.get_offline_cache = AsyncMock()
    client.validate_api_key = AsyncMock(
        return_value=ValidateApiKeyResult(
            is_valid=True,
            tenant_id="tenant",
            project_id=None,
            project_ids=(),
            default_project_id=None,
            integration_name=None,
            authenticated_at=None,
        )
    )
    return client


@pytest.fixture
def offline_options() -> OfflineCacheOptions:
    return OfflineCacheOptions(enabled=True, default_project_id=DEFAULT_PROJECT)


def _create_client(
    inner_client: AsyncMock,
    cache: _MockOfflineCache,
    mode: OfflineFallbackMode,
    options: OfflineCacheOptions,
) -> CachingTranslaasClient:
    options.fallback_mode = mode
    return CachingTranslaasClient(inner_client, cache, options, DEFAULT_PROJECT)


def _plural_group(lang: str, forms: Optional[dict[str, str]] = None) -> _MockOfflineCache:
    cache = _MockOfflineCache()
    cache.groups[f"{DEFAULT_PROJECT}:messages:{lang}"] = TranslationGroup(
        entries={"items": dict(forms or _DEFAULT_PLURAL_FORMS)}
    )
    return cache


@pytest.mark.asyncio
@pytest.mark.parametrize("lang,number,expected", GOLDEN_GET_ENTRY_ROWS)
async def test_get_entry_cache_only_returns_form_for_cldr_category(
    inner_client: AsyncMock,
    offline_options: OfflineCacheOptions,
    lang: str,
    number: float,
    expected: str,
) -> None:
    cache = _plural_group(lang)
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_ONLY, offline_options)
    result = await client.get_entry("messages", "items", lang, number=number)
    assert result == expected
    inner_client.get_entry.assert_not_called()


@pytest.mark.asyncio
async def test_get_entry_cache_only_falls_back_to_other_when_category_missing(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _plural_group("ar", {"other": "FORM:other-only"})
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_ONLY, offline_options)
    result = await client.get_entry("messages", "items", "ar", number=2)
    assert result == "FORM:other-only"


@pytest.mark.asyncio
async def test_get_entry_cache_only_null_number_uses_other_form(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _plural_group("en")
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_ONLY, offline_options)
    result = await client.get_entry("messages", "items", "en", number=None)
    assert result == "FORM:other"


@pytest.mark.asyncio
async def test_get_entry_cache_only_substitutes_n_on_plural(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _plural_group("en", {"other": "Count {N}"})
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_ONLY, offline_options)
    result = await client.get_entry("messages", "items", "en", number=0)
    assert result == "Count 0"


@pytest.mark.asyncio
async def test_get_entry_cache_only_non_plural_unchanged(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _MockOfflineCache()
    cache.groups[f"{DEFAULT_PROJECT}:common:en"] = TranslationGroup(
        entries={"hello": "Hello World"}
    )
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_ONLY, offline_options)
    result = await client.get_entry("common", "hello", "en", number=5)
    assert result == "Hello World"


@pytest.mark.asyncio
async def test_get_entry_cache_first_cldr_plural_on_hit(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _plural_group("pl")
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_FIRST, offline_options)
    result = await client.get_entry("messages", "items", "pl", number=2)
    assert result == "FORM:few"
    inner_client.get_entry.assert_not_called()


@pytest.mark.asyncio
async def test_get_entry_cache_first_pt_pt_rules(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _plural_group("pt-PT")
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_FIRST, offline_options)
    result = await client.get_entry("messages", "items", "pt-PT", number=0)
    assert result == "FORM:other"

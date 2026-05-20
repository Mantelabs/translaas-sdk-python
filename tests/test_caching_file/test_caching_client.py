"""Tests for CachingTranslaasClient offline fallback modes."""

from __future__ import annotations

from typing import Dict, Optional
from unittest.mock import AsyncMock

import httpx
import pytest

from translaas.caching_file.caching_client import CachingTranslaasClient
from translaas.exceptions import TranslaasOfflineCacheMissException
from translaas.models.enums import OfflineFallbackMode
from translaas.models.options import OfflineCacheOptions
from translaas.models.responses import TranslationGroup, TranslationProject
from translaas.models.sdk_payloads import ValidateApiKeyResult

DEFAULT_PROJECT = "test-project"


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


@pytest.mark.asyncio
async def test_get_entry_cache_first_returns_cached(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _MockOfflineCache()
    cache.groups[f"{DEFAULT_PROJECT}:common:en"] = TranslationGroup(
        entries={"hello": "Hello World"}
    )
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_FIRST, offline_options)
    result = await client.get_entry("common", "hello", "en")
    assert result == "Hello World"
    inner_client.get_entry.assert_not_called()


@pytest.mark.asyncio
async def test_get_entry_cache_first_calls_api_on_miss(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _MockOfflineCache()
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_FIRST, offline_options)
    result = await client.get_entry("common", "hello", "en")
    assert result == "from-api"
    inner_client.get_entry.assert_called_once()


@pytest.mark.asyncio
async def test_get_entry_cache_first_raises_on_api_failure(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _MockOfflineCache()
    inner_client.get_entry.side_effect = httpx.ConnectError("network")
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_FIRST, offline_options)
    with pytest.raises(TranslaasOfflineCacheMissException):
        await client.get_entry("common", "hello", "en")


@pytest.mark.asyncio
async def test_get_entry_api_first_falls_back_to_cache(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _MockOfflineCache()
    cache.groups[f"{DEFAULT_PROJECT}:common:en"] = TranslationGroup(
        entries={"hello": "Hello from Cache"}
    )
    inner_client.get_entry.side_effect = httpx.ConnectError("network")
    client = _create_client(inner_client, cache, OfflineFallbackMode.API_FIRST, offline_options)
    result = await client.get_entry("common", "hello", "en")
    assert result == "Hello from Cache"


@pytest.mark.asyncio
async def test_get_entry_cache_only_never_calls_api(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _MockOfflineCache()
    cache.groups[f"{DEFAULT_PROJECT}:common:en"] = TranslationGroup(entries={"hello": "Cached"})
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_ONLY, offline_options)
    result = await client.get_entry("common", "hello", "en")
    assert result == "Cached"
    inner_client.get_entry.assert_not_called()


@pytest.mark.asyncio
async def test_get_entry_plural_from_cache(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _MockOfflineCache()
    cache.groups[f"{DEFAULT_PROJECT}:items:en"] = TranslationGroup(
        entries={"count": {"one": "1 item", "other": "{N} items"}}
    )
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_ONLY, offline_options)
    one = await client.get_entry("items", "count", "en", number=1)
    other = await client.get_entry("items", "count", "en", number=5)
    assert one == "1 item"
    assert other == "5 items"


@pytest.mark.asyncio
async def test_get_group_cache_first_from_cache(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _MockOfflineCache()
    cache.groups["demo:common:en"] = TranslationGroup(entries={"hello": "Hi"})
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_FIRST, offline_options)
    group = await client.get_group("demo", "common", "en")
    assert group.get_value("hello") == "Hi"
    inner_client.get_group.assert_not_called()


@pytest.mark.asyncio
async def test_get_project_api_only_with_backup_passthrough(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    from translaas.models.responses import TranslationProject

    project = TranslationProject(groups={"g": {"e": "v"}})
    inner_client.get_project = AsyncMock(return_value=project)
    cache = _MockOfflineCache()
    client = _create_client(
        inner_client, cache, OfflineFallbackMode.API_ONLY_WITH_BACKUP, offline_options
    )
    result = await client.get_project("demo", "en")
    assert result.groups["g"]["e"] == "v"
    inner_client.get_project.assert_called_once()


@pytest.mark.asyncio
async def test_get_project_locales_cache_only(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    from translaas.models.responses import ProjectLocales

    cache = _MockOfflineCache()
    cache.locales["demo"] = ProjectLocales(locales=["en"], project="demo")
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_ONLY, offline_options)
    locales = await client.get_project_locales("demo")
    assert locales.locales == ["en"]


@pytest.mark.asyncio
async def test_get_group_api_first_fallback(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _MockOfflineCache()
    cache.groups["demo:common:en"] = TranslationGroup(entries={"hello": "cached"})
    inner_client.get_group.side_effect = httpx.ConnectError("offline")
    client = _create_client(inner_client, cache, OfflineFallbackMode.API_FIRST, offline_options)
    group = await client.get_group("demo", "common", "en")
    assert group.get_value("hello") == "cached"


@pytest.mark.asyncio
async def test_get_group_cache_first_miss_raises(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    inner_client.get_group.side_effect = httpx.ConnectError("offline")
    cache = _MockOfflineCache()
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_FIRST, offline_options)
    with pytest.raises(TranslaasOfflineCacheMissException):
        await client.get_group("demo", "common", "en")


@pytest.mark.asyncio
async def test_get_project_cache_first_from_cache(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _MockOfflineCache()
    cache.projects["demo:en"] = TranslationProject(groups={"g": {"e": "v"}})
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_FIRST, offline_options)
    project = await client.get_project("demo", "en")
    assert project.groups["g"]["e"] == "v"


@pytest.mark.asyncio
async def test_get_project_api_first_fallback(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _MockOfflineCache()
    cache.projects["demo:en"] = TranslationProject(groups={"g": {"e": "cached"}})
    inner_client.get_project.side_effect = httpx.ConnectError("offline")
    client = _create_client(inner_client, cache, OfflineFallbackMode.API_FIRST, offline_options)
    project = await client.get_project("demo", "en")
    assert project.groups["g"]["e"] == "cached"


@pytest.mark.asyncio
async def test_get_locales_api_first_fallback(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    from translaas.models.responses import ProjectLocales

    cache = _MockOfflineCache()
    cache.locales["demo"] = ProjectLocales(locales=["en"], project="demo")
    inner_client.get_project_locales.side_effect = httpx.ConnectError("offline")
    client = _create_client(inner_client, cache, OfflineFallbackMode.API_FIRST, offline_options)
    locales = await client.get_project_locales("demo")
    assert locales.locales == ["en"]


def test_constructor_requires_arguments() -> None:
    with pytest.raises(ValueError):
        CachingTranslaasClient(None, _MockOfflineCache(), OfflineCacheOptions(), "p")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_get_entry_cache_only_missing_entry_raises(
    inner_client: AsyncMock, offline_options: OfflineCacheOptions
) -> None:
    cache = _MockOfflineCache()
    cache.groups[f"{DEFAULT_PROJECT}:common:en"] = TranslationGroup(entries={})
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_ONLY, offline_options)
    with pytest.raises(TranslaasOfflineCacheMissException):
        await client.get_entry("common", "missing", "en")


@pytest.mark.asyncio
async def test_pass_through_methods(inner_client: AsyncMock, offline_options: OfflineCacheOptions) -> None:
    cache = _MockOfflineCache()
    client = _create_client(inner_client, cache, OfflineFallbackMode.CACHE_ONLY, offline_options)
    await client.report_missing_keys([])
    inner_client.report_missing_keys.assert_called_once()
    await client.validate_api_key()
    inner_client.validate_api_key.assert_called_once()

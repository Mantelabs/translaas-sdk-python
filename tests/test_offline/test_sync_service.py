"""Tests for OfflineCacheSyncService."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from translaas.caching_file.file_cache import FileCacheProvider
from translaas.models.options import OfflineCacheOptions
from translaas.models.responses import OfflineCacheDownloadResult, ProjectLocales, TranslationProject
from translaas.offline.sync_service import OfflineCacheSyncService

from .test_zip_bundle import _build_zip


@pytest.mark.asyncio
async def test_sync_project_validation() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        service = OfflineCacheSyncService(AsyncMock(), FileCacheProvider(tmpdir), OfflineCacheOptions())
        with pytest.raises(ValueError):
            await service.sync_project("", "en")


@pytest.mark.asyncio
async def test_sync_project() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = FileCacheProvider(tmpdir)
        client = AsyncMock()
        client.get_project = AsyncMock(
            return_value=TranslationProject(groups={"common": {"hello": "Hi"}})
        )
        options = OfflineCacheOptions(enabled=True, cache_directory=tmpdir)
        service = OfflineCacheSyncService(client, cache, options)
        await service.sync_project("demo", "en")
        stored = cache.get_project("demo", "en")
        assert stored is not None
        assert stored.groups["common"]["hello"] == "Hi"


@pytest.mark.asyncio
async def test_sync_project_all_languages() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = FileCacheProvider(tmpdir)
        client = AsyncMock()
        client.get_project_locales = AsyncMock(
            return_value=ProjectLocales(locales=["en", "de"], project="demo")
        )
        client.get_project = AsyncMock(
            side_effect=[
                TranslationProject(groups={"g": {"e_en": "EN"}}),
                TranslationProject(groups={"g": {"e_de": "DE"}}),
            ]
        )
        options = OfflineCacheOptions(enabled=True, cache_directory=tmpdir)
        service = OfflineCacheSyncService(client, cache, options)
        await service.sync_project_all_languages("demo")
        assert cache.get_project_locales("demo") is not None
        assert cache.get_project("demo", "en") is not None
        assert cache.get_project("demo", "de") is not None


@pytest.mark.asyncio
async def test_sync_all_uses_configured_projects() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = FileCacheProvider(tmpdir)
        client = AsyncMock()
        client.get_project_locales = AsyncMock(
            return_value=ProjectLocales(locales=["en"], project="demo")
        )
        client.get_project = AsyncMock(
            return_value=TranslationProject(groups={"g": {"e": "v"}})
        )
        options = OfflineCacheOptions(
            enabled=True, cache_directory=tmpdir, projects=["demo"]
        )
        service = OfflineCacheSyncService(client, cache, options)
        await service.sync_all()
        assert cache.get_project("demo", "en") is not None


@pytest.mark.asyncio
async def test_sync_from_offline_zip() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = FileCacheProvider(tmpdir)
        client = AsyncMock()
        client.get_offline_cache = AsyncMock(
            return_value=OfflineCacheDownloadResult(content=_build_zip())
        )
        options = OfflineCacheOptions(enabled=True, cache_directory=tmpdir)
        service = OfflineCacheSyncService(client, cache, options)
        await service.sync_from_offline_zip("demo-project")
        assert cache.get_project("demo-project", "en") is not None
        assert cache.get_project_locales("demo-project") is not None

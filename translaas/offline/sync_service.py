"""Synchronize on-disk offline cache with the Translaas API."""

from __future__ import annotations

import asyncio
from typing import Optional

from translaas.caching_file.file_cache import FileCacheProvider
from translaas.caching_file.offline_protocol import IOfflineCacheProvider
from translaas.models.options import OfflineCacheOptions
from translaas.models.protocols import ITranslaasClient
from translaas.models.responses import OfflineCacheDownloadResult
from translaas.offline.zip_bundle import parse_offline_zip, resolve_project_key


class OfflineCacheSyncService:
    """Pull translations from the API (or ZIP) into the offline file cache."""

    def __init__(
        self,
        client: ITranslaasClient,
        cache_provider: IOfflineCacheProvider,
        options: OfflineCacheOptions,
    ) -> None:
        if client is None:
            raise ValueError("client is required")
        if cache_provider is None:
            raise ValueError("cache_provider is required")
        if options is None:
            raise ValueError("options is required")
        self._client = client
        self._cache = cache_provider
        self._options = options
        self._lock = asyncio.Lock()
        self._background_task: Optional[asyncio.Task[None]] = None
        self._background_stop = asyncio.Event()

    @property
    def is_background_sync_running(self) -> bool:
        return self._background_task is not None and not self._background_task.done()

    async def sync_project(self, project: str, lang: str) -> None:
        if not project or not str(project).strip():
            raise ValueError("project is required")
        if not lang or not str(lang).strip():
            raise ValueError("lang is required")
        async with self._lock:
            project_data = await self._client.get_project(project, lang)
            self._cache.save_project(project, lang, project_data)

    async def sync_project_all_languages(self, project: str) -> None:
        if not project or not str(project).strip():
            raise ValueError("project is required")
        async with self._lock:
            locales = await self._client.get_project_locales(project)
            self._cache.save_project_locales(project, locales)
            languages = (
                _filter_languages(locales.locales, self._options.languages)
                if self._options.languages
                else list(locales.locales)
            )
            for lang in languages:
                try:
                    project_data = await self._client.get_project(project, lang)
                    self._cache.save_project(project, lang, project_data)
                except Exception:
                    continue

    async def sync_from_offline_zip(self, project: str) -> None:
        """Download the offline ZIP for ``project`` and persist it to disk."""
        result: OfflineCacheDownloadResult = await self._client.get_offline_cache(project)
        if result.not_modified or not result.content:
            return
        bundle = parse_offline_zip(result.content)
        key = resolve_project_key(bundle, project)
        locales = bundle.locales_by_project.get(key)
        projects_by_lang = bundle.projects_by_project_lang.get(key, {})
        if isinstance(self._cache, FileCacheProvider):
            self._cache.apply_offline_bundle(project, locales, projects_by_lang)
        else:
            if locales is not None:
                self._cache.save_project_locales(project, locales)
            for lang, data in projects_by_lang.items():
                self._cache.save_project(project, lang, data)

    async def sync_all(self) -> None:
        for project in self._options.projects:
            try:
                await self.sync_project_all_languages(project)
            except Exception:
                continue

    async def start_background_sync(self) -> None:
        if self.is_background_sync_running:
            return
        if not self._options.auto_sync or self._options.auto_sync_interval is None:
            return
        self._background_stop.clear()
        self._background_task = asyncio.create_task(self._background_loop())

    async def stop_background_sync(self) -> None:
        if self._background_task is None:
            return
        self._background_stop.set()
        try:
            await self._background_task
        except asyncio.CancelledError:
            pass
        finally:
            self._background_task = None

    async def _background_loop(self) -> None:
        interval = self._options.auto_sync_interval
        if interval is None:
            return
        seconds = interval.total_seconds()
        while not self._background_stop.is_set():
            try:
                await self.sync_all()
            except Exception:
                pass
            try:
                await asyncio.wait_for(self._background_stop.wait(), timeout=seconds)
            except asyncio.TimeoutError:
                continue


def _filter_languages(available: list[str], configured: list[str]) -> list[str]:
    configured_set = {lang.lower() for lang in configured}
    return [lang for lang in available if lang.lower() in configured_set]

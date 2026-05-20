"""Decorator client that adds offline cache fallback modes."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import httpx

from translaas.caching_file.offline_protocol import IOfflineCacheProvider
from translaas.exceptions import (
    TranslaasApiException,
    TranslaasOfflineCacheMissException,
)
from translaas.i18n.parameter_replacer import ParameterReplacer
from translaas.i18n.plural_resolver import PluralResolver
from translaas.models.enums import OfflineFallbackMode, PluralCategory
from translaas.models.options import OfflineCacheOptions
from translaas.models.protocols import ITranslaasClient
from translaas.models.request_context import TranslaasRequestContext
from translaas.models.responses import (
    OfflineCacheDownloadResult,
    ProjectLocales,
    TranslationGroup,
    TranslationProject,
)
from translaas.models.sdk_payloads import ReportMissingKeyItem, ValidateApiKeyResult


def _offline_cache_miss(
    project: str,
    language: str,
    *,
    group: Optional[str] = None,
    entry: Optional[str] = None,
) -> TranslaasOfflineCacheMissException:
    if entry and group:
        message = (
            f"Translation entry '{entry}' in group '{group}' for project '{project}' "
            f"and language '{language}' was not found in the offline cache."
        )
    elif group:
        message = (
            f"Translation group '{group}' for project '{project}' and language '{language}' "
            f"was not found in the offline cache."
        )
    else:
        message = (
            f"Project '{project}' for language '{language}' was not found in the offline cache."
        )
    return TranslaasOfflineCacheMissException(message)


def _is_network_or_api_error(exc: BaseException) -> bool:
    return isinstance(
        exc,
        (
            httpx.HTTPError,
            httpx.TimeoutException,
            asyncio.TimeoutError,
            TranslaasApiException,
        ),
    )


class CachingTranslaasClient(ITranslaasClient):
    """Wraps a client with offline cache orchestration."""

    def __init__(
        self,
        inner_client: ITranslaasClient,
        cache_provider: IOfflineCacheProvider,
        options: OfflineCacheOptions,
        project_id: str,
    ) -> None:
        if inner_client is None:
            raise ValueError("inner_client is required")
        if cache_provider is None:
            raise ValueError("cache_provider is required")
        if options is None:
            raise ValueError("options is required")
        if not project_id or not str(project_id).strip():
            raise ValueError("project_id is required")
        self._inner = inner_client
        self._cache = cache_provider
        self._options = options
        self._project_id = project_id

    async def __aenter__(self) -> "CachingTranslaasClient":
        enter = getattr(self._inner, "__aenter__", None)
        if enter is not None:
            await enter()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        exit_fn = getattr(self._inner, "__aexit__", None)
        if exit_fn is not None:
            await exit_fn(exc_type, exc_val, exc_tb)

    async def get_entry(
        self,
        group: str,
        entry: str,
        lang: str,
        number: Optional[float] = None,
        parameters: Optional[Dict[str, str]] = None,
        *,
        project: Optional[str] = None,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> str:
        del project, channel, snapshot_version
        mode = self._options.fallback_mode
        if mode == OfflineFallbackMode.CACHE_FIRST:
            return await self._get_entry_cache_first(
                group, entry, lang, number, parameters, request_context
            )
        if mode == OfflineFallbackMode.API_FIRST:
            return await self._get_entry_api_first(
                group, entry, lang, number, parameters, request_context
            )
        if mode == OfflineFallbackMode.CACHE_ONLY:
            return await self._get_entry_cache_only(group, entry, lang, number, parameters)
        return await self._inner.get_entry(
            group,
            entry,
            lang,
            number=number,
            parameters=parameters,
            project=self._project_id,
            request_context=request_context,
        )

    async def get_group(
        self,
        project: str,
        group: str,
        lang: str,
        format: Optional[str] = None,
        *,
        include_context: Optional[bool] = None,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> TranslationGroup:
        mode = self._options.fallback_mode
        if mode == OfflineFallbackMode.CACHE_FIRST:
            return await self._get_group_cache_first(
                project,
                group,
                lang,
                format,
                include_context,
                channel,
                snapshot_version,
                request_context,
            )
        if mode == OfflineFallbackMode.API_FIRST:
            return await self._get_group_api_first(
                project,
                group,
                lang,
                format,
                include_context,
                channel,
                snapshot_version,
                request_context,
            )
        if mode == OfflineFallbackMode.CACHE_ONLY:
            return await self._get_group_cache_only(project, group, lang)
        return await self._inner.get_group(
            project,
            group,
            lang,
            format,
            include_context=include_context,
            channel=channel,
            snapshot_version=snapshot_version,
            request_context=request_context,
        )

    async def get_project(
        self,
        project: str,
        lang: str,
        format: Optional[str] = None,
        *,
        include_context: Optional[bool] = None,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> TranslationProject:
        mode = self._options.fallback_mode
        if mode == OfflineFallbackMode.CACHE_FIRST:
            return await self._get_project_cache_first(
                project,
                lang,
                format,
                include_context,
                channel,
                snapshot_version,
                request_context,
            )
        if mode == OfflineFallbackMode.API_FIRST:
            return await self._get_project_api_first(
                project,
                lang,
                format,
                include_context,
                channel,
                snapshot_version,
                request_context,
            )
        if mode == OfflineFallbackMode.CACHE_ONLY:
            return await self._get_project_cache_only(project, lang)
        return await self._inner.get_project(
            project,
            lang,
            format,
            include_context=include_context,
            channel=channel,
            snapshot_version=snapshot_version,
            request_context=request_context,
        )

    async def get_project_locales(
        self,
        project: str,
        *,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> ProjectLocales:
        mode = self._options.fallback_mode
        if mode == OfflineFallbackMode.CACHE_FIRST:
            return await self._get_locales_cache_first(
                project, channel, snapshot_version, request_context
            )
        if mode == OfflineFallbackMode.API_FIRST:
            return await self._get_locales_api_first(
                project, channel, snapshot_version, request_context
            )
        if mode == OfflineFallbackMode.CACHE_ONLY:
            return await self._get_locales_cache_only(project)
        return await self._inner.get_project_locales(
            project,
            channel=channel,
            snapshot_version=snapshot_version,
            request_context=request_context,
        )

    async def report_missing_keys(self, keys: list[ReportMissingKeyItem]) -> None:
        await self._inner.report_missing_keys(keys)

    async def get_offline_cache(
        self,
        project: str,
        *,
        include_context: Optional[bool] = None,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> OfflineCacheDownloadResult:
        return await self._inner.get_offline_cache(
            project,
            include_context=include_context,
            channel=channel,
            snapshot_version=snapshot_version,
            request_context=request_context,
        )

    async def validate_api_key(self) -> ValidateApiKeyResult:
        return await self._inner.validate_api_key()

    # --- Entry modes ---

    async def _get_entry_cache_first(
        self,
        group: str,
        entry: str,
        lang: str,
        number: Optional[float],
        parameters: Optional[Dict[str, str]],
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> str:
        cached_group = self._cache.get_group(self._project_id, group, lang)
        resolved = self._resolve_entry_from_group(cached_group, entry, lang, number, parameters)
        if resolved is not None:
            return resolved
        try:
            result = await self._inner.get_entry(
                group,
                entry,
                lang,
                number=number,
                parameters=parameters,
                project=self._project_id,
                request_context=request_context,
            )
            try:
                await self._update_group_cache(self._project_id, group, lang)
            except Exception:
                pass
            return result
        except Exception as ex:
            if _is_network_or_api_error(ex):
                raise _offline_cache_miss(self._project_id, lang, group=group, entry=entry) from ex
            raise

    async def _get_entry_api_first(
        self,
        group: str,
        entry: str,
        lang: str,
        number: Optional[float],
        parameters: Optional[Dict[str, str]],
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> str:
        try:
            result = await self._inner.get_entry(
                group,
                entry,
                lang,
                number=number,
                parameters=parameters,
                project=self._project_id,
                request_context=request_context,
            )
            try:
                await self._update_group_cache(self._project_id, group, lang)
            except Exception:
                pass
            return result
        except Exception as ex:
            if not _is_network_or_api_error(ex):
                raise
            cached_group = self._cache.get_group(self._project_id, group, lang)
            resolved = self._resolve_entry_from_group(
                cached_group, entry, lang, number, parameters
            )
            if resolved is not None:
                return resolved
            raise _offline_cache_miss(self._project_id, lang, group=group, entry=entry) from ex

    async def _get_entry_cache_only(
        self,
        group: str,
        entry: str,
        lang: str,
        number: Optional[float],
        parameters: Optional[Dict[str, str]],
    ) -> str:
        cached_group = self._cache.get_group(self._project_id, group, lang)
        resolved = self._resolve_entry_from_group(cached_group, entry, lang, number, parameters)
        if resolved is not None:
            return resolved
        raise _offline_cache_miss(self._project_id, lang, group=group, entry=entry)

    def _resolve_entry_from_group(
        self,
        group: Optional[TranslationGroup],
        entry: str,
        lang: str,
        number: Optional[float],
        parameters: Optional[Dict[str, str]],
    ) -> Optional[str]:
        if group is None:
            return None
        template: Optional[str] = None
        if group.has_plural_forms(entry):
            category = PluralResolver.resolve_category(number or 0, lang)
            template = group.get_plural_form(entry, category)
            if template is None and category != PluralCategory.OTHER:
                template = group.get_plural_form(entry, PluralCategory.OTHER)
        else:
            template = group.get_value(entry)
        if template is None:
            return None
        return ParameterReplacer.replace(template, parameters, number=number)

    # --- Group modes ---

    async def _get_group_cache_first(
        self,
        project: str,
        group: str,
        lang: str,
        format: Optional[str],
        include_context: Optional[bool],
        channel: Optional[str],
        snapshot_version: Optional[str],
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> TranslationGroup:
        cached = self._cache.get_group(project, group, lang)
        if cached is not None:
            return cached
        try:
            result = await self._inner.get_group(
                project,
                group,
                lang,
                format,
                include_context=include_context,
                channel=channel,
                snapshot_version=snapshot_version,
                request_context=request_context,
            )
            asyncio.create_task(self._update_group_cache(project, group, lang))
            return result
        except Exception as ex:
            if _is_network_or_api_error(ex):
                raise _offline_cache_miss(project, lang, group=group) from ex
            raise

    async def _get_group_api_first(
        self,
        project: str,
        group: str,
        lang: str,
        format: Optional[str],
        include_context: Optional[bool],
        channel: Optional[str],
        snapshot_version: Optional[str],
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> TranslationGroup:
        try:
            result = await self._inner.get_group(
                project,
                group,
                lang,
                format,
                include_context=include_context,
                channel=channel,
                snapshot_version=snapshot_version,
                request_context=request_context,
            )
            asyncio.create_task(self._update_group_cache(project, group, lang))
            return result
        except Exception as ex:
            if not _is_network_or_api_error(ex):
                raise
            cached = self._cache.get_group(project, group, lang)
            if cached is not None:
                return cached
            raise _offline_cache_miss(project, lang, group=group) from ex

    async def _get_group_cache_only(self, project: str, group: str, lang: str) -> TranslationGroup:
        cached = self._cache.get_group(project, group, lang)
        if cached is not None:
            return cached
        raise _offline_cache_miss(project, lang, group=group)

    # --- Project modes ---

    async def _get_project_cache_first(
        self,
        project: str,
        lang: str,
        format: Optional[str],
        include_context: Optional[bool],
        channel: Optional[str],
        snapshot_version: Optional[str],
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> TranslationProject:
        cached = self._cache.get_project(project, lang)
        if cached is not None:
            return cached
        try:
            result = await self._inner.get_project(
                project,
                lang,
                format,
                include_context=include_context,
                channel=channel,
                snapshot_version=snapshot_version,
                request_context=request_context,
            )
            asyncio.create_task(self._update_project_cache(project, lang))
            return result
        except Exception as ex:
            if _is_network_or_api_error(ex):
                raise _offline_cache_miss(project, lang) from ex
            raise

    async def _get_project_api_first(
        self,
        project: str,
        lang: str,
        format: Optional[str],
        include_context: Optional[bool],
        channel: Optional[str],
        snapshot_version: Optional[str],
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> TranslationProject:
        try:
            result = await self._inner.get_project(
                project,
                lang,
                format,
                include_context=include_context,
                channel=channel,
                snapshot_version=snapshot_version,
                request_context=request_context,
            )
            asyncio.create_task(self._update_project_cache(project, lang))
            return result
        except Exception as ex:
            if not _is_network_or_api_error(ex):
                raise
            cached = self._cache.get_project(project, lang)
            if cached is not None:
                return cached
            raise _offline_cache_miss(project, lang) from ex

    async def _get_project_cache_only(self, project: str, lang: str) -> TranslationProject:
        cached = self._cache.get_project(project, lang)
        if cached is not None:
            return cached
        raise _offline_cache_miss(project, lang)

    # --- Locales modes ---

    async def _get_locales_cache_first(
        self,
        project: str,
        channel: Optional[str],
        snapshot_version: Optional[str],
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> ProjectLocales:
        cached = self._cache.get_project_locales(project)
        if cached is not None:
            return cached
        try:
            result = await self._inner.get_project_locales(
                project,
                channel=channel,
                snapshot_version=snapshot_version,
                request_context=request_context,
            )
            self._cache.save_project_locales(project, result)
            return result
        except Exception as ex:
            if _is_network_or_api_error(ex):
                raise _offline_cache_miss(project, lang="*") from ex
            raise

    async def _get_locales_api_first(
        self,
        project: str,
        channel: Optional[str],
        snapshot_version: Optional[str],
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> ProjectLocales:
        try:
            result = await self._inner.get_project_locales(
                project,
                channel=channel,
                snapshot_version=snapshot_version,
                request_context=request_context,
            )
            self._cache.save_project_locales(project, result)
            return result
        except Exception as ex:
            if not _is_network_or_api_error(ex):
                raise
            cached = self._cache.get_project_locales(project)
            if cached is not None:
                return cached
            raise _offline_cache_miss(project, lang="*") from ex

    async def _get_locales_cache_only(self, project: str) -> ProjectLocales:
        cached = self._cache.get_project_locales(project)
        if cached is not None:
            return cached
        raise _offline_cache_miss(project, lang="*")

    # --- Cache writers ---

    async def _update_group_cache(self, project: str, group: str, lang: str) -> None:
        group_data = await self._inner.get_group(project, group, lang)
        existing = self._cache.get_project(project, lang)
        if existing is not None:
            existing.groups[group] = dict(group_data.entries)
            if group_data.entry_context:
                ctx = existing.group_entry_context or {}
                ctx[group] = group_data.entry_context
                existing.group_entry_context = ctx
            project_to_save = existing
        else:
            project_to_save = TranslationProject(groups={group: dict(group_data.entries)})
        self._cache.save_project(project, lang, project_to_save)

    async def _update_project_cache(self, project: str, lang: str) -> None:
        project_data = await self._inner.get_project(project, lang)
        self._cache.save_project(project, lang, project_data)

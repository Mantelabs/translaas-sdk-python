"""Core HTTP client implementation for the Translaas SDK."""

from __future__ import annotations

import asyncio
import json
from datetime import timedelta
from email.utils import decode_rfc2231
from typing import Any, Dict, Optional

import httpx

from translaas.caching.cache_key_builder import CacheKeyBuilder
from translaas.client.parsing import (
    project_locales_from_response,
    translation_group_from_response,
    translation_project_from_response,
)
from translaas.client.text_query import build_text_query_params
from translaas.exceptions import (
    TranslaasApiException,
    TranslaasConfigurationException,
    create_api_exception_from_httpx_error,
)
from translaas.models.enums import CacheMode
from translaas.models.options import TranslaasOptions
from translaas.models.protocols import ITranslaasCacheProvider, ITranslaasClient
from translaas.models.request_context import (
    SdkTranslationQueryParams,
    TranslaasRequestContext,
    assign_response_context,
    context_to_sdk_query,
    merge_sdk_query,
    prepare_request_context,
    sdk_query_to_params,
)
from translaas.models.responses import (
    OfflineCacheDownloadResult,
    ProjectLocales,
    TranslationGroup,
    TranslationProject,
)
from translaas.models.sdk_payloads import (
    ReportMissingKeyItem,
    ValidateApiKeyResult,
    report_missing_keys_body,
)

_PATH_VALIDATE_KEY = "api/v1/api-keys/validate"


def _response_etag(response: httpx.Response) -> Optional[str]:
    return response.headers.get("etag") or response.headers.get("ETag")


def _parse_suggested_filename(response: httpx.Response) -> Optional[str]:
    cd = response.headers.get("content-disposition")
    if not cd:
        return None
    lower = cd.lower()
    if "filename*=" in lower:
        for part in cd.split(";"):
            part = part.strip()
            if part.lower().startswith("filename*="):
                value = part.split("=", 1)[1].strip().strip('"')
                if value.lower().startswith("utf-8''"):
                    return value[7:]
                decoded = decode_rfc2231(value)
                if decoded and decoded[2]:
                    return decoded[2]
                return value
    if "filename=" in lower:
        for part in cd.split(";"):
            part = part.strip()
            if part.lower().startswith("filename="):
                return part.split("=", 1)[1].strip().strip('"')
    return None


class TranslaasClient(ITranslaasClient):
    """HTTP client for the Translaas Translation Delivery API."""

    def __init__(
        self,
        options: TranslaasOptions,
        cache_provider: Optional[ITranslaasCacheProvider] = None,
    ) -> None:
        if not options.api_key or not options.base_url:
            raise TranslaasConfigurationException(
                "api_key and base_url are required in TranslaasOptions"
            )

        self.options = options
        self.cache_provider = cache_provider
        self._http_client: Optional[httpx.AsyncClient] = None
        self._etag_by_resource: dict[str, str] = {}

    async def __aenter__(self) -> TranslaasClient:
        timeout: Optional[httpx.Timeout] = None
        if self.options.timeout:
            timeout_seconds = self.options.timeout.total_seconds()
            timeout = httpx.Timeout(timeout_seconds, connect=timeout_seconds)

        header_name = self.options.api_key_header.strip() or "X-Api-Key"
        self._http_client = httpx.AsyncClient(
            base_url=self.options.base_url.rstrip("/"),
            headers={header_name: self.options.api_key},
            timeout=timeout,
            verify=self.options.verify,
        )
        return self

    async def __aexit__(
        self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[object]
    ) -> None:
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            raise TranslaasConfigurationException(
                "Client must be used as async context manager or initialized manually"
            )
        return self._http_client

    def _translation_path(self, resource: str) -> str:
        prefix = self.options.sdk_translations_path_prefix.strip("/")
        return f"{prefix}/{resource.lstrip('/')}"

    def _default_sdk_query_params(self) -> SdkTranslationQueryParams:
        return SdkTranslationQueryParams(
            channel=self.options.channel,
            v=self.options.snapshot_version,
            include_context=self.options.include_context,
        )

    def _resolve_sdk_query(
        self,
        request_context: Optional[TranslaasRequestContext],
        *,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
        include_context: Optional[bool] = None,
        omit_include_context: bool = False,
    ) -> SdkTranslationQueryParams:
        base = merge_sdk_query(
            self._default_sdk_query_params(),
            self.options.default_sdk_query,
            omit_include_context=omit_include_context,
        )
        ctx_query = context_to_sdk_query(
            request_context, omit_include_context=omit_include_context
        )
        merged = merge_sdk_query(base, ctx_query, omit_include_context=omit_include_context)
        if channel is not None:
            merged.channel = channel
        if snapshot_version is not None:
            merged.v = str(snapshot_version)
        if not omit_include_context and include_context is not None:
            merged.include_context = include_context
        return merged

    def _query_channel_version(
        self, query: SdkTranslationQueryParams
    ) -> tuple[Optional[str], Optional[str], Optional[bool]]:
        return query.channel, query.v, query.include_context

    def _should_cache(self, cache_mode: CacheMode, method: str) -> bool:
        if cache_mode == CacheMode.NONE or self.cache_provider is None:
            return False
        if method == "entry":
            return cache_mode in (CacheMode.ENTRY, CacheMode.GROUP, CacheMode.PROJECT)
        if method == "group":
            return cache_mode in (CacheMode.GROUP, CacheMode.PROJECT)
        if method == "project":
            return cache_mode == CacheMode.PROJECT
        if method == "locales":
            return True
        return False

    def _get_expiration_ms(self, expiration: Optional[timedelta]) -> Optional[int]:
        if expiration is None:
            return None
        return int(expiration.total_seconds() * 1000)

    async def _send_get(
        self,
        path: str,
        params: dict[str, str],
        *,
        if_none_match: Optional[str] = None,
    ) -> httpx.Response:
        client = self._ensure_client()
        headers: dict[str, str] = {}
        if if_none_match:
            headers["If-None-Match"] = if_none_match
        try:
            return await client.get(path, params=params, headers=headers)
        except httpx.RequestError as e:
            raise create_api_exception_from_httpx_error(
                e, default_message="Failed to connect to Translaas API"
            ) from e
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise TranslaasApiException(
                f"Unexpected error during API request: {str(e)}", inner_error=e
            ) from e

    def _if_none_match_for(self, cache_key: str, context: Optional[TranslaasRequestContext]) -> Optional[str]:
        if context and context.if_none_match:
            return context.if_none_match
        if not self.options.use_conditional_requests:
            return None
        return self._etag_by_resource.get(cache_key)

    def _store_etag(self, cache_key: str, response: httpx.Response) -> None:
        etag = _response_etag(response)
        if etag:
            self._etag_by_resource[cache_key] = etag

    def _after_response(
        self,
        cache_key: str,
        response: httpx.Response,
        context: Optional[TranslaasRequestContext],
        *,
        not_modified: bool = False,
    ) -> None:
        etag = _response_etag(response)
        assign_response_context(context, etag=etag, not_modified=not_modified)
        if not not_modified and response.status_code == 200:
            self._store_etag(cache_key, response)

    async def get_entry(
        self,
        group: str,
        entry: str,
        lang: str,
        number: Optional[float] = None,
        parameters: Optional[dict[str, str]] = None,
        *,
        project: Optional[str] = None,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> str:
        """Get a single translation entry."""
        prepare_request_context(request_context)
        resolved_project = project
        if resolved_project is None and request_context and request_context.project:
            resolved_project = request_context.project
        if resolved_project is None:
            resolved_project = self.options.default_project

        sdk_query = self._resolve_sdk_query(
            request_context,
            channel=channel,
            snapshot_version=snapshot_version,
            omit_include_context=True,
        )
        ch, ver, _ = self._query_channel_version(sdk_query)

        cache_key = CacheKeyBuilder.build_entry_key(
            group,
            entry,
            lang,
            number,
            parameters,
            project=resolved_project,
            channel=ch,
            version=ver,
        )

        if self._should_cache(self.options.cache_mode, "entry") and self.cache_provider is not None:
            cached_value = self.cache_provider.get(cache_key)
            if cached_value is not None:
                return cached_value

        extra = sdk_query_to_params(sdk_query, omit_include_context=True)
        req = build_text_query_params(
            group=group,
            entry=entry,
            lang=lang,
            project=resolved_project,
            number=number,
            parameters=parameters,
            extra_query=extra,
        )

        ifnm = self._if_none_match_for(cache_key, request_context)
        response = await self._send_get(self._translation_path("text"), req, if_none_match=ifnm)

        if response.status_code == 204:
            self._after_response(cache_key, response, request_context)
            return entry

        if response.status_code == 304:
            self._after_response(cache_key, response, request_context, not_modified=True)
            if self.cache_provider is not None:
                cached_fallback = self.cache_provider.get(cache_key)
                if cached_fallback is not None:
                    return cached_fallback
            return ""

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e) from e

        self._after_response(cache_key, response, request_context)
        response_text = str(response.text)

        if self._should_cache(self.options.cache_mode, "entry") and self.cache_provider is not None:
            self.cache_provider.set(
                cache_key,
                response_text,
                absolute_expiration_ms=self._get_expiration_ms(self.options.cache_absolute_expiration),
                sliding_expiration_ms=self._get_expiration_ms(self.options.cache_sliding_expiration),
            )

        return response_text

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
        """Get a translation group."""
        prepare_request_context(request_context)
        sdk_query = self._resolve_sdk_query(
            request_context,
            channel=channel,
            snapshot_version=snapshot_version,
            include_context=include_context,
        )
        ch, ver, ic = self._query_channel_version(sdk_query)

        cache_key = CacheKeyBuilder.build_group_key(
            project, group, lang, format, channel=ch, version=ver, include_context=ic
        )

        if self._should_cache(self.options.cache_mode, "group") and self.cache_provider is not None:
            cached_value = self.cache_provider.get(cache_key)
            if cached_value is not None:
                try:
                    return translation_group_from_response(json.loads(cached_value))
                except (json.JSONDecodeError, TypeError, ValueError, TranslaasApiException):
                    pass

        req: dict[str, str] = {
            "project": project,
            "group": group,
            "lang": lang,
            **sdk_query_to_params(sdk_query),
        }
        if format:
            req["format"] = format

        ifnm = self._if_none_match_for(cache_key, request_context)
        response = await self._send_get(self._translation_path("group"), req, if_none_match=ifnm)

        if response.status_code in (204, 304):
            self._after_response(
                cache_key,
                response,
                request_context,
                not_modified=response.status_code == 304,
            )
            if response.status_code == 304 and self.cache_provider is not None:
                cached_fallback = self.cache_provider.get(cache_key)
                if cached_fallback is not None:
                    return translation_group_from_response(json.loads(cached_fallback))
            return TranslationGroup()

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e) from e

        self._after_response(cache_key, response, request_context)
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            raise TranslaasApiException(
                "Invalid JSON in group translations response",
                inner_error=e,
            ) from e
        if not isinstance(response_data, dict):
            raise TranslaasApiException(
                f"Invalid response format: expected dict, got {type(response_data).__name__}",
            )
        translation_group = translation_group_from_response(response_data)

        if self._should_cache(self.options.cache_mode, "group") and self.cache_provider is not None:
            self.cache_provider.set(
                cache_key,
                json.dumps(response_data),
                absolute_expiration_ms=self._get_expiration_ms(self.options.cache_absolute_expiration),
                sliding_expiration_ms=self._get_expiration_ms(self.options.cache_sliding_expiration),
            )

        return translation_group

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
        """Get an entire translation project."""
        prepare_request_context(request_context)
        sdk_query = self._resolve_sdk_query(
            request_context,
            channel=channel,
            snapshot_version=snapshot_version,
            include_context=include_context,
        )
        ch, ver, ic = self._query_channel_version(sdk_query)

        cache_key = CacheKeyBuilder.build_project_key(
            project, lang, format, channel=ch, version=ver, include_context=ic
        )

        if (
            self._should_cache(self.options.cache_mode, "project")
            and self.cache_provider is not None
        ):
            cached_value = self.cache_provider.get(cache_key)
            if cached_value is not None:
                try:
                    return translation_project_from_response(json.loads(cached_value), format)
                except (json.JSONDecodeError, TypeError, ValueError, TranslaasApiException):
                    pass

        req: dict[str, str] = {"project": project, "lang": lang, **sdk_query_to_params(sdk_query)}
        if format:
            req["format"] = format

        ifnm = self._if_none_match_for(cache_key, request_context)
        response = await self._send_get(self._translation_path("project"), req, if_none_match=ifnm)

        if response.status_code in (204, 304):
            self._after_response(
                cache_key,
                response,
                request_context,
                not_modified=response.status_code == 304,
            )
            if response.status_code == 304 and self.cache_provider is not None:
                cached_fallback = self.cache_provider.get(cache_key)
                if cached_fallback is not None:
                    return translation_project_from_response(json.loads(cached_fallback), format)
            return TranslationProject()

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e) from e

        self._after_response(cache_key, response, request_context)
        response_data = response.json()
        if not isinstance(response_data, dict):
            raise TranslaasApiException(
                f"Invalid response format: expected dict, got {type(response_data).__name__}",
            )
        translation_project = translation_project_from_response(response_data, format)

        if (
            self._should_cache(self.options.cache_mode, "project")
            and self.cache_provider is not None
        ):
            self.cache_provider.set(
                cache_key,
                json.dumps(response_data),
                absolute_expiration_ms=self._get_expiration_ms(self.options.cache_absolute_expiration),
                sliding_expiration_ms=self._get_expiration_ms(self.options.cache_sliding_expiration),
            )

        return translation_project

    async def get_project_locales(
        self,
        project: str,
        *,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> ProjectLocales:
        """Get the list of available locales for a project."""
        prepare_request_context(request_context)
        sdk_query = self._resolve_sdk_query(
            request_context,
            channel=channel,
            snapshot_version=snapshot_version,
            omit_include_context=True,
        )
        ch, ver, _ = self._query_channel_version(sdk_query)

        cache_key = CacheKeyBuilder.build_locales_key(project, channel=ch, version=ver)

        if (
            self._should_cache(self.options.cache_mode, "locales")
            and self.cache_provider is not None
        ):
            cached_value = self.cache_provider.get(cache_key)
            if cached_value is not None:
                try:
                    cached_raw = json.loads(cached_value)
                    if isinstance(cached_raw, list):
                        return ProjectLocales(locales=cached_raw)
                    if isinstance(cached_raw, dict):
                        return project_locales_from_response(cached_raw)
                except (json.JSONDecodeError, TypeError, ValueError, TranslaasApiException):
                    pass

        req: dict[str, str] = {"project": project, **sdk_query_to_params(sdk_query, omit_include_context=True)}

        ifnm = self._if_none_match_for(cache_key, request_context)
        response = await self._send_get(self._translation_path("locales"), req, if_none_match=ifnm)

        if response.status_code in (204, 304):
            self._after_response(
                cache_key,
                response,
                request_context,
                not_modified=response.status_code == 304,
            )
            if response.status_code == 304 and self.cache_provider is not None:
                cached_fallback = self.cache_provider.get(cache_key)
                if cached_fallback is not None:
                    raw = json.loads(cached_fallback)
                    if isinstance(raw, list):
                        return ProjectLocales(locales=raw)
                    if isinstance(raw, dict):
                        return project_locales_from_response(raw)
            return ProjectLocales()

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e) from e

        self._after_response(cache_key, response, request_context)
        response_data = response.json()
        project_locales = project_locales_from_response(response_data)

        if (
            self._should_cache(self.options.cache_mode, "locales")
            and self.cache_provider is not None
        ):
            cache_value = (
                json.dumps(response_data)
                if isinstance(response_data, dict)
                else json.dumps(project_locales.locales)
            )
            self.cache_provider.set(
                cache_key,
                cache_value,
                absolute_expiration_ms=self._get_expiration_ms(self.options.cache_absolute_expiration),
                sliding_expiration_ms=self._get_expiration_ms(self.options.cache_sliding_expiration),
            )

        return project_locales

    async def report_missing_keys(self, keys: list[ReportMissingKeyItem]) -> None:
        """Report missing translation keys."""
        if not keys:
            return
        client = self._ensure_client()
        body = report_missing_keys_body(keys)
        try:
            response = await client.post(self._translation_path("report-missing"), json=body)
            if response.status_code == 202:
                return
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e) from e
        except httpx.RequestError as e:
            raise create_api_exception_from_httpx_error(
                e, default_message="Failed to connect to Translaas API"
            ) from e
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise TranslaasApiException(
                f"Unexpected error during API request: {str(e)}", inner_error=e
            ) from e

    async def get_offline_cache(
        self,
        project: str,
        *,
        include_context: Optional[bool] = None,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
        request_context: Optional[TranslaasRequestContext] = None,
    ) -> OfflineCacheDownloadResult:
        """Download the offline ZIP bundle."""
        prepare_request_context(request_context)
        sdk_query = self._resolve_sdk_query(
            request_context,
            channel=channel,
            snapshot_version=snapshot_version,
            include_context=include_context,
        )
        ch, ver, ic = self._query_channel_version(sdk_query)

        cache_key = CacheKeyBuilder.build_offline_cache_key(
            project, channel=ch, version=ver, include_context=ic
        )
        req: dict[str, str] = {"project": project, **sdk_query_to_params(sdk_query)}

        ifnm = self._if_none_match_for(cache_key, request_context)
        response = await self._send_get(
            self._translation_path("offline-cache"), req, if_none_match=ifnm
        )

        if response.status_code == 304:
            etag = _response_etag(response)
            self._after_response(cache_key, response, request_context, not_modified=True)
            return OfflineCacheDownloadResult(not_modified=True, etag=etag, content=None)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e) from e

        self._after_response(cache_key, response, request_context)
        return OfflineCacheDownloadResult(
            not_modified=False,
            etag=_response_etag(response),
            suggested_file_name=_parse_suggested_filename(response),
            content=bytes(response.content),
        )

    async def validate_api_key(self) -> ValidateApiKeyResult:
        """Validate the configured API key."""
        client = self._ensure_client()
        try:
            response = await client.get(_PATH_VALIDATE_KEY)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e) from e
        except httpx.RequestError as e:
            raise create_api_exception_from_httpx_error(
                e, default_message="Failed to connect to Translaas API"
            ) from e
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise TranslaasApiException(
                f"Unexpected error during API request: {str(e)}", inner_error=e
            ) from e

        data = response.json()
        if not isinstance(data, dict):
            raise TranslaasApiException(
                f"Invalid validate response: expected object, got {type(data).__name__}",
            )
        return ValidateApiKeyResult.from_api_dict(data)

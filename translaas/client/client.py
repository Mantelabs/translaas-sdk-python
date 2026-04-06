"""Core HTTP client implementation for the Translaas SDK.

This module provides the TranslaasClient class, which handles all HTTP
communication with the Translaas Translation Delivery API.
"""

from __future__ import annotations

import asyncio
import json
from datetime import timedelta
from typing import Any, Optional

import httpx

from translaas.client.parsing import (
    project_locales_from_response,
    translation_group_from_response,
    translation_project_from_response,
)
from translaas.exceptions import (
    TranslaasApiException,
    TranslaasConfigurationException,
    create_api_exception_from_httpx_error,
)
from translaas.models.enums import CacheMode
from translaas.models.options import TranslaasOptions
from translaas.models.protocols import ITranslaasCacheProvider, ITranslaasClient
from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject
from translaas.models.sdk_payloads import (
    ReportMissingKeyItem,
    ValidateApiKeyResult,
    report_missing_keys_body,
)

# OpenAPI: /sdk/v1/translations/...
_PATH_TEXT = "sdk/v1/translations/text"
_PATH_LOCALES = "sdk/v1/translations/locales"
_PATH_PROJECT = "sdk/v1/translations/project"
_PATH_GROUP = "sdk/v1/translations/group"
_PATH_REPORT_MISSING = "sdk/v1/translations/report-missing"
_PATH_OFFLINE_CACHE = "sdk/v1/translations/offline-cache"
_PATH_VALIDATE_KEY = "api/v1/api-keys/validate"


class TranslaasClient(ITranslaasClient):
    """HTTP client for communicating with the Translaas Translation Delivery API.

    This client provides async methods for fetching translations, handling errors,
    integrating caching, and managing HTTP sessions. It implements the ITranslaasClient
    protocol and supports context manager usage for resource cleanup.

    Attributes:
        options: Configuration options for the client.
        cache_provider: Optional cache provider for caching translations.
        _http_client: Internal httpx.AsyncClient instance.

    Example:
        ```python
        options = TranslaasOptions(
            api_key="your-api-key",
            base_url="https://api.translaas.com",
        )
        async with TranslaasClient(options) as client:
            translation = await client.get_entry("group", "entry", "en")
        ```
    """

    def __init__(
        self,
        options: TranslaasOptions,
        cache_provider: Optional[ITranslaasCacheProvider] = None,
    ) -> None:
        """Initialize a TranslaasClient instance.

        Args:
            options: Configuration options for the client. Must include api_key and base_url.
            cache_provider: Optional cache provider for caching translations.

        Raises:
            TranslaasConfigurationException: If options are invalid.
        """
        if not options.api_key or not options.base_url:
            raise TranslaasConfigurationException(
                "api_key and base_url are required in TranslaasOptions"
            )

        self.options = options
        self.cache_provider = cache_provider
        self._http_client: Optional[httpx.AsyncClient] = None
        self._etag_by_resource: dict[str, str] = {}

    async def __aenter__(self) -> TranslaasClient:
        """Enter the async context manager.

        Initializes the HTTP client session.

        Returns:
            Self for use in async context manager.
        """
        timeout: Optional[httpx.Timeout] = None
        if self.options.timeout:
            timeout_seconds = self.options.timeout.total_seconds()
            timeout = httpx.Timeout(timeout_seconds, connect=timeout_seconds)

        header_name = self.options.api_key_header.strip() or "X-Api-Key"
        self._http_client = httpx.AsyncClient(
            base_url=self.options.base_url.rstrip("/"),
            headers={
                header_name: self.options.api_key,
            },
            timeout=timeout,
            verify=self.options.verify,
        )
        return self

    async def __aexit__(
        self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[object]
    ) -> None:
        """Exit the async context manager.

        Closes the HTTP client session.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure the HTTP client is initialized.

        Returns:
            The initialized HTTP client.

        Raises:
            TranslaasConfigurationException: If client is not initialized.
        """
        if self._http_client is None:
            raise TranslaasConfigurationException(
                "Client must be used as async context manager or initialized manually"
            )
        return self._http_client

    def _sdk_query_base(self) -> dict[str, str]:
        """Shared SDK query parameters from options."""
        out: dict[str, str] = {}
        if self.options.channel:
            out["channel"] = self.options.channel
        if self.options.snapshot_version:
            out["v"] = str(self.options.snapshot_version)
        return out

    def _maybe_include_context(self, include_context: Optional[bool]) -> dict[str, str]:
        q: dict[str, str] = {}
        ic = include_context if include_context is not None else self.options.include_context
        if ic is not None:
            q["includeContext"] = "true" if ic else "false"
        return q

    def _build_cache_key(
        self,
        method: str,
        project: Optional[str] = None,
        group: Optional[str] = None,
        entry: Optional[str] = None,
        lang: Optional[str] = None,
        format: Optional[str] = None,
        number: Optional[float] = None,
        parameters: Optional[dict[str, str]] = None,
        *,
        include_context: Optional[bool] = None,
    ) -> str:
        """Build a cache key from method parameters."""
        parts = [method]
        if project:
            parts.append(f"project:{project}")
        if group:
            parts.append(f"group:{group}")
        if entry:
            parts.append(f"entry:{entry}")
        if lang:
            parts.append(f"lang:{lang}")
        if format:
            parts.append(f"format:{format}")
        if number is not None:
            parts.append(f"number:{number}")
        if parameters:
            sorted_params = sorted(parameters.items())
            param_str = ",".join(f"{k}={v}" for k, v in sorted_params)
            parts.append(f"params:{param_str}")
        if self.options.channel:
            parts.append(f"channel:{self.options.channel}")
        if self.options.snapshot_version:
            parts.append(f"v:{self.options.snapshot_version}")
        ic_eff = include_context if include_context is not None else self.options.include_context
        if ic_eff is not None:
            parts.append(f"includeContext:{ic_eff}")
        return "|".join(parts)

    def _should_cache(self, cache_mode: CacheMode, method: str) -> bool:
        """Check if caching should be used for a given method and cache mode."""
        if cache_mode == CacheMode.NONE or self.cache_provider is None:
            return False

        if method == "entry":
            return cache_mode in (CacheMode.ENTRY, CacheMode.GROUP, CacheMode.PROJECT)
        elif method == "group":
            return cache_mode in (CacheMode.GROUP, CacheMode.PROJECT)
        elif method == "project":
            return cache_mode == CacheMode.PROJECT
        elif method == "locales":
            return True

        return False

    def _get_expiration_ms(self, expiration: Optional[timedelta]) -> Optional[int]:
        """Convert timedelta to milliseconds."""
        if expiration is None:
            return None
        return int(expiration.total_seconds() * 1000)

    async def _send_get(
        self,
        path: str,
        params: dict[str, str],
        *,
        etag: Optional[str] = None,
    ) -> httpx.Response:
        client = self._ensure_client()
        headers: dict[str, str] = {}
        if etag:
            headers["If-None-Match"] = etag
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

    def _store_etag(self, resource_key: str, response: httpx.Response) -> None:
        if not self.options.use_conditional_requests:
            return
        etag = response.headers.get("etag") or response.headers.get("ETag")
        if etag:
            self._etag_by_resource[resource_key] = etag

    def _if_none_match_for(self, resource_key: str) -> Optional[str]:
        if not self.options.use_conditional_requests:
            return None
        return self._etag_by_resource.get(resource_key)

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
    ) -> str:
        """Get a single translation entry."""
        resolved_project = project if project is not None else self.options.default_project
        cache_key = self._build_cache_key(
            "entry",
            project=resolved_project,
            group=group,
            entry=entry,
            lang=lang,
            number=number,
            parameters=parameters,
        )

        if self._should_cache(self.options.cache_mode, "entry") and self.cache_provider is not None:
            cached_value = self.cache_provider.get(cache_key)
            if cached_value is not None:
                return cached_value

        request_body: dict[str, Any] = {
            "group": group,
            "entry": entry,
            "lang": lang,
        }
        if resolved_project:
            request_body["project"] = resolved_project
        if number is not None:
            request_body["n"] = number
        if parameters:
            request_body.update(parameters)
        req = self._sdk_query_base()
        if channel:
            req["channel"] = channel
        if snapshot_version is not None:
            req["v"] = str(snapshot_version)
        for k, v in request_body.items():
            if v is not None:
                req[k] = str(v)

        ifnm = self._if_none_match_for(cache_key)
        response = await self._send_get(_PATH_TEXT, req, etag=ifnm)

        if response.status_code == 304:
            if self.cache_provider is not None:
                cached_fallback = self.cache_provider.get(cache_key)
                if cached_fallback is not None:
                    return cached_fallback
            raise TranslaasApiException(
                "304 Not Modified but no cached translation is available; "
                "enable caching for this key or disable use_conditional_requests.",
                status_code=304,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e) from e

        self._store_etag(cache_key, response)
        response_text = response.text

        if self._should_cache(self.options.cache_mode, "entry") and self.cache_provider is not None:
            absolute_expiration_ms = self._get_expiration_ms(self.options.cache_absolute_expiration)
            sliding_expiration_ms = self._get_expiration_ms(self.options.cache_sliding_expiration)
            self.cache_provider.set(
                cache_key,
                response_text,
                absolute_expiration_ms=absolute_expiration_ms,
                sliding_expiration_ms=sliding_expiration_ms,
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
    ) -> TranslationGroup:
        """Get a translation group."""
        cache_key = self._build_cache_key(
            "group",
            project=project,
            group=group,
            lang=lang,
            format=format,
            include_context=include_context,
        )

        if self._should_cache(self.options.cache_mode, "group") and self.cache_provider is not None:
            cached_value = self.cache_provider.get(cache_key)
            if cached_value is not None:
                try:
                    cached_raw = json.loads(cached_value)
                    return translation_group_from_response(cached_raw)
                except (json.JSONDecodeError, TypeError, ValueError, TranslaasApiException):
                    pass

        request_body: dict[str, str] = {
            "project": project,
            "group": group,
            "lang": lang,
        }
        if format:
            request_body["format"] = format
        req = {
            **self._sdk_query_base(),
            **request_body,
            **self._maybe_include_context(include_context),
        }
        if channel:
            req["channel"] = channel
        if snapshot_version is not None:
            req["v"] = str(snapshot_version)

        ifnm = self._if_none_match_for(cache_key)
        response = await self._send_get(_PATH_GROUP, req, etag=ifnm)

        if response.status_code == 304:
            if self.cache_provider is not None:
                cached_fallback = self.cache_provider.get(cache_key)
                if cached_fallback is not None:
                    return translation_group_from_response(json.loads(cached_fallback))
            raise TranslaasApiException(
                "304 Not Modified but no cached group payload is available.",
                status_code=304,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e) from e

        self._store_etag(cache_key, response)
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
            cache_value = json.dumps(response_data)
            absolute_expiration_ms = self._get_expiration_ms(self.options.cache_absolute_expiration)
            sliding_expiration_ms = self._get_expiration_ms(self.options.cache_sliding_expiration)
            self.cache_provider.set(
                cache_key,
                cache_value,
                absolute_expiration_ms=absolute_expiration_ms,
                sliding_expiration_ms=sliding_expiration_ms,
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
    ) -> TranslationProject:
        """Get an entire translation project."""
        cache_key = self._build_cache_key(
            "project",
            project=project,
            lang=lang,
            format=format,
            include_context=include_context,
        )

        if (
            self._should_cache(self.options.cache_mode, "project")
            and self.cache_provider is not None
        ):
            cached_value = self.cache_provider.get(cache_key)
            if cached_value is not None:
                try:
                    cached_raw = json.loads(cached_value)
                    return translation_project_from_response(cached_raw)
                except (json.JSONDecodeError, TypeError, ValueError, TranslaasApiException):
                    pass

        request_body: dict[str, str] = {"project": project, "lang": lang}
        if format:
            request_body["format"] = format
        req = {
            **self._sdk_query_base(),
            **request_body,
            **self._maybe_include_context(include_context),
        }
        if channel:
            req["channel"] = channel
        if snapshot_version is not None:
            req["v"] = str(snapshot_version)

        ifnm = self._if_none_match_for(cache_key)
        response = await self._send_get(_PATH_PROJECT, req, etag=ifnm)

        if response.status_code == 304:
            if self.cache_provider is not None:
                cached_fallback = self.cache_provider.get(cache_key)
                if cached_fallback is not None:
                    return translation_project_from_response(json.loads(cached_fallback))
            raise TranslaasApiException(
                "304 Not Modified but no cached project payload is available.",
                status_code=304,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e) from e

        self._store_etag(cache_key, response)
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            raise TranslaasApiException(
                "Invalid JSON in project translations response",
                inner_error=e,
            ) from e
        if not isinstance(response_data, dict):
            raise TranslaasApiException(
                f"Invalid response format: expected dict, got {type(response_data).__name__}",
            )
        translation_project = translation_project_from_response(response_data)

        if (
            self._should_cache(self.options.cache_mode, "project")
            and self.cache_provider is not None
        ):
            cache_value = json.dumps(response_data)
            absolute_expiration_ms = self._get_expiration_ms(self.options.cache_absolute_expiration)
            sliding_expiration_ms = self._get_expiration_ms(self.options.cache_sliding_expiration)
            self.cache_provider.set(
                cache_key,
                cache_value,
                absolute_expiration_ms=absolute_expiration_ms,
                sliding_expiration_ms=sliding_expiration_ms,
            )

        return translation_project

    async def get_project_locales(
        self,
        project: str,
        *,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
    ) -> ProjectLocales:
        """Get the list of available locales for a project."""
        cache_key = self._build_cache_key("locales", project=project)

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

        request_body: dict[str, str] = {"project": project}
        req = {**self._sdk_query_base(), **request_body}
        if channel:
            req["channel"] = channel
        if snapshot_version is not None:
            req["v"] = str(snapshot_version)

        ifnm = self._if_none_match_for(cache_key)
        response = await self._send_get(_PATH_LOCALES, req, etag=ifnm)

        if response.status_code == 304:
            if self.cache_provider is not None:
                cached_fallback = self.cache_provider.get(cache_key)
                if cached_fallback is not None:
                    raw = json.loads(cached_fallback)
                    if isinstance(raw, list):
                        return ProjectLocales(locales=raw)
                    if isinstance(raw, dict):
                        return project_locales_from_response(raw)
            raise TranslaasApiException(
                "304 Not Modified but no cached locales payload is available.",
                status_code=304,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e) from e

        self._store_etag(cache_key, response)
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            raise TranslaasApiException(
                "Invalid JSON in project locales response",
                inner_error=e,
            ) from e
        project_locales = project_locales_from_response(response_data)

        if (
            self._should_cache(self.options.cache_mode, "locales")
            and self.cache_provider is not None
        ):
            if isinstance(response_data, dict):
                cache_value = json.dumps(response_data)
            else:
                cache_value = json.dumps(project_locales.locales)
            absolute_expiration_ms = self._get_expiration_ms(self.options.cache_absolute_expiration)
            sliding_expiration_ms = self._get_expiration_ms(self.options.cache_sliding_expiration)
            self.cache_provider.set(
                cache_key,
                cache_value,
                absolute_expiration_ms=absolute_expiration_ms,
                sliding_expiration_ms=sliding_expiration_ms,
            )

        return project_locales

    async def report_missing_keys(self, keys: list[ReportMissingKeyItem]) -> None:
        """Report missing translation keys (`POST /sdk/v1/translations/report-missing`)."""
        client = self._ensure_client()
        body = report_missing_keys_body(keys)
        try:
            response = await client.post(
                _PATH_REPORT_MISSING,
                json=body,
            )
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
    ) -> bytes:
        """Download the offline ZIP bundle (`GET /sdk/v1/translations/offline-cache`)."""
        req: dict[str, str] = {
            "project": project,
            **self._sdk_query_base(),
            **self._maybe_include_context(include_context),
        }
        if channel:
            req["channel"] = channel
        if snapshot_version is not None:
            req["v"] = str(snapshot_version)

        cache_key = f"offline|project:{project}|{req.get('channel','')}|{req.get('v','')}|{req.get('includeContext','')}"
        ifnm = self._if_none_match_for(cache_key)
        response = await self._send_get(_PATH_OFFLINE_CACHE, req, etag=ifnm)

        if response.status_code == 304:
            raise TranslaasApiException(
                "304 Not Modified for offline cache; persist the last ZIP locally if you need 304 handling.",
                status_code=304,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise create_api_exception_from_httpx_error(e) from e

        self._store_etag(cache_key, response)
        return response.content

    async def validate_api_key(self) -> ValidateApiKeyResult:
        """Validate the configured API key (`GET /api/v1/api-keys/validate`)."""
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

"""Core HTTP client implementation for the Translaas SDK.

This module provides the TranslaasClient class, which handles all HTTP
communication with the Translaas Translation Delivery API.
"""

import asyncio
import json
from datetime import timedelta
from typing import Any, Dict, Optional

import httpx

from translaas.exceptions import (
    TranslaasApiException,
    TranslaasConfigurationException,
    create_api_exception_from_httpx_error,
)
from translaas.models.enums import CacheMode
from translaas.models.options import TranslaasOptions
from translaas.models.protocols import ITranslaasCacheProvider, ITranslaasClient
from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject


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

    async def __aenter__(self) -> "TranslaasClient":
        """Enter the async context manager.

        Initializes the HTTP client session.

        Returns:
            Self for use in async context manager.
        """
        timeout: Optional[httpx.Timeout] = None
        if self.options.timeout:
            timeout_seconds = self.options.timeout.total_seconds()
            timeout = httpx.Timeout(timeout_seconds, connect=timeout_seconds)

        self._http_client = httpx.AsyncClient(
            base_url=self.options.base_url.rstrip("/"),
            headers={
                "X-Api-Key": self.options.api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
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

    def _build_cache_key(
        self,
        method: str,
        project: Optional[str] = None,
        group: Optional[str] = None,
        entry: Optional[str] = None,
        lang: Optional[str] = None,
        format: Optional[str] = None,
        number: Optional[float] = None,
        parameters: Optional[Dict[str, str]] = None,
    ) -> str:
        """Build a cache key from method parameters.

        Args:
            method: The method name (e.g., 'entry', 'group', 'project', 'locales').
            project: Optional project ID.
            group: Optional group name.
            entry: Optional entry key.
            lang: Optional language code.
            format: Optional format specification.
            number: Optional number for plural forms.
            parameters: Optional parameters dictionary.

        Returns:
            A cache key string.
        """
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
            # Sort parameters for consistent cache keys
            sorted_params = sorted(parameters.items())
            param_str = ",".join(f"{k}={v}" for k, v in sorted_params)
            parts.append(f"params:{param_str}")

        return "|".join(parts)

    def _should_cache(self, cache_mode: CacheMode, method: str) -> bool:
        """Check if caching should be used for a given method and cache mode.

        Args:
            cache_mode: The cache mode from options.
            method: The method name ('entry', 'group', 'project', 'locales').

        Returns:
            True if caching should be used, False otherwise.
        """
        if cache_mode == CacheMode.NONE or self.cache_provider is None:
            return False

        if method == "entry":
            return cache_mode in (CacheMode.ENTRY, CacheMode.GROUP, CacheMode.PROJECT)
        elif method == "group":
            return cache_mode in (CacheMode.GROUP, CacheMode.PROJECT)
        elif method == "project":
            return cache_mode == CacheMode.PROJECT
        elif method == "locales":
            # Locales are typically cached regardless of mode
            return True

        return False

    def _get_expiration_ms(self, expiration: Optional[timedelta]) -> Optional[int]:
        """Convert timedelta to milliseconds.

        Args:
            expiration: Optional timedelta expiration.

        Returns:
            Expiration in milliseconds, or None.
        """
        if expiration is None:
            return None
        return int(expiration.total_seconds() * 1000)

    async def _make_request(
        self,
        endpoint: str,
        request_body: Dict[str, Any],
        response_type: str = "json",
    ) -> Any:
        """Make an HTTP request to the API.

        Args:
            endpoint: The API endpoint path.
            request_body: The request parameters as a dictionary (converted to query parameters).
            response_type: The expected response type ('json' or 'text').

        Returns:
            The parsed response (dict for JSON, str for text).

        Raises:
            TranslaasApiException: If the API request fails.
        """
        client = self._ensure_client()
        # httpx.AsyncClient handles URL joining automatically when base_url is set
        # Just use the endpoint path directly
        url = endpoint.lstrip("/")

        try:
            # Convert request body dict to query parameters
            # Filter out None values and convert to strings
            params: Dict[str, str] = {}
            for key, value in request_body.items():
                if value is not None:
                    if isinstance(value, dict):
                        # For nested dicts (like parameters), serialize as JSON string
                        params[key] = json.dumps(value)
                    else:
                        params[key] = str(value)

            response = await client.get(url, params=params)
            response.raise_for_status()

            if response_type == "json":
                return response.json()
            else:
                return response.text

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

    async def get_entry(
        self,
        group: str,
        entry: str,
        lang: str,
        number: Optional[float] = None,
        parameters: Optional[Dict[str, str]] = None,
    ) -> str:
        """Get a single translation entry.

        Args:
            group: The translation group name.
            entry: The translation entry key.
            lang: The language code (ISO 639-1).
            number: Optional number for plural form selection.
            parameters: Optional dictionary of parameters for string interpolation.

        Returns:
            The translated string.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        cache_key = self._build_cache_key(
            "entry", group=group, entry=entry, lang=lang, number=number, parameters=parameters
        )

        # Check cache first if caching is enabled
        if self._should_cache(self.options.cache_mode, "entry") and self.cache_provider is not None:
            cached_value = self.cache_provider.get(cache_key)
            if cached_value is not None:
                return cached_value

        # Build request body
        request_body: Dict[str, Any] = {
            "group": group,
            "entry": entry,
            "lang": lang,
        }
        if number is not None:
            request_body["n"] = number
        if parameters:
            request_body["parameters"] = parameters

        # Make API request
        response_text_raw = await self._make_request(
            "/api/translations/text", request_body, response_type="text"
        )
        # Ensure we return a string (mypy doesn't know _make_request returns str for text type)
        response_text: str = str(response_text_raw)

        # Update cache if caching is enabled
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
    ) -> TranslationGroup:
        """Get a translation group.

        Args:
            project: The project ID.
            group: The translation group name.
            lang: The language code (ISO 639-1).
            format: Optional format specification.

        Returns:
            A TranslationGroup containing all entries in the group.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        cache_key = self._build_cache_key(
            "group", project=project, group=group, lang=lang, format=format
        )

        # Check cache first if caching is enabled
        if self._should_cache(self.options.cache_mode, "group") and self.cache_provider is not None:
            cached_value = self.cache_provider.get(cache_key)
            if cached_value is not None:
                try:
                    cached_data = json.loads(cached_value)
                    return TranslationGroup(entries=cached_data)
                except (json.JSONDecodeError, TypeError, ValueError):
                    # Cache data is corrupted, continue to API
                    pass

        # Build request body
        request_body: Dict[str, Any] = {
            "project": project,
            "group": group,
            "lang": lang,
        }
        if format:
            request_body["format"] = format

        # Make API request
        response_data = await self._make_request(
            "/api/translations/group", request_body, response_type="json"
        )

        # Parse response
        if not isinstance(response_data, dict):
            raise TranslaasApiException(
                f"Invalid response format: expected dict, got {type(response_data).__name__}"
            )

        translation_group = TranslationGroup(entries=response_data)

        # Update cache if caching is enabled
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
    ) -> TranslationProject:
        """Get an entire translation project.

        Args:
            project: The project ID.
            lang: The language code (ISO 639-1).
            format: Optional format specification.

        Returns:
            A TranslationProject containing all groups and entries.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        cache_key = self._build_cache_key("project", project=project, lang=lang, format=format)

        # Check cache first if caching is enabled
        if (
            self._should_cache(self.options.cache_mode, "project")
            and self.cache_provider is not None
        ):
            cached_value = self.cache_provider.get(cache_key)
            if cached_value is not None:
                try:
                    cached_data = json.loads(cached_value)
                    return TranslationProject(groups=cached_data)
                except (json.JSONDecodeError, TypeError, ValueError):
                    # Cache data is corrupted, continue to API
                    pass

        # Build request body
        request_body: Dict[str, Any] = {
            "project": project,
            "lang": lang,
        }
        if format:
            request_body["format"] = format

        # Make API request
        response_data = await self._make_request(
            "/api/translations/project", request_body, response_type="json"
        )

        # Parse response
        if not isinstance(response_data, dict):
            raise TranslaasApiException(
                f"Invalid response format: expected dict, got {type(response_data).__name__}"
            )

        translation_project = TranslationProject(groups=response_data)

        # Update cache if caching is enabled
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
    ) -> ProjectLocales:
        """Get the list of available locales for a project.

        Args:
            project: The project ID.

        Returns:
            A ProjectLocales instance containing the list of available locales.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        cache_key = self._build_cache_key("locales", project=project)

        # Check cache first if caching is enabled
        if (
            self._should_cache(self.options.cache_mode, "locales")
            and self.cache_provider is not None
        ):
            cached_value = self.cache_provider.get(cache_key)
            if cached_value is not None:
                try:
                    cached_data = json.loads(cached_value)
                    if isinstance(cached_data, list):
                        return ProjectLocales(locales=cached_data)
                except (json.JSONDecodeError, TypeError, ValueError):
                    # Cache data is corrupted, continue to API
                    pass

        # Build request body
        request_body: Dict[str, Any] = {"project": project}

        # Make API request
        response_data = await self._make_request(
            "/api/translations/locales", request_body, response_type="json"
        )

        # Parse response
        if isinstance(response_data, dict) and "locales" in response_data:
            locales_list = response_data["locales"]
        elif isinstance(response_data, list):
            locales_list = response_data
        else:
            raise TranslaasApiException(
                f"Invalid response format: expected dict with 'locales' key or list, got {type(response_data).__name__}"
            )

        if not isinstance(locales_list, list):
            raise TranslaasApiException(
                f"Invalid locales format: expected list, got {type(locales_list).__name__}"
            )

        project_locales = ProjectLocales(locales=locales_list)

        # Update cache if caching is enabled
        if (
            self._should_cache(self.options.cache_mode, "locales")
            and self.cache_provider is not None
        ):
            cache_value = json.dumps(locales_list)
            absolute_expiration_ms = self._get_expiration_ms(self.options.cache_absolute_expiration)
            sliding_expiration_ms = self._get_expiration_ms(self.options.cache_sliding_expiration)
            self.cache_provider.set(
                cache_key,
                cache_value,
                absolute_expiration_ms=absolute_expiration_ms,
                sliding_expiration_ms=sliding_expiration_ms,
            )

        return project_locales

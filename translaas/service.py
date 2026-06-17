"""Service layer for the Translaas SDK.

This module provides the TranslaasService class, which offers a convenient
high-level API for translations with automatic language resolution and
parameter replacement.
"""

import re
from typing import Dict, List, Optional, Tuple, Union, overload

from translaas.caching_file.client_factory import create_translaas_client
from translaas.client.text_query import merge_number_into_parameters
from translaas.exceptions import (
    TranslaasConfigurationException,
    TranslaasLanguageResolutionException,
)
from translaas.language.resolver import LanguageResolver
from translaas.models.options import TranslaasOptions
from translaas.models.protocols import ITranslaasCacheProvider, ITranslaasClient, ITranslaasService
from translaas.models.request_context import (
    SdkTranslationQueryParams,
    TranslaasRequestContext,
    merge_request_context,
)
from translaas.models.responses import (
    OfflineCacheDownloadResult,
    ProjectLocales,
    TranslationGroup,
    TranslationProject,
)
from translaas.models.sdk_payloads import ReportMissingKeyItem, ValidateApiKeyResult


class TranslaasService(ITranslaasService):
    """High-level service for translations with automatic language resolution.

    TranslaasService provides a convenient API for fetching translations with
    automatic language resolution, parameter replacement, and pluralization support.
    It wraps TranslaasClient and LanguageResolver to provide a simpler interface.

    Attributes:
        options: Configuration options for the service.
        cache_provider: Optional cache provider for caching translations.
        language_resolver: Optional language resolver for automatic language resolution.
        _client: Internal TranslaasClient instance.

    Example:
        ```python
        options = TranslaasOptions(
            api_key="your-api-key",
            base_url="https://api.translaas.com",
        )
        resolver = LanguageResolver([DefaultLanguageProvider('en')])
        async with TranslaasService(options, language_resolver=resolver) as service:
            # Automatic language resolution
            translation = await service.t('common', 'welcome')

            # Explicit language
            translation = await service.t('common', 'welcome', 'fr')

            # With parameters
            translation = await service.t('common', 'greeting', {'name': 'John'})
        ```
    """

    def __init__(
        self,
        options: TranslaasOptions,
        cache_provider: Optional[ITranslaasCacheProvider] = None,
        language_resolver: Optional[LanguageResolver] = None,
    ) -> None:
        """Initialize a TranslaasService instance.

        Args:
            options: Configuration options for the service. Must include api_key and base_url.
            cache_provider: Optional cache provider for caching translations.
            language_resolver: Optional language resolver for automatic language resolution.
                If provided, allows omitting the lang parameter in t() calls.

        Raises:
            TranslaasConfigurationException: If options are invalid.
        """
        self.options = options
        self.cache_provider = cache_provider
        self.language_resolver = language_resolver
        self._client: Optional[ITranslaasClient] = None

    async def __aenter__(self) -> "TranslaasService":
        """Enter the async context manager.

        Initializes the internal client.

        Returns:
            Self for use in async context manager.
        """
        self._client = create_translaas_client(self.options, self.cache_provider)
        enter = getattr(self._client, "__aenter__", None)
        if enter is not None:
            await enter()
        return self

    async def __aexit__(
        self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[object]
    ) -> None:
        """Exit the async context manager.

        Closes the internal client.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        if self._client:
            exit_fn = getattr(self._client, "__aexit__", None)
            if exit_fn is not None:
                await exit_fn(exc_type, exc_val, exc_tb)
            self._client = None

    def _ensure_client(self) -> ITranslaasClient:
        """Ensure the client is initialized.

        Returns:
            The initialized client.

        Raises:
            TranslaasConfigurationException: If client is not initialized.
        """
        if self._client is None:
            raise TranslaasConfigurationException(
                "Service must be used as async context manager or client must be initialized manually"
            )
        return self._client

    async def _resolve_language(self, lang: Optional[str]) -> str:
        """Resolve the language to use for translation.

        If lang is provided, returns it. Otherwise, attempts to resolve
        language using the language resolver. Falls back to default_language
        from options if available.

        Args:
            lang: Optional explicit language code.

        Returns:
            The language code to use.

        Raises:
            TranslaasLanguageResolutionException: If language cannot be resolved.
        """
        if lang:
            return lang

        if self.language_resolver:
            try:
                resolved_lang = await self.language_resolver.resolve()
                if resolved_lang:
                    return resolved_lang
            except TranslaasLanguageResolutionException:
                pass

        if self.options.default_language:
            return self.options.default_language

        raise TranslaasLanguageResolutionException(
            "Language must be provided explicitly or resolved via language_resolver, "
            "or default_language must be set in options"
        )

    def _replace_parameters(self, text: str, parameters: Optional[Dict[str, str]]) -> str:
        """Replace parameters in translation text.

        Supports both {{key}} and {key} formats for parameter replacement.
        Parameters are replaced in order, with {{key}} taking precedence over {key}
        if both exist.

        Args:
            text: The translation text with parameter placeholders.
            parameters: Optional dictionary of parameters to replace.

        Returns:
            The text with parameters replaced.
        """
        if not parameters:
            return text

        result = text

        # First, replace {{key}} format (double braces)
        for key, value in parameters.items():
            # Escape the key to prevent regex injection
            escaped_key = re.escape(key)
            # Replace {{key}} with value
            pattern = r"\{\{" + escaped_key + r"\}\}"
            result = re.sub(pattern, value, result)

        # Then, replace {key} format (single braces)
        for key, value in parameters.items():
            # Escape the key to prevent regex injection
            escaped_key = re.escape(key)
            # Replace {key} with value, but not if it's part of {{key}}
            pattern = r"(?<!\{)\{" + escaped_key + r"\}(?!\})"
            result = re.sub(pattern, value, result)

        return result

    @overload
    async def t(
        self,
        group: str,
        entry: str,
    ) -> str:
        """Get translation without language (automatic resolution).

        Args:
            group: The translation group name.
            entry: The translation entry key.

        Returns:
            The translated string.

        Raises:
            TranslaasLanguageResolutionException: If language cannot be resolved.
            TranslaasApiException: If the API request fails.
        """
        ...

    @overload
    async def t(
        self,
        group: str,
        entry: str,
        number: float,
    ) -> str:
        """Get translation with number for plural forms (automatic language resolution).

        Args:
            group: The translation group name.
            entry: The translation entry key.
            number: Number for plural form selection.

        Returns:
            The translated string with appropriate plural form.

        Raises:
            TranslaasLanguageResolutionException: If language cannot be resolved.
            TranslaasApiException: If the API request fails.
        """
        ...

    @overload
    async def t(
        self,
        group: str,
        entry: str,
        number: float,
        parameters: Dict[str, str],
    ) -> str:
        """Get translation with number and parameters (automatic language resolution)."""
        ...

    @overload
    async def t(
        self,
        group: str,
        entry: str,
        parameters: Dict[str, str],
    ) -> str:
        """Get translation with parameters (automatic language resolution).

        Args:
            group: The translation group name.
            entry: The translation entry key.
            parameters: Dictionary of parameters for string interpolation.

        Returns:
            The translated string with interpolated parameters.

        Raises:
            TranslaasLanguageResolutionException: If language cannot be resolved.
            TranslaasApiException: If the API request fails.
        """
        ...

    @overload
    async def t(
        self,
        group: str,
        entry: str,
        lang: str,
    ) -> str:
        """Get translation with explicit language.

        Args:
            group: The translation group name.
            entry: The translation entry key.
            lang: The language code (ISO 639-1).

        Returns:
            The translated string.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        ...

    @overload
    async def t(
        self,
        group: str,
        entry: str,
        lang: str,
        number: float,
    ) -> str:
        """Get translation with explicit language and number for plural forms.

        Args:
            group: The translation group name.
            entry: The translation entry key.
            lang: The language code (ISO 639-1).
            number: Number for plural form selection.

        Returns:
            The translated string with appropriate plural form.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        ...

    @overload
    async def t(
        self,
        group: str,
        entry: str,
        lang: str,
        parameters: Dict[str, str],
    ) -> str:
        """Get translation with explicit language and parameters.

        Args:
            group: The translation group name.
            entry: The translation entry key.
            lang: The language code (ISO 639-1).
            parameters: Dictionary of parameters for string interpolation.

        Returns:
            The translated string with interpolated parameters.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        ...

    @overload
    async def t(
        self,
        group: str,
        entry: str,
        lang: str,
        number: float,
        parameters: Dict[str, str],
    ) -> str:
        """Get translation with explicit language, number, and parameters."""
        ...

    async def t(  # type: ignore[misc]
        self,
        group: str,
        entry: str,
        lang_or_number_or_params: Optional[Union[str, int, float, Dict[str, str]]] = None,
        number_or_params: Optional[Union[int, float, Dict[str, str]]] = None,
        parameters: Optional[Dict[str, str]] = None,
        *,
        request_context: Optional[TranslaasRequestContext] = None,
        sdk_query: Optional[SdkTranslationQueryParams] = None,
        project: Optional[str] = None,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
    ) -> str:
        """Get translation (implementation method).

        This is the actual implementation that handles all overloads.
        The overloads above provide type hints for different call patterns.

        Args:
            group: The translation group name.
            entry: The translation entry key.
            lang_or_number_or_params: Optional language code, number, or parameters dict.
                - If str: language code (ISO 639-1)
                - If float: number for plural form selection (automatic language resolution)
                - If Dict[str, str]: parameters for string interpolation (automatic language resolution)
                - If None: uses automatic language resolution
            number_or_params: Optional number or parameters dict.
                - With explicit lang: number or parameters for the fourth positional argument
                - With automatic language: parameters when third argument is a number
            parameters: Optional parameters dict (fifth positional or keyword).
                Use with ``t(group, entry, lang, number, parameters)`` or
                ``t(group, entry, number, parameters)``.

        Returns:
            The translated string with parameters replaced if provided.

        Raises:
            TranslaasLanguageResolutionException: If language cannot be resolved.
            TranslaasApiException: If the API request fails.
        """
        client = self._ensure_client()

        lang, number, resolved_parameters = self._parse_t_arguments(
            lang_or_number_or_params,
            number_or_params,
            parameters,
        )

        # Resolve language
        resolved_lang = await self._resolve_language(lang)

        ctx = merge_request_context(
            request_context,
            sdk_query,
            project=project if project is not None else self.options.default_project,
            channel=channel,
            snapshot_version=snapshot_version,
        )
        translation = await client.get_entry(
            group=group,
            entry=entry,
            lang=resolved_lang,
            number=number,
            parameters=None,
            project=ctx.project if ctx and ctx.project else self.options.default_project,
            request_context=ctx,
        )

        merged_parameters = merge_number_into_parameters(number, resolved_parameters)
        if merged_parameters:
            translation = self._replace_parameters(translation, merged_parameters)

        return translation

    @staticmethod
    def _parse_t_arguments(
        lang_or_number_or_params: Optional[Union[str, int, float, Dict[str, str]]],
        number_or_params: Optional[Union[int, float, Dict[str, str]]],
        parameters: Optional[Dict[str, str]],
    ) -> Tuple[Optional[str], Optional[float], Optional[Dict[str, str]]]:
        """Normalize positional ``t()`` arguments to match .NET ``ITranslaasService.T``."""
        lang: Optional[str] = None
        number: Optional[float] = None
        resolved_parameters = parameters

        def _merge_parameters_dict(value: Dict[str, str]) -> None:
            nonlocal number, resolved_parameters
            extracted_number = value.pop("number", None)
            if isinstance(extracted_number, (int, float)):
                number = float(extracted_number)
            merged = dict(value)
            if resolved_parameters:
                merged = {**merged, **resolved_parameters}
            resolved_parameters = merged or None

        if lang_or_number_or_params is None:
            pass
        elif isinstance(lang_or_number_or_params, str):
            lang = lang_or_number_or_params
            if isinstance(number_or_params, (int, float)):
                number = float(number_or_params)
            elif isinstance(number_or_params, dict):
                _merge_parameters_dict(dict(number_or_params))
        elif isinstance(lang_or_number_or_params, (int, float)):
            number = float(lang_or_number_or_params)
            if isinstance(number_or_params, dict):
                _merge_parameters_dict(dict(number_or_params))
        elif isinstance(lang_or_number_or_params, dict):
            _merge_parameters_dict(dict(lang_or_number_or_params))
        else:
            raise TypeError(
                f"Invalid argument type for lang_or_number_or_params: {type(lang_or_number_or_params)}"
            )

        return lang, number, resolved_parameters

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
        sdk_query: Optional[SdkTranslationQueryParams] = None,
    ) -> str:
        """Get a single translation entry.

        Convenience method that delegates to the client. This method provides
        direct access to the client API without automatic language resolution.

        Args:
            group: The translation group name.
            entry: The translation entry key.
            lang: The language code (ISO 639-1).
            number: Optional number for plural form selection.
            parameters: Optional dictionary of parameters for string interpolation.
            project: Optional project slug/id (falls back to ``default_project`` in options).
            channel: Optional channel override for this request.
            snapshot_version: Optional snapshot version (`v`) override.
            request_context: Optional per-request context (ETag, project, channel, version).
            sdk_query: Optional SDK query overrides merged into ``request_context``.

        Returns:
            The translated string with parameters replaced if provided.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        client = self._ensure_client()
        resolved_project = project if project is not None else self.options.default_project
        ctx = merge_request_context(
            request_context,
            sdk_query,
            project=resolved_project,
            channel=channel,
            snapshot_version=snapshot_version,
        )

        translation = await client.get_entry(
            group=group,
            entry=entry,
            lang=lang,
            number=number,
            parameters=None,
            project=resolved_project,
            request_context=ctx,
        )

        merged_parameters = merge_number_into_parameters(number, parameters)
        if merged_parameters:
            translation = self._replace_parameters(translation, merged_parameters)

        return translation

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
        sdk_query: Optional[SdkTranslationQueryParams] = None,
    ) -> TranslationGroup:
        """Get a translation group.

        Convenience method that delegates to the client.

        Args:
            project: The project ID.
            group: The translation group name.
            lang: The language code (ISO 639-1).
            format: Optional format specification.
            include_context: Optional `includeContext` override for this request.
            channel: Optional channel override.
            snapshot_version: Optional snapshot version (`v`) override.
            request_context: Optional per-request context.
            sdk_query: Optional SDK query overrides merged into ``request_context``.

        Returns:
            A TranslationGroup containing all entries in the group.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        client = self._ensure_client()
        ctx = merge_request_context(
            request_context,
            sdk_query,
            project=project,
            channel=channel,
            snapshot_version=snapshot_version,
            include_context=include_context,
        )
        return await client.get_group(
            project=project,
            group=group,
            lang=lang,
            format=format,
            include_context=include_context,
            request_context=ctx,
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
        sdk_query: Optional[SdkTranslationQueryParams] = None,
    ) -> TranslationProject:
        """Get an entire translation project.

        Convenience method that delegates to the client.

        Args:
            project: The project ID.
            lang: The language code (ISO 639-1).
            format: Optional format specification.
            include_context: Optional `includeContext` override for this request.
            channel: Optional channel override.
            snapshot_version: Optional snapshot version (`v`) override.
            request_context: Optional per-request context.
            sdk_query: Optional SDK query overrides merged into ``request_context``.

        Returns:
            A TranslationProject containing all groups and entries.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        client = self._ensure_client()
        ctx = merge_request_context(
            request_context,
            sdk_query,
            project=project,
            channel=channel,
            snapshot_version=snapshot_version,
            include_context=include_context,
        )
        return await client.get_project(
            project=project,
            lang=lang,
            format=format,
            include_context=include_context,
            request_context=ctx,
        )

    async def get_project_locales(
        self,
        project: str,
        *,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
        request_context: Optional[TranslaasRequestContext] = None,
        sdk_query: Optional[SdkTranslationQueryParams] = None,
    ) -> ProjectLocales:
        """Get the list of available locales for a project.

        Convenience method that delegates to the client.

        Args:
            project: The project ID.
            channel: Optional channel override.
            snapshot_version: Optional snapshot version (`v`) override.
            request_context: Optional per-request context.
            sdk_query: Optional SDK query overrides merged into ``request_context``.

        Returns:
            A ProjectLocales instance containing the list of available locales.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        client = self._ensure_client()
        ctx = merge_request_context(
            request_context,
            sdk_query,
            project=project,
            channel=channel,
            snapshot_version=snapshot_version,
        )
        return await client.get_project_locales(project=project, request_context=ctx)

    async def report_missing_keys(self, keys: List[ReportMissingKeyItem]) -> None:
        """Report missing translation keys (requires a project-scoped API key)."""
        client = self._ensure_client()
        await client.report_missing_keys(keys)

    async def get_offline_cache(
        self,
        project: str,
        *,
        include_context: Optional[bool] = None,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
        request_context: Optional[TranslaasRequestContext] = None,
        sdk_query: Optional[SdkTranslationQueryParams] = None,
    ) -> OfflineCacheDownloadResult:
        """Download the offline ZIP bundle for a project."""
        client = self._ensure_client()
        ctx = merge_request_context(
            request_context,
            sdk_query,
            project=project,
            channel=channel,
            snapshot_version=snapshot_version,
            include_context=include_context,
        )
        return await client.get_offline_cache(
            project,
            include_context=include_context,
            channel=channel,
            snapshot_version=snapshot_version,
            request_context=ctx,
        )

    async def validate_api_key(self) -> ValidateApiKeyResult:
        """Validate the configured API key."""
        client = self._ensure_client()
        return await client.validate_api_key()

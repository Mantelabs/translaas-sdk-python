"""Service layer for the Translaas SDK.

This module provides the TranslaasService class, which offers a convenient
high-level API for translations with automatic language resolution and
parameter replacement.
"""

import re
from typing import Dict, Optional, Union, overload

from translaas.client.client import TranslaasClient
from translaas.exceptions import (
    TranslaasConfigurationException,
    TranslaasLanguageResolutionException,
)
from translaas.language.resolver import LanguageResolver
from translaas.models.options import TranslaasOptions
from translaas.models.protocols import ITranslaasCacheProvider, ITranslaasService
from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject


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
        self._client: Optional[TranslaasClient] = None

    async def __aenter__(self) -> "TranslaasService":
        """Enter the async context manager.

        Initializes the internal client.

        Returns:
            Self for use in async context manager.
        """
        self._client = TranslaasClient(self.options, self.cache_provider)
        await self._client.__aenter__()
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
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
            self._client = None

    def _ensure_client(self) -> TranslaasClient:
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

    async def t(  # type: ignore[misc]
        self,
        group: str,
        entry: str,
        lang_or_number_or_params: Optional[Union[str, int, float, Dict[str, str]]] = None,
        number_or_params: Optional[Union[int, float, Dict[str, str]]] = None,
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
            number_or_params: Optional number or parameters dict (only used when lang is provided).
                - If float: number for plural form selection
                - If Dict[str, str]: parameters for string interpolation

        Returns:
            The translated string with parameters replaced if provided.

        Raises:
            TranslaasLanguageResolutionException: If language cannot be resolved.
            TranslaasApiException: If the API request fails.
        """
        client = self._ensure_client()

        # Parse arguments based on their types
        lang: Optional[str] = None
        number: Optional[float] = None
        parameters: Optional[Dict[str, str]] = None

        if lang_or_number_or_params is None:
            # t(group, entry) - automatic language resolution
            pass
        elif isinstance(lang_or_number_or_params, str):
            # t(group, entry, lang) or t(group, entry, lang, number/params)
            lang = lang_or_number_or_params
            if isinstance(number_or_params, (int, float)):
                number = float(number_or_params)
            elif isinstance(number_or_params, dict):
                parameters = number_or_params
        elif isinstance(lang_or_number_or_params, (int, float)):
            # t(group, entry, number) - automatic language resolution with plural
            number = float(lang_or_number_or_params)
        elif isinstance(lang_or_number_or_params, dict):
            # t(group, entry, parameters) - automatic language resolution with params
            parameters = lang_or_number_or_params
        else:
            raise TypeError(
                f"Invalid argument type for lang_or_number_or_params: {type(lang_or_number_or_params)}"
            )

        # Resolve language
        resolved_lang = await self._resolve_language(lang)

        # Get translation from API (API handles pluralization via number parameter)
        # Note: We pass parameters to the API, but also do client-side replacement
        # for compatibility with both server-side and client-side parameter handling
        translation = await client.get_entry(
            group=group,
            entry=entry,
            lang=resolved_lang,
            number=number,
            parameters=None,  # We handle parameters client-side
        )

        # Replace parameters client-side
        if parameters:
            translation = self._replace_parameters(translation, parameters)

        return translation

    async def get_entry(
        self,
        group: str,
        entry: str,
        lang: str,
        number: Optional[float] = None,
        parameters: Optional[Dict[str, str]] = None,
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

        Returns:
            The translated string with parameters replaced if provided.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        client = self._ensure_client()

        # Get translation from API
        translation = await client.get_entry(
            group=group,
            entry=entry,
            lang=lang,
            number=number,
            parameters=None,  # We handle parameters client-side
        )

        # Replace parameters client-side
        if parameters:
            translation = self._replace_parameters(translation, parameters)

        return translation

    async def get_group(
        self,
        project: str,
        group: str,
        lang: str,
        format: Optional[str] = None,
    ) -> TranslationGroup:
        """Get a translation group.

        Convenience method that delegates to the client.

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
        client = self._ensure_client()
        return await client.get_group(project=project, group=group, lang=lang, format=format)

    async def get_project(
        self,
        project: str,
        lang: str,
        format: Optional[str] = None,
    ) -> TranslationProject:
        """Get an entire translation project.

        Convenience method that delegates to the client.

        Args:
            project: The project ID.
            lang: The language code (ISO 639-1).
            format: Optional format specification.

        Returns:
            A TranslationProject containing all groups and entries.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        client = self._ensure_client()
        return await client.get_project(project=project, lang=lang, format=format)

    async def get_project_locales(
        self,
        project: str,
    ) -> ProjectLocales:
        """Get the list of available locales for a project.

        Convenience method that delegates to the client.

        Args:
            project: The project ID.

        Returns:
            A ProjectLocales instance containing the list of available locales.

        Raises:
            TranslaasApiException: If the API request fails.
        """
        client = self._ensure_client()
        return await client.get_project_locales(project=project)

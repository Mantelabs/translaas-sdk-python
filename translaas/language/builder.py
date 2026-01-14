"""Builder for fluent language provider configuration.

This module provides the LanguageProviderBuilder class for building
language resolver configurations using a fluent interface.
"""

from typing import List, Optional

from translaas.exceptions import TranslaasLanguageResolutionException
from translaas.language.providers import (
    CultureLanguageProvider,
    DefaultLanguageProvider,
    RequestLanguageProvider,
)
from translaas.language.resolver import LanguageResolver
from translaas.models.protocols import ILanguageProvider


class LanguageProviderBuilder:
    """Builder for creating language resolver configurations.

    Provides a fluent interface for building language resolver configurations
    by chaining multiple providers together.

    Example:
        ```python
        builder = LanguageProviderBuilder()
        resolver = (
            builder
            .add_request_provider(request)
            .add_culture_provider()
            .add_default_provider('en')
            .build()
        )
        language = await resolver.resolve()
        ```
    """

    def __init__(self) -> None:
        """Initialize a LanguageProviderBuilder."""
        self._providers: List[ILanguageProvider] = []

    def add_request_provider(
        self,
        request: object,
        *,
        header_name: str = "Accept-Language",
        cookie_name: str = "language",
        param_name: Optional[str] = None,
    ) -> "LanguageProviderBuilder":
        """Add a request-based language provider.

        Args:
            request: The request object with headers and cookies attributes.
            header_name: The header name to check (default: 'Accept-Language').
            cookie_name: The cookie name to check (default: 'language').
            param_name: Optional query parameter name to check.

        Returns:
            Self for method chaining.
        """
        provider = RequestLanguageProvider(
            request,
            header_name=header_name,
            cookie_name=cookie_name,
            param_name=param_name,
        )
        self._providers.append(provider)
        return self

    def add_culture_provider(self) -> "LanguageProviderBuilder":
        """Add a culture-based language provider.

        Adds a provider that detects language from system locale.

        Returns:
            Self for method chaining.
        """
        provider = CultureLanguageProvider()
        self._providers.append(provider)
        return self

    def add_default_provider(self, default_language: str) -> "LanguageProviderBuilder":
        """Add a default language provider.

        Adds a provider that always returns the specified default language.
        This should typically be added last as a fallback.

        Args:
            default_language: The default language code (ISO 639-1).

        Returns:
            Self for method chaining.

        Raises:
            TranslaasLanguageResolutionException: If the language code is invalid.
        """
        provider = DefaultLanguageProvider(default_language)
        self._providers.append(provider)
        return self

    def add_provider(self, provider: ILanguageProvider) -> "LanguageProviderBuilder":
        """Add a custom language provider.

        Args:
            provider: A custom language provider implementing ILanguageProvider.

        Returns:
            Self for method chaining.
        """
        self._providers.append(provider)
        return self

    def build(self) -> LanguageResolver:
        """Build the language resolver with configured providers.

        Returns:
            A LanguageResolver instance with all configured providers.

        Raises:
            TranslaasLanguageResolutionException: If no providers were added.
        """
        if not self._providers:
            raise TranslaasLanguageResolutionException(
                "At least one language provider must be added before building"
            )
        return LanguageResolver(self._providers)

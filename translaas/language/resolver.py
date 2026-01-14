"""Language resolver for chaining multiple language providers.

This module provides the LanguageResolver class that chains multiple language
providers together and resolves the current language by trying each provider
in order until one returns a language.
"""

from typing import List, Optional

from translaas.exceptions import TranslaasLanguageResolutionException
from translaas.models.protocols import ILanguageProvider


class LanguageResolver:
    """Language resolver that chains multiple providers.

    The resolver evaluates providers in order and returns the first language
    found. If no provider returns a language, it raises an exception.

    Attributes:
        providers: List of language providers to evaluate in order.

    Example:
        ```python
        resolver = LanguageResolver([
            RequestLanguageProvider(request),
            CultureLanguageProvider(),
            DefaultLanguageProvider('en')
        ])
        language = await resolver.resolve()  # Returns first available language
        ```
    """

    def __init__(self, providers: List[ILanguageProvider]) -> None:
        """Initialize a LanguageResolver.

        Args:
            providers: List of language providers to evaluate in order.

        Raises:
            TranslaasLanguageResolutionException: If providers list is empty.
        """
        if not providers:
            raise TranslaasLanguageResolutionException("At least one language provider is required")
        self.providers = providers

    async def resolve(self) -> str:
        """Resolve the current language by trying each provider in order.

        Returns:
            The language code (ISO 639-1) from the first provider that returns one.

        Raises:
            TranslaasLanguageResolutionException: If no provider returns a language.
        """
        for provider in self.providers:
            try:
                language = await provider.get_language()
                if language:
                    return language
            except Exception:
                # Log error but continue to next provider
                # In a production system, you might want to log this
                continue

        raise TranslaasLanguageResolutionException("Could not resolve language from any provider")

    async def resolve_or_none(self) -> Optional[str]:
        """Resolve the current language, returning None if not found.

        Similar to resolve(), but returns None instead of raising an exception
        if no provider returns a language.

        Returns:
            The language code (ISO 639-1) if found, or None if not available.
        """
        try:
            return await self.resolve()
        except TranslaasLanguageResolutionException:
            return None

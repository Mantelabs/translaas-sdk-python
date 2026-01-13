"""Protocol definitions for the Translaas SDK.

Protocols define the interfaces that implementations must follow.
These use structural typing (duck typing) rather than inheritance.
"""

from typing import Dict, Optional, Protocol, overload

from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject


class ITranslaasClient(Protocol):
    """Protocol for the Translaas HTTP client.

    Defines the interface for making API requests to the Translaas service.
    All methods are asynchronous.
    """

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
        ...

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
        ...

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
        ...

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
        ...


class ITranslaasService(Protocol):
    """Protocol for the Translaas service layer.

    Defines the interface for the high-level translation service that
    handles language resolution and provides convenient translation methods.
    All methods are asynchronous.
    """

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
        """
        ...

    async def t(  # type: ignore[misc]
        self,
        group: str,
        entry: str,
        lang: Optional[str] = None,
        number: Optional[float] = None,
        parameters: Optional[Dict[str, str]] = None,
    ) -> str:
        """Get translation (implementation method).

        This is the actual implementation that handles all overloads.
        The overloads above provide type hints for different call patterns.

        Args:
            group: The translation group name.
            entry: The translation entry key.
            lang: Optional language code (ISO 639-1). If None, uses automatic resolution.
            number: Optional number for plural form selection.
            parameters: Optional dictionary of parameters for string interpolation.

        Returns:
            The translated string.
        """
        ...


class ITranslaasCacheProvider(Protocol):
    """Protocol for cache providers.

    Defines the interface for caching translation data. Implementations
    can use in-memory, file-based, or other storage mechanisms.
    """

    def get(self, key: str) -> Optional[str]:
        """Get a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value if found, or None if not found or expired.
        """
        ...

    def set(
        self,
        key: str,
        value: str,
        absolute_expiration_ms: Optional[int] = None,
        sliding_expiration_ms: Optional[int] = None,
    ) -> None:
        """Set a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
            absolute_expiration_ms: Optional absolute expiration time in milliseconds.
            sliding_expiration_ms: Optional sliding expiration time in milliseconds.
        """
        ...

    def remove(self, key: str) -> None:
        """Remove a value from the cache.

        Args:
            key: The cache key to remove.
        """
        ...

    def clear(self) -> None:
        """Clear all values from the cache."""
        ...


class ILanguageProvider(Protocol):
    """Protocol for language providers.

    Defines the interface for resolving the current language from various
    sources (request headers, cookies, route parameters, etc.).
    """

    async def get_language(self) -> Optional[str]:
        """Get the current language code.

        Returns:
            The language code (ISO 639-1) if found, or None if not available.
        """
        ...

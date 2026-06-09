"""Protocol definitions for the Translaas SDK.

Protocols define the interfaces that implementations must follow.
These use structural typing (duck typing) rather than inheritance.
"""

from typing import Dict, List, Optional, Protocol, overload

from translaas.models.responses import (
    OfflineCacheDownloadResult,
    ProjectLocales,
    TranslationGroup,
    TranslationProject,
)
from translaas.models.sdk_payloads import ReportMissingKeyItem, ValidateApiKeyResult


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
        *,
        project: Optional[str] = None,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
    ) -> str:
        """Get a single translation entry."""
        ...

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
        ...

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
        ...

    async def get_project_locales(
        self,
        project: str,
        *,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
    ) -> ProjectLocales:
        """Get the list of available locales for a project."""
        ...

    async def report_missing_keys(self, keys: List[ReportMissingKeyItem]) -> None:
        """Report missing keys to the API."""
        ...

    async def get_offline_cache(
        self,
        project: str,
        *,
        include_context: Optional[bool] = None,
        channel: Optional[str] = None,
        snapshot_version: Optional[str] = None,
    ) -> OfflineCacheDownloadResult:
        """Download offline translation ZIP bundle."""
        ...

    async def validate_api_key(self) -> ValidateApiKeyResult:
        """Validate the configured API key."""
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
        """Get translation without language (automatic resolution)."""
        ...

    @overload
    async def t(
        self,
        group: str,
        entry: str,
        number: float,
    ) -> str:
        """Get translation with number for plural forms (automatic language resolution)."""
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
        """Get translation with parameters (automatic language resolution)."""
        ...

    @overload
    async def t(
        self,
        group: str,
        entry: str,
        lang: str,
    ) -> str:
        """Get translation with explicit language."""
        ...

    @overload
    async def t(
        self,
        group: str,
        entry: str,
        lang: str,
        number: float,
    ) -> str:
        """Get translation with explicit language and number for plural forms."""
        ...

    @overload
    async def t(
        self,
        group: str,
        entry: str,
        lang: str,
        parameters: Dict[str, str],
    ) -> str:
        """Get translation with explicit language and parameters."""
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
        lang: Optional[str] = None,
        number: Optional[float] = None,
        parameters: Optional[Dict[str, str]] = None,
    ) -> str:
        """Get translation (implementation method)."""
        ...


class ITranslaasCacheProvider(Protocol):
    """Protocol for cache providers.

    Defines the interface for caching translation data. Implementations
    can use in-memory, file-based, or other storage mechanisms.
    """

    def get(self, key: str) -> Optional[str]:
        """Get a value from the cache."""
        ...

    def set(
        self,
        key: str,
        value: str,
        absolute_expiration_ms: Optional[int] = None,
        sliding_expiration_ms: Optional[int] = None,
    ) -> None:
        """Set a value in the cache."""
        ...

    def remove(self, key: str) -> None:
        """Remove a value from the cache."""
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
        """Get the current language code."""
        ...

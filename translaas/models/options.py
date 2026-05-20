"""Configuration models for the Translaas SDK."""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING, List, Optional

from translaas.models.enums import CacheMode, OfflineFallbackMode

if TYPE_CHECKING:
    from translaas.models.request_context import SdkTranslationQueryParams


def normalize_translaas_base_url(url: str) -> str:
    """Normalize ``base_url`` for the HTTP client.

    If the URL ends with ``/sdk/v1`` (case-insensitive), that segment is removed.
    The client always requests paths like ``sdk/v1/translations/...`` relative to
    this origin, so both of these are equivalent:

    - ``https://api.translaas.local``
    - ``https://api.translaas.local/sdk/v1``
    """
    u = url.strip().rstrip("/")
    suffix = "/sdk/v1"
    if u.lower().endswith(suffix):
        u = u[: -len(suffix)].rstrip("/")
    return u


@dataclass
class HybridCacheOptions:
    """Configuration options for hybrid caching (memory + file cache).

    Hybrid caching combines in-memory caching with file-based caching for
    optimal performance and offline support.

    Attributes:
        enabled: Whether hybrid caching is enabled. Defaults to True.
        memory_cache_expiration: Optional expiration time for memory cache entries.
        max_memory_cache_entries: Maximum number of entries in memory cache. Defaults to 1000.
        warmup_on_startup: Whether to warm up cache on startup. Defaults to False.
    """

    enabled: bool = True
    memory_cache_expiration: Optional[timedelta] = None
    max_memory_cache_entries: Optional[int] = 1000
    warmup_on_startup: bool = False


@dataclass
class OfflineCacheOptions:
    """Configuration options for offline file-based caching.

    Offline caching allows the SDK to work without an active API connection
    by storing translations in local files.

    Attributes:
        enabled: Whether offline caching is enabled. Defaults to False.
        cache_directory: Directory path for storing cache files. Defaults to ".translaas-cache".
        fallback_mode: Fallback mode when offline. Defaults to CACHE_FIRST.
        auto_sync: Whether to automatically sync cache with API. Defaults to True.
        auto_sync_interval: Optional interval for automatic cache synchronization.
        projects: List of project IDs to cache. Empty list means cache all projects.
        languages: List of language codes to cache. Empty list means cache all languages.
        default_project_id: Optional default project ID to use when not specified.
        hybrid_cache: Optional hybrid cache configuration.
    """

    enabled: bool = False
    cache_directory: str = ".translaas-cache"
    fallback_mode: OfflineFallbackMode = OfflineFallbackMode.CACHE_FIRST
    auto_sync: bool = True
    auto_sync_interval: Optional[timedelta] = None
    projects: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    default_project_id: Optional[str] = None
    hybrid_cache: Optional[HybridCacheOptions] = None


@dataclass
class TranslaasOptions:
    """Main configuration options for the Translaas SDK.

    This is the primary configuration class that controls all aspects of
    the SDK behavior, including API connection, caching, and offline support.

    Attributes:
        api_key: API key for authenticating with the Translaas API. Required.
        base_url: Origin of the Translaas API (scheme + host [+ port]), e.g.
            ``https://api.translaas.local``. You may also paste ``.../sdk/v1``;
            that suffix is stripped automatically because the client appends
            ``sdk/v1/translations/...`` paths itself.
        cache_mode: Cache mode for translations. Defaults to NONE.
        timeout: Optional timeout for API requests.
        cache_absolute_expiration: Optional absolute expiration time for cache entries.
        cache_sliding_expiration: Optional sliding expiration time for cache entries.
        offline_cache: Optional offline cache configuration.
        default_language: Optional default language code to use when not specified.
        verify: Whether to verify SSL certificates. Defaults to True. Set to False for local development with self-signed certificates.
        default_project: Optional default `project` query for single-text fetches (multi-project API keys).
        channel: Optional SDK snapshot channel passed as query `channel`.
        snapshot_version: Optional SDK snapshot version passed as query `v`.
        include_context: Optional flag for `includeContext` on project/group/offline-cache requests.
        use_conditional_requests: When True, reuse ETags with `If-None-Match` and handle 304 when caching is enabled.
        api_key_header: HTTP header name for the API key.

    Raises:
        ValueError: If api_key or base_url is empty or None.
    """

    api_key: str
    base_url: str
    cache_mode: CacheMode = CacheMode.NONE
    timeout: Optional[timedelta] = None
    cache_absolute_expiration: Optional[timedelta] = None
    cache_sliding_expiration: Optional[timedelta] = None
    offline_cache: Optional[OfflineCacheOptions] = None
    default_language: Optional[str] = None
    verify: bool = True
    #: Sent as `project` on SDK text calls when not overridden per request (tenant / multi-project keys).
    default_project: Optional[str] = None
    #: Optional release channel query (`channel`).
    channel: Optional[str] = None
    #: Optional snapshot / version query (`v`).
    snapshot_version: Optional[str] = None
    #: When set, adds `includeContext=true|false` on project, group, and offline-cache requests.
    include_context: Optional[bool] = None
    #: Send `If-None-Match` using the last ETag seen per resource key; on 304, return cached body when available.
    use_conditional_requests: bool = False
    #: Header name for the API key (default matches OpenAPI).
    api_key_header: str = "X-Api-Key"
    #: Path prefix for SDK translation routes (default ``/sdk/v1/translations``).
    sdk_translations_path_prefix: str = "/sdk/v1/translations"
    #: Default SDK query params merged into translation requests.
    default_sdk_query: Optional["SdkTranslationQueryParams"] = None

    def __post_init__(self) -> None:
        """Validate configuration options after initialization.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        if not self.api_key or not isinstance(self.api_key, str) or not self.api_key.strip():
            raise ValueError("api_key is required and cannot be empty")
        if not self.base_url or not isinstance(self.base_url, str) or not self.base_url.strip():
            raise ValueError("base_url is required and cannot be empty")
        self.base_url = normalize_translaas_base_url(self.base_url)
        if not self.base_url:
            raise ValueError("base_url is required and cannot be empty")
        prefix = (self.sdk_translations_path_prefix or "/sdk/v1/translations").strip()
        if not prefix.startswith("/"):
            prefix = "/" + prefix
        self.sdk_translations_path_prefix = prefix.rstrip("/") or "/sdk/v1/translations"

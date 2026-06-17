"""Translaas Python SDK - A strongly-typed SDK for the Translaas Translation Delivery API."""

from translaas.__version__ import __version__
from translaas.caching import CacheKeyBuilder
from translaas.caching_file import CachingTranslaasClient, create_translaas_client
from translaas.client import TranslaasClient
from translaas.exceptions import (
    TranslaasApiException,
    TranslaasConfigurationException,
    TranslaasException,
    TranslaasLanguageResolutionException,
    TranslaasOfflineCacheException,
    TranslaasOfflineCacheMissException,
    create_api_exception_from_httpx_error,
)
from translaas.models import (
    CacheMode,
    LanguageCodes,
    OfflineCacheDownloadResult,
    OfflineCacheOptions,
    OfflineFallbackMode,
    ReportMissingKeyItem,
    SdkTranslationQueryParams,
    TranslaasOptions,
    TranslaasRequestContext,
    ValidateApiKeyResult,
)
from translaas.offline import OfflineBundle, OfflineCacheSyncService, parse_offline_zip
from translaas.service import TranslaasService

__all__ = [
    "__version__",
    # Client
    "TranslaasClient",
    # Service
    "TranslaasService",
    # Exceptions
    "TranslaasException",
    "TranslaasApiException",
    "TranslaasConfigurationException",
    "TranslaasOfflineCacheException",
    "TranslaasOfflineCacheMissException",
    "TranslaasLanguageResolutionException",
    "create_api_exception_from_httpx_error",
    # Models
    "TranslaasOptions",
    "ReportMissingKeyItem",
    "ValidateApiKeyResult",
    "CacheMode",
    "OfflineCacheOptions",
    "OfflineFallbackMode",
    "LanguageCodes",
    "OfflineCacheDownloadResult",
    "SdkTranslationQueryParams",
    "TranslaasRequestContext",
    "CacheKeyBuilder",
    "CachingTranslaasClient",
    "create_translaas_client",
    "OfflineBundle",
    "OfflineCacheSyncService",
    "parse_offline_zip",
]

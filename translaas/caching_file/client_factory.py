"""Factory helpers for constructing SDK clients with optional offline decoration."""

from __future__ import annotations

from typing import Optional

from translaas.caching_file.caching_client import CachingTranslaasClient
from translaas.caching_file.file_cache import FileCacheProvider
from translaas.client.client import TranslaasClient
from translaas.exceptions import TranslaasConfigurationException
from translaas.models.options import OfflineCacheOptions, TranslaasOptions
from translaas.models.protocols import ITranslaasCacheProvider, ITranslaasClient


def create_translaas_client(
    options: TranslaasOptions,
    cache_provider: Optional[ITranslaasCacheProvider] = None,
) -> ITranslaasClient:
    """Create the HTTP client, wrapping with offline cache when enabled."""
    inner = TranslaasClient(options, cache_provider)
    offline = options.offline_cache
    if offline is None or not offline.enabled:
        return inner

    project_id = offline.default_project_id or options.default_project
    if not project_id:
        raise TranslaasConfigurationException(
            "offline_cache.default_project_id or default_project is required when offline cache is enabled"
        )

    file_provider = FileCacheProvider(offline)
    return CachingTranslaasClient(inner, file_provider, offline, project_id)


def create_offline_cache_provider(
    offline_options: OfflineCacheOptions,
) -> FileCacheProvider:
    """Create the on-disk offline cache provider."""
    return FileCacheProvider(offline_options)

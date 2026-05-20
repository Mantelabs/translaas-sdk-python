"""Tests for client factory helpers."""

import pytest

from translaas.caching_file.caching_client import CachingTranslaasClient
from translaas.caching_file.client_factory import (
    create_offline_cache_provider,
    create_translaas_client,
)
from translaas.client.client import TranslaasClient
from translaas.exceptions import TranslaasConfigurationException
from translaas.models.enums import OfflineFallbackMode
from translaas.models.options import OfflineCacheOptions, TranslaasOptions


@pytest.fixture
def base_options() -> TranslaasOptions:
    return TranslaasOptions(api_key="key", base_url="https://api.example.com")


def test_create_translaas_client_without_offline(base_options: TranslaasOptions) -> None:
    client = create_translaas_client(base_options)
    assert isinstance(client, TranslaasClient)


def test_create_translaas_client_with_offline(base_options: TranslaasOptions) -> None:
    base_options.offline_cache = OfflineCacheOptions(
        enabled=True,
        default_project_id="proj",
        fallback_mode=OfflineFallbackMode.CACHE_FIRST,
    )
    client = create_translaas_client(base_options)
    assert isinstance(client, CachingTranslaasClient)


def test_create_translaas_client_offline_requires_project(base_options: TranslaasOptions) -> None:
    base_options.offline_cache = OfflineCacheOptions(enabled=True)
    with pytest.raises(TranslaasConfigurationException):
        create_translaas_client(base_options)


def test_create_offline_cache_provider() -> None:
    provider = create_offline_cache_provider(OfflineCacheOptions(cache_directory=".cache"))
    assert provider.cache_directory.name == ".cache"

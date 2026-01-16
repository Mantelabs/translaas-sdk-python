"""Pytest configuration and shared fixtures for the Translaas SDK test suite.

This module provides common fixtures and test utilities used across all test modules.
"""

from datetime import timedelta
from typing import Dict, Optional

import httpx
import pytest

from translaas.client.client import TranslaasClient
from translaas.models.enums import CacheMode, OfflineFallbackMode
from translaas.models.options import OfflineCacheOptions, TranslaasOptions
from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject


class MockCacheProvider:
    """Mock cache provider for testing.

    Implements ITranslaasCacheProvider protocol for use in tests.
    """

    def __init__(self) -> None:
        """Initialize mock cache provider."""
        self._cache: Dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        return self._cache.get(key)

    def set(
        self,
        key: str,
        value: str,
        absolute_expiration_ms: Optional[int] = None,
        sliding_expiration_ms: Optional[int] = None,
    ) -> None:
        """Set value in cache."""
        self._cache[key] = value

    def remove(self, key: str) -> None:
        """Remove value from cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()


@pytest.fixture
def options() -> TranslaasOptions:
    """Create default test options.

    Returns:
        TranslaasOptions instance with test configuration.
    """
    return TranslaasOptions(
        api_key="test-api-key",
        base_url="https://api.test.com",
    )


@pytest.fixture
def options_with_cache() -> TranslaasOptions:
    """Create test options with caching enabled.

    Returns:
        TranslaasOptions instance with cache mode set to ENTRY.
    """
    return TranslaasOptions(
        api_key="test-api-key",
        base_url="https://api.test.com",
        cache_mode=CacheMode.ENTRY,
        cache_absolute_expiration=timedelta(minutes=5),
    )


@pytest.fixture
def options_with_offline_cache() -> TranslaasOptions:
    """Create test options with offline caching enabled.

    Returns:
        TranslaasOptions instance with offline cache configuration.
    """
    return TranslaasOptions(
        api_key="test-api-key",
        base_url="https://api.test.com",
        offline_cache=OfflineCacheOptions(
            enabled=True,
            cache_directory=".test-cache",
            fallback_mode=OfflineFallbackMode.CACHE_FIRST,
        ),
    )


@pytest.fixture
def cache_provider() -> MockCacheProvider:
    """Create mock cache provider.

    Returns:
        MockCacheProvider instance for testing.
    """
    return MockCacheProvider()


@pytest.fixture
async def client(options: TranslaasOptions, cache_provider: MockCacheProvider) -> TranslaasClient:
    """Create and return a TranslaasClient instance.

    This fixture creates a client with a mock cache provider and ensures
    proper cleanup after tests.

    Args:
        options: Test options fixture.
        cache_provider: Mock cache provider fixture.

    Yields:
        TranslaasClient instance ready for testing.
    """
    client_instance = TranslaasClient(options, cache_provider=cache_provider)
    async with client_instance:
        yield client_instance


@pytest.fixture
async def client_no_cache(options: TranslaasOptions) -> TranslaasClient:
    """Create and return a TranslaasClient instance without cache.

    Args:
        options: Test options fixture.

    Yields:
        TranslaasClient instance without cache provider.
    """
    client_instance = TranslaasClient(options)
    async with client_instance:
        yield client_instance


@pytest.fixture
def mock_httpx_response() -> httpx.Response:
    """Create a mock HTTP response.

    Returns:
        httpx.Response instance with default test data.
    """
    return httpx.Response(
        200,
        text="Hello, World!",
        request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
    )


@pytest.fixture
def mock_translation_group() -> TranslationGroup:
    """Create a mock translation group.

    Returns:
        TranslationGroup instance with test data.
    """
    return TranslationGroup(
        entries={
            "entry1": "Hello, World!",
            "entry2": "Goodbye, World!",
            "plural_entry": {
                "zero": "No items",
                "one": "One item",
                "two": "Two items",
                "few": "Few items",
                "many": "Many items",
                "other": "Other items",
            },
        }
    )


@pytest.fixture
def mock_translation_project() -> TranslationProject:
    """Create a mock translation project.

    Returns:
        TranslationProject instance with test data.
    """
    return TranslationProject(
        groups={
            "group1": TranslationGroup(
                entries={
                    "entry1": "Hello",
                    "entry2": "World",
                }
            ),
            "group2": TranslationGroup(
                entries={
                    "entry3": "Foo",
                    "entry4": "Bar",
                }
            ),
        }
    )


@pytest.fixture
def mock_project_locales() -> ProjectLocales:
    """Create a mock project locales response.

    Returns:
        ProjectLocales instance with test data.
    """
    return ProjectLocales(locales=["en", "es", "fr", "de"])


@pytest.fixture
def mock_httpx_error_response() -> httpx.Response:
    """Create a mock HTTP error response.

    Returns:
        httpx.Response instance with 404 status.
    """
    return httpx.Response(
        404,
        text="Not Found",
        request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
    )


@pytest.fixture
def mock_httpx_server_error_response() -> httpx.Response:
    """Create a mock HTTP server error response.

    Returns:
        httpx.Response instance with 500 status.
    """
    return httpx.Response(
        500,
        text="Internal Server Error",
        request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
    )


@pytest.fixture
def sample_json_response() -> Dict:
    """Create sample JSON response data.

    Returns:
        Dictionary with sample API response data.
    """
    return {
        "group1": {
            "entry1": "Hello, World!",
            "entry2": "Goodbye, World!",
        },
        "group2": {
            "entry3": "Foo",
            "entry4": "Bar",
        },
    }


@pytest.fixture
def sample_plural_response() -> Dict:
    """Create sample plural form response data.

    Returns:
        Dictionary with sample plural form data.
    """
    return {
        "zero": "No items",
        "one": "One item",
        "two": "Two items",
        "few": "Few items",
        "many": "Many items",
        "other": "Other items",
    }

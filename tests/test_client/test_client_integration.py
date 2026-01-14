"""Integration tests for TranslaasClient.

These tests verify that TranslaasClient works correctly with different
configurations, cache modes, and real-world usage scenarios.
"""

import asyncio
from datetime import timedelta
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from translaas.client.client import TranslaasClient
from translaas.exceptions import TranslaasApiException
from translaas.models.enums import CacheMode
from translaas.models.options import TranslaasOptions
from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject


class MockCacheProvider:
    """Mock cache provider for integration testing."""

    def __init__(self) -> None:
        """Initialize mock cache provider."""
        self._cache: Dict[str, str] = {}
        self._call_count: Dict[str, int] = {"get": 0, "set": 0}

    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        self._call_count["get"] += 1
        return self._cache.get(key)

    def set(
        self,
        key: str,
        value: str,
        absolute_expiration_ms: Optional[int] = None,
        sliding_expiration_ms: Optional[int] = None,
    ) -> None:
        """Set value in cache."""
        self._call_count["set"] += 1
        self._cache[key] = value

    def remove(self, key: str) -> None:
        """Remove value from cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()


@pytest.fixture
def options() -> TranslaasOptions:
    """Create test options."""
    return TranslaasOptions(
        api_key="test-api-key",
        base_url="https://api.test.com",
        timeout=timedelta(seconds=30),
    )


@pytest.fixture
def cache_provider() -> MockCacheProvider:
    """Create mock cache provider."""
    return MockCacheProvider()


class TestTranslaasClientIntegration:
    """Integration tests for TranslaasClient."""

    @pytest.mark.asyncio
    async def test_full_workflow_without_cache(self, options: TranslaasOptions) -> None:
        """Test complete workflow without caching."""
        mock_responses = {
            "/api/translations/text": httpx.Response(
                200,
                text="Hello",
                request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
            ),
            "/api/translations/group": httpx.Response(
                200,
                json={"entry1": "value1"},
                request=httpx.Request("GET", "https://api.test.com/api/translations/group"),
            ),
            "/api/translations/project": httpx.Response(
                200,
                json={"group1": {"entry1": "value1"}},
                request=httpx.Request("GET", "https://api.test.com/api/translations/project"),
            ),
            "/api/translations/locales": httpx.Response(
                200,
                json={"locales": ["en", "fr"]},
                request=httpx.Request("GET", "https://api.test.com/api/translations/locales"),
            ),
        }

        async def mock_get(url: Any, **kwargs: Any) -> httpx.Response:
            """Mock GET request."""
            # Convert URL to string for comparison
            url_str = str(url) if not isinstance(url, str) else url
            for path, response in mock_responses.items():
                # Check both with and without leading slash
                if path in url_str or path.lstrip("/") in url_str:
                    return response
            raise ValueError(f"Unexpected URL: {url_str}")

        async with TranslaasClient(options) as client:
            with patch.object(client._http_client, "get", side_effect=mock_get):
                # Test all methods
                entry = await client.get_entry("group1", "entry1", "en")
                assert entry == "Hello"

                group = await client.get_group("project1", "group1", "en")
                assert isinstance(group, TranslationGroup)

                project = await client.get_project("project1", "en")
                assert isinstance(project, TranslationProject)

                locales = await client.get_project_locales("project1")
                assert isinstance(locales, ProjectLocales)

    @pytest.mark.asyncio
    async def test_cache_mode_entry(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test caching behavior with ENTRY cache mode."""
        options.cache_mode = CacheMode.ENTRY
        mock_response = httpx.Response(
            200,
            text="Cached Entry",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
            ):
                # First call - should hit API and cache
                result1 = await client.get_entry("group1", "entry1", "en")
                assert result1 == "Cached Entry"
                assert cache_provider._call_count["get"] == 1  # Cache miss
                assert cache_provider._call_count["set"] == 1  # Cache set

                # Second call - should hit cache
                result2 = await client.get_entry("group1", "entry1", "en")
                assert result2 == "Cached Entry"
                assert cache_provider._call_count["get"] == 2  # Cache hit
                assert cache_provider._call_count["set"] == 1  # No additional set

    @pytest.mark.asyncio
    async def test_cache_mode_group(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test caching behavior with GROUP cache mode."""
        options.cache_mode = CacheMode.GROUP
        mock_response = httpx.Response(
            200,
            json={"entry1": "value1", "entry2": "value2"},
            request=httpx.Request("GET", "https://api.test.com/api/translations/group"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
            ):
                # First call - should hit API and cache
                result1 = await client.get_group("project1", "group1", "en")
                assert isinstance(result1, TranslationGroup)
                assert cache_provider._call_count["set"] == 1

                # Second call - should hit cache
                result2 = await client.get_group("project1", "group1", "en")
                assert isinstance(result2, TranslationGroup)
                assert cache_provider._call_count["get"] == 2

    @pytest.mark.asyncio
    async def test_cache_mode_project(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test caching behavior with PROJECT cache mode."""
        options.cache_mode = CacheMode.PROJECT
        mock_response = httpx.Response(
            200,
            json={"group1": {"entry1": "value1"}},
            request=httpx.Request("GET", "https://api.test.com/api/translations/project"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
            ):
                # First call - should hit API and cache
                result1 = await client.get_project("project1", "en")
                assert isinstance(result1, TranslationProject)
                assert cache_provider._call_count["set"] == 1

                # Second call - should hit cache
                result2 = await client.get_project("project1", "en")
                assert isinstance(result2, TranslationProject)
                assert cache_provider._call_count["get"] == 2

    @pytest.mark.asyncio
    async def test_cache_mode_none(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test that NONE cache mode doesn't use cache."""
        options.cache_mode = CacheMode.NONE
        mock_response = httpx.Response(
            200,
            text="No Cache",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
            ):
                # Call should hit API but not cache
                result1 = await client.get_entry("group1", "entry1", "en")
                assert result1 == "No Cache"
                assert cache_provider._call_count["get"] == 0  # Cache not checked
                assert cache_provider._call_count["set"] == 0  # Cache not updated

                # Second call should also hit API
                result2 = await client.get_entry("group1", "entry1", "en")
                assert result2 == "No Cache"
                assert cache_provider._call_count["get"] == 0
                assert cache_provider._call_count["set"] == 0

    @pytest.mark.asyncio
    async def test_cache_key_uniqueness(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test that cache keys are unique for different parameters."""
        options.cache_mode = CacheMode.ENTRY
        mock_response = httpx.Response(
            200,
            text="Value",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
            ):
                await client.get_entry("group1", "entry1", "en")
                await client.get_entry("group1", "entry1", "fr")
                await client.get_entry("group1", "entry2", "en")
                await client.get_entry("group2", "entry1", "en")

                # Verify different cache keys were created
                assert len(cache_provider._cache) == 4

    @pytest.mark.asyncio
    async def test_cache_with_parameters(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test that cache keys include parameters."""
        options.cache_mode = CacheMode.ENTRY
        mock_response = httpx.Response(
            200,
            text="Hello, John!",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
            ):
                await client.get_entry("group1", "entry1", "en", parameters={"name": "John"})
                await client.get_entry("group1", "entry1", "en", parameters={"name": "Jane"})

                # Verify different cache keys for different parameters
                assert len(cache_provider._cache) == 2

    @pytest.mark.asyncio
    async def test_cache_with_number(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test that cache keys include number parameter."""
        options.cache_mode = CacheMode.ENTRY
        mock_response = httpx.Response(
            200,
            text="1 item",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
            ):
                await client.get_entry("group1", "entry1", "en", number=1.0)
                await client.get_entry("group1", "entry1", "en", number=2.0)

                # Verify different cache keys for different numbers
                assert len(cache_provider._cache) == 2

    @pytest.mark.asyncio
    async def test_error_handling_chain(self, options: TranslaasOptions) -> None:
        """Test that errors are properly handled and chained."""
        mock_response = httpx.Response(
            500,
            text="Internal Server Error",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        async with TranslaasClient(options) as client:
            with patch.object(
                client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
            ):
                with pytest.raises(TranslaasApiException) as exc_info:
                    await client.get_entry("group1", "entry1", "en")
                assert exc_info.value.status_code == 500
                assert exc_info.value.inner_error is not None

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, options: TranslaasOptions) -> None:
        """Test that timeout is properly configured."""
        options.timeout = timedelta(seconds=10)
        mock_response = httpx.Response(
            200,
            text="Success",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        async with TranslaasClient(options) as client:
            # Verify timeout is set on HTTP client
            assert client._http_client is not None
            assert client._http_client.timeout is not None
            assert client._http_client.timeout.connect == 10.0

            with patch.object(
                client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
            ):
                result = await client.get_entry("group1", "entry1", "en")
                assert result == "Success"

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, options: TranslaasOptions) -> None:
        """Test handling multiple concurrent requests."""
        mock_responses = [
            httpx.Response(
                200,
                text=f"Response {i}",
                request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
            )
            for i in range(5)
        ]

        async with TranslaasClient(options) as client:
            with patch.object(client._http_client, "get", side_effect=mock_responses):
                # Make concurrent requests
                results = await asyncio.gather(
                    *[client.get_entry("group1", f"entry{i}", "en") for i in range(5)]
                )

                assert len(results) == 5
                for i, result in enumerate(results):
                    assert result == f"Response {i}"

    @pytest.mark.asyncio
    async def test_cache_corruption_handling(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test that corrupted cache data is handled gracefully."""
        options.cache_mode = CacheMode.GROUP
        # Set corrupted cache data
        cache_provider.set("group|project:project1|group:group1|lang:en", "invalid json{")

        mock_response = httpx.Response(
            200,
            json={"entry1": "value1"},
            request=httpx.Request("GET", "https://api.test.com/api/translations/group"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
            ):
                # Should fall back to API when cache is corrupted
                result = await client.get_group("project1", "group1", "en")
                assert isinstance(result, TranslationGroup)
                assert result.get_value("entry1") == "value1"

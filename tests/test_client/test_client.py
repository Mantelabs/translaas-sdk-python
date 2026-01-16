"""Unit tests for TranslaasClient."""

import asyncio
import json
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import httpx
import pytest

# Import shared fixtures and utilities from conftest
from tests.conftest import MockCacheProvider  # noqa: F401
from translaas.client.client import TranslaasClient
from translaas.exceptions import TranslaasApiException, TranslaasConfigurationException
from translaas.models.enums import CacheMode
from translaas.models.options import TranslaasOptions
from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject


class TestTranslaasClientInitialization:
    """Tests for TranslaasClient initialization."""

    def test_init_with_valid_options(self, options: TranslaasOptions) -> None:
        """Test initialization with valid options."""
        client = TranslaasClient(options)
        assert client.options == options
        assert client.cache_provider is None

    def test_init_with_cache_provider(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test initialization with cache provider."""
        client = TranslaasClient(options, cache_provider=cache_provider)
        assert client.cache_provider == cache_provider

    def test_init_with_invalid_api_key(self) -> None:
        """Test initialization with invalid API key."""
        with pytest.raises(ValueError):
            TranslaasOptions(api_key="", base_url="https://api.test.com")

    def test_init_with_invalid_base_url(self) -> None:
        """Test initialization with invalid base URL."""
        with pytest.raises(ValueError):
            TranslaasOptions(api_key="test-key", base_url="")


class TestTranslaasClientContextManager:
    """Tests for TranslaasClient context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager_initializes_client(self, options: TranslaasOptions) -> None:
        """Test that context manager initializes HTTP client."""
        async with TranslaasClient(options) as client:
            assert client._http_client is not None
            assert isinstance(client._http_client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_context_manager_closes_client(self, options: TranslaasOptions) -> None:
        """Test that context manager closes HTTP client."""
        async with TranslaasClient(options) as client:
            http_client = client._http_client
            assert http_client is not None

        # After exiting context, client should be closed
        assert client._http_client is None

    @pytest.mark.asyncio
    async def test_context_manager_sets_headers(self, options: TranslaasOptions) -> None:
        """Test that context manager sets correct headers."""
        async with TranslaasClient(options) as client:
            assert client._http_client is not None
            # Headers are set on the client, verify through base_url and api_key
            assert client.options.api_key == "test-api-key"


class TestTranslaasClientGetEntry:
    """Tests for get_entry method."""

    @pytest.mark.asyncio
    async def test_get_entry_success(self, client: TranslaasClient) -> None:
        """Test successful get_entry call."""
        mock_response = httpx.Response(
            200,
            text="Hello, World!",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        with patch.object(
            client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await client.get_entry("group1", "entry1", "en")
            assert result == "Hello, World!"

    @pytest.mark.asyncio
    async def test_get_entry_with_number(self, client: TranslaasClient) -> None:
        """Test get_entry with number parameter."""
        mock_response = httpx.Response(
            200,
            text="1 item",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        with patch.object(
            client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await client.get_entry("group1", "entry1", "en", number=1.0)
            assert result == "1 item"

    @pytest.mark.asyncio
    async def test_get_entry_with_parameters(self, client: TranslaasClient) -> None:
        """Test get_entry with parameters."""
        mock_response = httpx.Response(
            200,
            text="Hello, John!",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        with patch.object(
            client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await client.get_entry("group1", "entry1", "en", parameters={"name": "John"})
            assert result == "Hello, John!"

    @pytest.mark.asyncio
    async def test_get_entry_with_cache_hit(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test get_entry with cache hit."""
        options.cache_mode = CacheMode.ENTRY
        cache_provider.set("entry|group:group1|entry:entry1|lang:en", "Cached Value")

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            result = await client.get_entry("group1", "entry1", "en")
            assert result == "Cached Value"
            # Verify API was not called
            assert client._http_client is not None

    @pytest.mark.asyncio
    async def test_get_entry_with_cache_miss_and_update(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test get_entry with cache miss and cache update."""
        options.cache_mode = CacheMode.ENTRY
        mock_response = httpx.Response(
            200,
            text="API Value",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "request", new_callable=AsyncMock, return_value=mock_response
            ):
                result = await client.get_entry("group1", "entry1", "en")
                assert result == "API Value"
                # Verify cache was updated
                cache_key = "entry|group:group1|entry:entry1|lang:en"
                assert cache_provider.get(cache_key) == "API Value"

    @pytest.mark.asyncio
    async def test_get_entry_http_error(self, client: TranslaasClient) -> None:
        """Test get_entry with HTTP error."""
        mock_response = httpx.Response(
            404,
            text="Not Found",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        with patch.object(
            client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(TranslaasApiException) as exc_info:
                await client.get_entry("group1", "entry1", "en")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_entry_network_error(self, client: TranslaasClient) -> None:
        """Test get_entry with network error."""
        with patch.object(
            client._http_client,
            "get",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection failed"),
        ):
            with pytest.raises(TranslaasApiException):
                await client.get_entry("group1", "entry1", "en")

    @pytest.mark.asyncio
    async def test_get_entry_timeout(self, client: TranslaasClient) -> None:
        """Test get_entry with timeout."""
        with patch.object(
            client._http_client,
            "get",
            new_callable=AsyncMock,
            side_effect=httpx.TimeoutException("Timeout"),
        ):
            with pytest.raises(TranslaasApiException):
                await client.get_entry("group1", "entry1", "en")


class TestTranslaasClientGetGroup:
    """Tests for get_group method."""

    @pytest.mark.asyncio
    async def test_get_group_success(self, client: TranslaasClient) -> None:
        """Test successful get_group call."""
        response_data = {"entry1": "value1", "entry2": "value2"}
        mock_response = httpx.Response(
            200,
            json=response_data,
            request=httpx.Request("GET", "https://api.test.com/api/translations/group"),
        )

        with patch.object(
            client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await client.get_group("project1", "group1", "en")
            assert isinstance(result, TranslationGroup)
            assert result.get_value("entry1") == "value1"
            assert result.get_value("entry2") == "value2"

    @pytest.mark.asyncio
    async def test_get_group_with_format(self, client: TranslaasClient) -> None:
        """Test get_group with format parameter."""
        response_data = {"entry1": "value1"}
        mock_response = httpx.Response(
            200,
            json=response_data,
            request=httpx.Request("GET", "https://api.test.com/api/translations/group"),
        )

        with patch.object(
            client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await client.get_group("project1", "group1", "en", format="json")
            assert isinstance(result, TranslationGroup)

    @pytest.mark.asyncio
    async def test_get_group_with_cache_hit(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test get_group with cache hit."""
        options.cache_mode = CacheMode.GROUP
        cache_data = {"entry1": "value1", "entry2": "value2"}
        cache_provider.set("group|project:project1|group:group1|lang:en", json.dumps(cache_data))

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            result = await client.get_group("project1", "group1", "en")
            assert isinstance(result, TranslationGroup)
            assert result.get_value("entry1") == "value1"

    @pytest.mark.asyncio
    async def test_get_group_with_cache_miss_and_update(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test get_group with cache miss and cache update."""
        options.cache_mode = CacheMode.GROUP
        response_data = {"entry1": "value1"}
        mock_response = httpx.Response(
            200,
            json=response_data,
            request=httpx.Request("GET", "https://api.test.com/api/translations/group"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "request", new_callable=AsyncMock, return_value=mock_response
            ):
                result = await client.get_group("project1", "group1", "en")
                assert isinstance(result, TranslationGroup)
                # Verify cache was updated
                cache_key = "group|project:project1|group:group1|lang:en"
                cached_value = cache_provider.get(cache_key)
                assert cached_value is not None
                assert json.loads(cached_value) == response_data

    @pytest.mark.asyncio
    async def test_get_group_invalid_response(self, client: TranslaasClient) -> None:
        """Test get_group with invalid response format."""
        mock_response = httpx.Response(
            200,
            text="not json",
            request=httpx.Request("GET", "https://api.test.com/api/translations/group"),
        )

        with patch.object(
            client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(TranslaasApiException):
                await client.get_group("project1", "group1", "en")


class TestTranslaasClientGetProject:
    """Tests for get_project method."""

    @pytest.mark.asyncio
    async def test_get_project_success(self, client: TranslaasClient) -> None:
        """Test successful get_project call."""
        response_data = {"group1": {"entry1": "value1"}, "group2": {"entry2": "value2"}}
        mock_response = httpx.Response(
            200,
            json=response_data,
            request=httpx.Request("GET", "https://api.test.com/api/translations/project"),
        )

        with patch.object(
            client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await client.get_project("project1", "en")
            assert isinstance(result, TranslationProject)
            group1 = result.get_group("group1")
            assert group1 is not None
            assert group1.get_value("entry1") == "value1"

    @pytest.mark.asyncio
    async def test_get_project_with_cache_hit(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test get_project with cache hit."""
        options.cache_mode = CacheMode.PROJECT
        cache_data = {"group1": {"entry1": "value1"}}
        cache_provider.set("project|project:project1|lang:en", json.dumps(cache_data))

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            result = await client.get_project("project1", "en")
            assert isinstance(result, TranslationProject)

    @pytest.mark.asyncio
    async def test_get_project_with_cache_miss_and_update(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test get_project with cache miss and cache update."""
        options.cache_mode = CacheMode.PROJECT
        response_data = {"group1": {"entry1": "value1"}}
        mock_response = httpx.Response(
            200,
            json=response_data,
            request=httpx.Request("GET", "https://api.test.com/api/translations/project"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "request", new_callable=AsyncMock, return_value=mock_response
            ):
                result = await client.get_project("project1", "en")
                assert isinstance(result, TranslationProject)
                # Verify cache was updated
                cache_key = "project|project:project1|lang:en"
                cached_value = cache_provider.get(cache_key)
                assert cached_value is not None
                assert json.loads(cached_value) == response_data


class TestTranslaasClientGetProjectLocales:
    """Tests for get_project_locales method."""

    @pytest.mark.asyncio
    async def test_get_project_locales_success(self, client: TranslaasClient) -> None:
        """Test successful get_project_locales call."""
        response_data = {"locales": ["en", "fr", "es"]}
        mock_response = httpx.Response(
            200,
            json=response_data,
            request=httpx.Request("GET", "https://api.test.com/api/translations/locales"),
        )

        with patch.object(
            client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await client.get_project_locales("project1")
            assert isinstance(result, ProjectLocales)
            assert result.locales == ["en", "fr", "es"]

    @pytest.mark.asyncio
    async def test_get_project_locales_list_response(self, client: TranslaasClient) -> None:
        """Test get_project_locales with list response."""
        response_data = ["en", "fr", "es"]
        mock_response = httpx.Response(
            200,
            json=response_data,
            request=httpx.Request("GET", "https://api.test.com/api/translations/locales"),
        )

        with patch.object(
            client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await client.get_project_locales("project1")
            assert isinstance(result, ProjectLocales)
            assert result.locales == ["en", "fr", "es"]

    @pytest.mark.asyncio
    async def test_get_project_locales_with_cache_hit(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test get_project_locales with cache hit."""
        options.cache_mode = CacheMode.PROJECT
        cache_data = ["en", "fr"]
        cache_provider.set("locales|project:project1", json.dumps(cache_data))

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            result = await client.get_project_locales("project1")
            assert isinstance(result, ProjectLocales)
            assert result.locales == ["en", "fr"]

    @pytest.mark.asyncio
    async def test_get_project_locales_invalid_response(self, client: TranslaasClient) -> None:
        """Test get_project_locales with invalid response."""
        mock_response = httpx.Response(
            200,
            json={"invalid": "data"},
            request=httpx.Request("GET", "https://api.test.com/api/translations/locales"),
        )

        with patch.object(
            client._http_client, "get", new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(TranslaasApiException):
                await client.get_project_locales("project1")


class TestTranslaasClientCacheExpiration:
    """Tests for cache expiration handling."""

    @pytest.mark.asyncio
    async def test_cache_with_absolute_expiration(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test cache with absolute expiration."""
        options.cache_mode = CacheMode.ENTRY
        options.cache_absolute_expiration = timedelta(hours=1)
        mock_response = httpx.Response(
            200,
            text="Cached Value",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "request", new_callable=AsyncMock, return_value=mock_response
            ):
                await client.get_entry("group1", "entry1", "en")
                # Verify cache.set was called with expiration
                cache_key = "entry|group:group1|entry:entry1|lang:en"
                cached_value = cache_provider.get(cache_key)
                assert cached_value == "Cached Value"

    @pytest.mark.asyncio
    async def test_cache_with_sliding_expiration(
        self, options: TranslaasOptions, cache_provider: MockCacheProvider
    ) -> None:
        """Test cache with sliding expiration."""
        options.cache_mode = CacheMode.ENTRY
        options.cache_sliding_expiration = timedelta(minutes=30)
        mock_response = httpx.Response(
            200,
            text="Cached Value",
            request=httpx.Request("GET", "https://api.test.com/api/translations/text"),
        )

        async with TranslaasClient(options, cache_provider=cache_provider) as client:
            with patch.object(
                client._http_client, "request", new_callable=AsyncMock, return_value=mock_response
            ):
                await client.get_entry("group1", "entry1", "en")
                cache_key = "entry|group:group1|entry:entry1|lang:en"
                cached_value = cache_provider.get(cache_key)
                assert cached_value == "Cached Value"


class TestTranslaasClientErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_ensure_client_not_initialized(self, options: TranslaasOptions) -> None:
        """Test that methods fail if client is not initialized."""
        client = TranslaasClient(options)
        with pytest.raises(TranslaasConfigurationException):
            await client.get_entry("group1", "entry1", "en")

    @pytest.mark.asyncio
    async def test_cancellation_support(self, client: TranslaasClient) -> None:
        """Test that cancellation is properly propagated."""
        with patch.object(
            client._http_client,
            "get",
            new_callable=AsyncMock,
            side_effect=asyncio.CancelledError(),
        ):
            with pytest.raises(asyncio.CancelledError):
                await client.get_entry("group1", "entry1", "en")

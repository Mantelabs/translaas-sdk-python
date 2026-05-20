"""Tests for 204/304 HTTP semantics (.NET parity)."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from translaas.client.client import TranslaasClient
from translaas.models.enums import CacheMode
from translaas.models.options import TranslaasOptions
from translaas.models.request_context import TranslaasRequestContext
from translaas.models.responses import TranslationGroup, TranslationProject


@pytest.fixture
def options() -> TranslaasOptions:
    return TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
    )


@pytest.mark.asyncio
async def test_get_entry_204_returns_entry_key(options: TranslaasOptions) -> None:
    async with TranslaasClient(options) as client:
        resp = httpx.Response(
            204,
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/text"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock, return_value=resp):
            result = await client.get_entry("g", "missing-key", "en")
        assert result == "missing-key"


@pytest.mark.asyncio
async def test_get_entry_304_returns_empty_without_cache(options: TranslaasOptions) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        use_conditional_requests=True,
    )
    ctx = TranslaasRequestContext(if_none_match='W/"abc"')
    async with TranslaasClient(opts) as client:
        resp = httpx.Response(
            304,
            headers={"ETag": 'W/"abc"'},
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/text"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock, return_value=resp):
            result = await client.get_entry("g", "e", "en", request_context=ctx)
        assert result == ""
        assert ctx.not_modified is True


@pytest.mark.asyncio
async def test_get_group_204_returns_empty_group(options: TranslaasOptions) -> None:
    async with TranslaasClient(options) as client:
        resp = httpx.Response(
            204,
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/group"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock, return_value=resp):
            result = await client.get_group("p", "g", "en")
        assert result.entries == {}


@pytest.mark.asyncio
async def test_get_project_304_empty_project(options: TranslaasOptions) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        use_conditional_requests=True,
    )
    async with TranslaasClient(opts) as client:
        resp = httpx.Response(
            304,
            headers={"ETag": 'W/"x"'},
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/project"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock, return_value=resp):
            result = await client.get_project("p", "en")
        assert isinstance(result, TranslationProject)
        assert result.groups == {}


@pytest.mark.asyncio
async def test_report_missing_empty_skips_http(options: TranslaasOptions) -> None:
    async with TranslaasClient(options) as client:
        with patch.object(client._http_client, "post", new_callable=AsyncMock) as mock_post:
            await client.report_missing_keys([])
        mock_post.assert_not_called()

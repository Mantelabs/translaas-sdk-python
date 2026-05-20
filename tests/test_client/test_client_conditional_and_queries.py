"""Tests for conditional requests (ETag/304), query flags, and custom API key header."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from tests.conftest import MockCacheProvider
from translaas.caching.cache_key_builder import CacheKeyBuilder
from translaas.client.client import TranslaasClient
from translaas.exceptions import TranslaasApiException
from translaas.models.enums import CacheMode
from translaas.models.options import TranslaasOptions
from translaas.models.sdk_payloads import ReportMissingKeyItem


def _params_from_get_call(mock_get: AsyncMock) -> dict[str, str]:
    _args, kwargs = mock_get.call_args
    params = kwargs.get("params")
    assert params is not None
    return dict(params)


def _headers_from_get_call(mock_get: AsyncMock) -> dict[str, str]:
    _args, kwargs = mock_get.call_args
    h = kwargs.get("headers") or {}
    return dict(h)


@pytest.mark.asyncio
async def test_custom_api_key_header_on_http_client() -> None:
    opts = TranslaasOptions(
        api_key="secret",
        base_url="https://api.test.com",
        api_key_header="X-Custom-Key",
    )
    async with TranslaasClient(opts) as client:
        assert client._http_client is not None
        assert client._http_client.headers["X-Custom-Key"] == "secret"


@pytest.mark.asyncio
async def test_get_entry_includes_default_project(cache_provider: MockCacheProvider) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        default_project="proj-default",
        cache_mode=CacheMode.NONE,
    )
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        mock_resp = httpx.Response(
            200,
            text="ok",
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/text"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            await client.get_entry("g", "e", "en")
        params = _params_from_get_call(mock_get)
        assert params["project"] == "proj-default"


@pytest.mark.asyncio
async def test_options_channel_and_snapshot_on_sdk_gets(cache_provider: MockCacheProvider) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        channel="beta",
        snapshot_version="42",
    )
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        mock_resp = httpx.Response(
            200,
            json={"entries": {}},
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/group"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            await client.get_group("p", "g", "en")
        params = _params_from_get_call(mock_get)
        assert params["channel"] == "beta"
        assert params["v"] == "42"


@pytest.mark.asyncio
async def test_per_call_channel_overrides_options_channel(
    cache_provider: MockCacheProvider
) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        channel="from-options",
    )
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        mock_resp = httpx.Response(
            200,
            json={"locales": ["en"]},
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/locales"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            await client.get_project_locales("p", channel="from-call")
        params = _params_from_get_call(mock_get)
        assert params["channel"] == "from-call"


@pytest.mark.asyncio
async def test_include_context_from_options_on_group_and_offline(
    cache_provider: MockCacheProvider,
) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        include_context=True,
    )
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        group_resp = httpx.Response(
            200,
            json={"entries": {"x": "y"}},
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/group"),
        )
        zip_resp = httpx.Response(
            200,
            content=b"z",
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/offline-cache"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [group_resp, zip_resp]
            await client.get_group("p", "g", "en")
            assert _params_from_get_call(mock_get)["includeContext"] == "true"
            await client.get_offline_cache("p")
            assert _params_from_get_call(mock_get)["includeContext"] == "true"


@pytest.mark.asyncio
async def test_include_context_per_call_false_overrides_options_true(
    cache_provider: MockCacheProvider,
) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        include_context=True,
    )
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        mock_resp = httpx.Response(
            200,
            json={"entries": {}},
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/group"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            await client.get_group("p", "g", "en", include_context=False)
        assert _params_from_get_call(mock_get)["includeContext"] == "false"


@pytest.mark.asyncio
async def test_get_group_with_flat_json_format(cache_provider: MockCacheProvider) -> None:
    opts = TranslaasOptions(api_key="k", base_url="https://api.test.com", cache_mode=CacheMode.NONE)
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        mock_resp = httpx.Response(
            200,
            json={"entry.a": "va", "entry.b": "vb"},
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/group"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            g = await client.get_group("p", "g", "en", format="flat-json")
        params = _params_from_get_call(mock_get)
        assert params["format"] == "flat-json"
        assert g.get_value("entry.a") == "va"


@pytest.mark.asyncio
async def test_get_project_with_flat_json_format(cache_provider: MockCacheProvider) -> None:
    opts = TranslaasOptions(api_key="k", base_url="https://api.test.com", cache_mode=CacheMode.NONE)
    flat = {"common.welcome": "Hello", "errors.404": "Missing"}
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        mock_resp = httpx.Response(
            200,
            json=flat,
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/project"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            p = await client.get_project("p", "en", format="flat-json")
        assert _params_from_get_call(mock_get)["format"] == "flat-json"
        assert p.groups["common"]["welcome"] == "Hello"
        assert p.groups["errors"]["404"] == "Missing"


@pytest.mark.asyncio
async def test_conditional_get_entry_304_uses_seeded_cache(
    cache_provider: MockCacheProvider,
) -> None:
    """304 fallback uses the same cache key as the text entry (see client.get_entry).

    With ``CacheMode.ENTRY``, a second in-process call returns from the memory cache
    before HTTP, so we use ``NONE`` and seed etag + body to exercise the 304 branch.
    """
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        use_conditional_requests=True,
    )
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        cache_key = CacheKeyBuilder.build_entry_key("g", "e", "en")
        client._etag_by_resource[cache_key] = 'W/"etag-1"'
        cache_provider.set(cache_key, "body-after-304")
        r304 = httpx.Response(
            304,
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/text"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = r304
            out = await client.get_entry("g", "e", "en")
        assert out == "body-after-304"
        assert _headers_from_get_call(mock_get).get("If-None-Match") == 'W/"etag-1"'


@pytest.mark.asyncio
async def test_conditional_get_entry_304_without_cache_returns_empty() -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        use_conditional_requests=True,
    )
    async with TranslaasClient(opts) as client:
        r1 = httpx.Response(
            200,
            text="only-etag",
            headers={"etag": "v1"},
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/text"),
        )
        r304 = httpx.Response(
            304,
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/text"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [r1, r304]
            await client.get_entry("g", "e", "en")
            assert await client.get_entry("g", "e", "en") == ""


@pytest.mark.asyncio
async def test_conditional_get_project_304_uses_json_cache(
    cache_provider: MockCacheProvider,
) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        use_conditional_requests=True,
    )
    payload = {"groups": {"g": {"e": "v"}}}
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        cache_key = CacheKeyBuilder.build_project_key("p", "en")
        client._etag_by_resource[cache_key] = "pv1"
        cache_provider.set(cache_key, json.dumps(payload))
        r304 = httpx.Response(
            304,
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/project"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = r304
            p = await client.get_project("p", "en")
        g = p.get_group("g")
        assert g is not None
        assert g.get_value("e") == "v"


@pytest.mark.asyncio
async def test_conditional_get_project_locales_304_uses_cache(
    cache_provider: MockCacheProvider,
) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        use_conditional_requests=True,
    )
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        cache_key = CacheKeyBuilder.build_locales_key("p")
        client._etag_by_resource[cache_key] = "loc1"
        cache_provider.set(cache_key, json.dumps({"locales": ["en", "de"]}))
        r304 = httpx.Response(
            304,
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/locales"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = r304
            loc = await client.get_project_locales("p")
        assert loc.locales == ["en", "de"]


@pytest.mark.asyncio
async def test_conditional_get_group_304_uses_json_cache(cache_provider: MockCacheProvider) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        use_conditional_requests=True,
    )
    payload = {"entries": {"k": "v"}}
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        cache_key = CacheKeyBuilder.build_group_key("p", "g", "en")
        client._etag_by_resource[cache_key] = "grp1"
        cache_provider.set(cache_key, json.dumps(payload))
        r304 = httpx.Response(
            304,
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/group"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = r304
            g = await client.get_group("p", "g", "en")
        assert g.get_value("k") == "v"


@pytest.mark.asyncio
async def test_conditional_get_group_304_without_cache_returns_empty(
    cache_provider: MockCacheProvider,
) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        use_conditional_requests=True,
    )
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        r1 = httpx.Response(
            200,
            json={"entries": {"k": "v"}},
            headers={"ETag": "g1"},
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/group"),
        )
        r304 = httpx.Response(
            304,
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/group"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [r1, r304]
            await client.get_group("p", "g", "en")
            g = await client.get_group("p", "g", "en")
            assert g.entries == {}


@pytest.mark.asyncio
async def test_get_offline_cache_passes_channel_and_v_per_call(
    cache_provider: MockCacheProvider,
) -> None:
    opts = TranslaasOptions(api_key="k", base_url="https://api.test.com", cache_mode=CacheMode.NONE)
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        mock_resp = httpx.Response(
            200,
            content=b"z",
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/offline-cache"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            await client.get_offline_cache("p", channel="ch", snapshot_version="7")
        params = _params_from_get_call(mock_get)
        assert params["project"] == "p"
        assert params["channel"] == "ch"
        assert params["v"] == "7"


@pytest.mark.asyncio
async def test_conditional_get_project_304_without_cache_returns_empty(
    cache_provider: MockCacheProvider,
) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        use_conditional_requests=True,
    )
    payload = {"groups": {"g": {"e": "v"}}}
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        r1 = httpx.Response(
            200,
            json=payload,
            headers={"ETag": "P1"},
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/project"),
        )
        r304 = httpx.Response(
            304,
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/project"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [r1, r304]
            await client.get_project("p", "en")
            p = await client.get_project("p", "en")
            assert p.groups == {}


@pytest.mark.asyncio
async def test_conditional_get_project_locales_304_without_cache_returns_empty(
    cache_provider: MockCacheProvider,
) -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        cache_mode=CacheMode.NONE,
        use_conditional_requests=True,
    )
    async with TranslaasClient(opts, cache_provider=cache_provider) as client:
        r1 = httpx.Response(
            200,
            json={"locales": ["en"]},
            headers={"ETag": "L1"},
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/locales"),
        )
        r304 = httpx.Response(
            304,
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/locales"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [r1, r304]
            await client.get_project_locales("p")
            loc = await client.get_project_locales("p")
            assert loc.locales == []


@pytest.mark.asyncio
async def test_offline_cache_304_returns_not_modified() -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        use_conditional_requests=True,
    )
    async with TranslaasClient(opts) as client:
        r304 = httpx.Response(
            304,
            headers={"ETag": 'W/"off"'},
            request=httpx.Request("GET", "https://api.test.com/sdk/v1/translations/offline-cache"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = r304
            result = await client.get_offline_cache("p")
        assert result.not_modified is True
        assert result.content is None


@pytest.mark.asyncio
async def test_validate_api_key_non_json_body_raises_json_error() -> None:
    opts = TranslaasOptions(api_key="k", base_url="https://api.test.com")
    async with TranslaasClient(opts) as client:
        mock_resp = httpx.Response(
            200,
            text="nope",
            request=httpx.Request("GET", "https://api.test.com/api/v1/api-keys/validate"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            with pytest.raises(json.JSONDecodeError):
                await client.validate_api_key()


@pytest.mark.asyncio
async def test_validate_api_key_list_json_raises() -> None:
    opts = TranslaasOptions(api_key="k", base_url="https://api.test.com")
    async with TranslaasClient(opts) as client:
        mock_resp = httpx.Response(
            200,
            json=[],
            request=httpx.Request("GET", "https://api.test.com/api/v1/api-keys/validate"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            with pytest.raises(TranslaasApiException, match="Invalid validate response"):
                await client.validate_api_key()


@pytest.mark.asyncio
async def test_validate_api_key_http_error_401() -> None:
    opts = TranslaasOptions(api_key="k", base_url="https://api.test.com")
    async with TranslaasClient(opts) as client:
        mock_resp = httpx.Response(
            401,
            request=httpx.Request("GET", "https://api.test.com/api/v1/api-keys/validate"),
        )
        with patch.object(client._http_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            with pytest.raises(TranslaasApiException):
                await client.validate_api_key()


@pytest.mark.asyncio
async def test_report_missing_keys_no_raise_on_202() -> None:
    opts = TranslaasOptions(api_key="k", base_url="https://api.test.com")
    async with TranslaasClient(opts) as client:
        mock_resp = httpx.Response(
            202,
            request=httpx.Request(
                "POST", "https://api.test.com/sdk/v1/translations/report-missing"
            ),
        )
        with patch.object(client._http_client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            await client.report_missing_keys([ReportMissingKeyItem("a", "b", "en")])


@pytest.mark.asyncio
async def test_report_missing_keys_400_raises() -> None:
    opts = TranslaasOptions(api_key="k", base_url="https://api.test.com")
    async with TranslaasClient(opts) as client:
        mock_resp = httpx.Response(
            400,
            request=httpx.Request(
                "POST", "https://api.test.com/sdk/v1/translations/report-missing"
            ),
        )
        with patch.object(client._http_client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            with pytest.raises(TranslaasApiException):
                await client.report_missing_keys(
                    [ReportMissingKeyItem("g", "e", "en")]
                )


@pytest.mark.asyncio
async def test_report_missing_non_202_raises_when_not_successful() -> None:
    opts = TranslaasOptions(api_key="k", base_url="https://api.test.com")
    async with TranslaasClient(opts) as client:
        mock_resp = httpx.Response(
            500,
            request=httpx.Request(
                "POST", "https://api.test.com/sdk/v1/translations/report-missing"
            ),
        )
        with patch.object(client._http_client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            with pytest.raises(TranslaasApiException):
                await client.report_missing_keys(
                    [ReportMissingKeyItem("g", "e", "en")]
                )


@pytest.mark.asyncio
async def test_empty_api_key_header_falls_back_to_default() -> None:
    opts = TranslaasOptions(
        api_key="k",
        base_url="https://api.test.com",
        api_key_header="   ",
    )
    async with TranslaasClient(opts) as client:
        assert client._http_client is not None
        assert client._http_client.headers["X-Api-Key"] == "k"

"""Tests for TranslaasService request context forwarding."""

from unittest.mock import AsyncMock, patch

import pytest

from translaas.models.request_context import SdkTranslationQueryParams, TranslaasRequestContext
from translaas.models.options import TranslaasOptions
from translaas.service import TranslaasService


@pytest.mark.asyncio
async def test_t_forwards_merged_request_context() -> None:
    options = TranslaasOptions(
        api_key="key",
        base_url="https://api.test.com",
        default_project="default-proj",
        default_language="en",
    )
    service = TranslaasService(options)

    mock_client = AsyncMock()
    mock_client.get_entry = AsyncMock(return_value="hello")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "translaas.service.create_translaas_client", return_value=mock_client
    ):
        async with service:
            await service.t(
                "common",
                "welcome",
                "en",
                sdk_query=SdkTranslationQueryParams(channel="beta", v="v1"),
            )

    mock_client.get_entry.assert_awaited_once()
    call_kwargs = mock_client.get_entry.await_args.kwargs
    ctx = call_kwargs["request_context"]
    assert isinstance(ctx, TranslaasRequestContext)
    assert ctx.channel == "beta"
    assert ctx.version == "v1"
    assert call_kwargs["project"] == "default-proj"


@pytest.mark.asyncio
async def test_get_group_forwards_request_context() -> None:
    from translaas.models.responses import TranslationGroup

    options = TranslaasOptions(api_key="key", base_url="https://api.test.com")
    service = TranslaasService(options)

    mock_client = AsyncMock()
    mock_client.get_group = AsyncMock(return_value=TranslationGroup(entries={}))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    ctx_in = TranslaasRequestContext(if_none_match='"abc"')

    with patch(
        "translaas.service.create_translaas_client", return_value=mock_client
    ):
        async with service:
            await service.get_group(
                "proj",
                "common",
                "en",
                request_context=ctx_in,
                channel="stable",
            )

    call_kwargs = mock_client.get_group.await_args.kwargs
    assert call_kwargs["request_context"].channel == "stable"
    assert call_kwargs["request_context"].if_none_match == '"abc"'

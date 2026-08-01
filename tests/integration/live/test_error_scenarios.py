"""Live API error scenario integration tests."""

from __future__ import annotations

from datetime import timedelta

import pytest

from tests.integration.live.helpers import (
    FIXTURE_ENTRY_SAVE,
    FIXTURE_GROUP,
    FIXTURE_LANG,
    LiveConfig,
    build_options,
    is_sdk_not_found,
)
from translaas.client.client import TranslaasClient
from translaas.exceptions import TranslaasApiException

pytestmark = pytest.mark.live


@pytest.mark.asyncio
async def test_error_invalid_api_key(require_reachable_api: LiveConfig) -> None:
    options = build_options(require_reachable_api, api_key="invalid-api-key-12345")
    async with TranslaasClient(options) as client:
        with pytest.raises(TranslaasApiException) as exc_info:
            await client.get_entry(FIXTURE_GROUP, FIXTURE_ENTRY_SAVE, FIXTURE_LANG)
    assert exc_info.value.status_code in (401, 403)


@pytest.mark.asyncio
async def test_error_invalid_base_url(live_config: LiveConfig) -> None:
    options = build_options(
        live_config,
        base_url="https://invalid-url-that-does-not-exist-12345.com",
    )
    async with TranslaasClient(options) as client:
        with pytest.raises(TranslaasApiException):
            await client.get_entry(FIXTURE_GROUP, FIXTURE_ENTRY_SAVE, FIXTURE_LANG)


@pytest.mark.asyncio
async def test_error_request_timeout(require_reachable_api: LiveConfig) -> None:
    options = build_options(require_reachable_api, timeout=timedelta(milliseconds=1))
    async with TranslaasClient(options) as client:
        with pytest.raises(TranslaasApiException) as exc_info:
            await client.get_entry(FIXTURE_GROUP, FIXTURE_ENTRY_SAVE, FIXTURE_LANG)

    exc = exc_info.value
    if exc.status_code == 408:
        assert "timed out" in exc.message.lower()
    else:
        assert "timed out" in exc.message.lower() or (
            exc.inner_error is not None and "timeout" in type(exc.inner_error).__name__.lower()
        )


@pytest.mark.asyncio
async def test_error_entry_not_found_returns_key(integration_client: TranslaasClient) -> None:
    entry = "nonexistent-entry"
    try:
        got = await integration_client.get_entry("nonexistent-group", entry, "nonexistent-lang")
    except TranslaasApiException as exc:
        if is_sdk_not_found(exc):
            return
        raise
    else:
        assert got == entry

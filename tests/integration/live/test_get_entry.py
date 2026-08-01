"""Live get_entry integration tests."""

from __future__ import annotations

import pytest

from tests.integration.live.helpers import (
    FIXTURE_ENTRY_PLURAL,
    FIXTURE_ENTRY_SAVE,
    FIXTURE_GROUP,
    FIXTURE_GROUP_MESSAGES,
    FIXTURE_LANG,
    LiveConfig,
    is_sdk_not_found,
    soft_skip_if,
    soft_skip_on_sdk_not_found,
)
from translaas.client.client import TranslaasClient
from translaas.exceptions import TranslaasApiException

pytestmark = pytest.mark.live


@pytest.mark.asyncio
async def test_get_entry_existing(integration_client: TranslaasClient) -> None:
    try:
        got = await integration_client.get_entry(FIXTURE_GROUP, FIXTURE_ENTRY_SAVE, FIXTURE_LANG)
    except TranslaasApiException as exc:
        soft_skip_on_sdk_not_found(exc)
        raise

    soft_skip_if(
        not got or got == FIXTURE_ENTRY_SAVE,
        "fixture data not available in API",
    )
    assert got


@pytest.mark.asyncio
async def test_get_entry_with_pluralization(integration_client: TranslaasClient) -> None:
    try:
        got = await integration_client.get_entry(
            FIXTURE_GROUP_MESSAGES,
            FIXTURE_ENTRY_PLURAL,
            FIXTURE_LANG,
            number=5.0,
        )
    except TranslaasApiException as exc:
        soft_skip_on_sdk_not_found(exc)
        raise

    soft_skip_if(
        not got or got == FIXTURE_ENTRY_PLURAL,
        "fixture data not available in API",
    )
    assert got


@pytest.mark.asyncio
async def test_get_entry_not_found_returns_entry_key(integration_client: TranslaasClient) -> None:
    entry = "nonexistent.entry"
    try:
        got = await integration_client.get_entry("nonexistent", entry, FIXTURE_LANG)
    except TranslaasApiException as exc:
        if is_sdk_not_found(exc):
            return
        raise
    else:
        assert got == entry


@pytest.mark.asyncio
async def test_get_entry_invalid_api_key(require_reachable_api: LiveConfig) -> None:
    from tests.integration.live.helpers import build_options

    options = build_options(require_reachable_api, api_key="invalid-api-key")
    async with TranslaasClient(options) as client:
        with pytest.raises(TranslaasApiException) as exc_info:
            await client.get_entry(FIXTURE_GROUP, FIXTURE_ENTRY_SAVE, FIXTURE_LANG)
    assert exc_info.value.status_code in (401, 403)

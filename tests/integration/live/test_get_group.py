"""Live get_group integration tests."""

from __future__ import annotations

import pytest

from tests.integration.live.helpers import (
    FIXTURE_GROUP,
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
async def test_get_group_existing(integration_client: TranslaasClient, live_config: LiveConfig) -> None:
    try:
        got = await integration_client.get_group(
            live_config.default_project,
            FIXTURE_GROUP,
            FIXTURE_LANG,
        )
    except TranslaasApiException as exc:
        soft_skip_on_sdk_not_found(exc)
        raise

    soft_skip_if(not got.entries, "fixture data not available in API")
    assert got.entries


@pytest.mark.asyncio
async def test_get_group_with_format(integration_client: TranslaasClient, live_config: LiveConfig) -> None:
    try:
        got = await integration_client.get_group(
            live_config.default_project,
            FIXTURE_GROUP,
            FIXTURE_LANG,
            format="json",
        )
    except TranslaasApiException as exc:
        soft_skip_on_sdk_not_found(exc)
        raise

    soft_skip_if(not got.entries, "fixture data not available in API")
    assert got.entries


@pytest.mark.asyncio
async def test_get_group_not_found(integration_client: TranslaasClient, live_config: LiveConfig) -> None:
    try:
        got = await integration_client.get_group(
            live_config.default_project,
            "nonexistent-group",
            FIXTURE_LANG,
        )
    except TranslaasApiException as exc:
        if is_sdk_not_found(exc):
            return
        raise
    else:
        assert not got.entries


@pytest.mark.asyncio
async def test_get_group_project_not_found(integration_client: TranslaasClient) -> None:
    try:
        got = await integration_client.get_group("nonexistent-project", FIXTURE_GROUP, FIXTURE_LANG)
    except TranslaasApiException as exc:
        if is_sdk_not_found(exc):
            return
        raise
    else:
        assert not got.entries

"""Live get_project integration tests."""

from __future__ import annotations

import pytest

from tests.integration.live.helpers import (
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
async def test_get_project_existing(integration_client: TranslaasClient, live_config: LiveConfig) -> None:
    try:
        got = await integration_client.get_project(live_config.default_project, FIXTURE_LANG)
    except TranslaasApiException as exc:
        soft_skip_on_sdk_not_found(exc)
        raise

    soft_skip_if(not got.groups, "fixture data not available in API")
    assert got.groups
    assert "Version" not in got.groups
    assert "version" not in got.groups


@pytest.mark.asyncio
async def test_get_project_with_format(integration_client: TranslaasClient, live_config: LiveConfig) -> None:
    try:
        got = await integration_client.get_project(
            live_config.default_project,
            FIXTURE_LANG,
            format="json",
        )
    except TranslaasApiException as exc:
        soft_skip_on_sdk_not_found(exc)
        raise

    soft_skip_if(not got.groups, "fixture data not available in API")
    assert got.groups


@pytest.mark.asyncio
async def test_get_project_not_found(integration_client: TranslaasClient) -> None:
    try:
        got = await integration_client.get_project("nonexistent-project", FIXTURE_LANG)
    except TranslaasApiException as exc:
        if is_sdk_not_found(exc):
            return
        raise
    else:
        assert not got.groups


@pytest.mark.asyncio
async def test_get_project_multiple_groups(integration_client: TranslaasClient, live_config: LiveConfig) -> None:
    try:
        got = await integration_client.get_project(live_config.default_project, FIXTURE_LANG)
    except TranslaasApiException as exc:
        soft_skip_on_sdk_not_found(exc)
        raise

    soft_skip_if(not got.groups, "fixture data not available in API")

    walked = 0
    for group_name in got.groups:
        group = got.get_group(group_name)
        if group is None or not group.entries:
            continue
        walked += 1

    soft_skip_if(walked == 0, "fixture data not available in API")
    assert walked > 0

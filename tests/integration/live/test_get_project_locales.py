"""Live get_project_locales integration tests."""

from __future__ import annotations

import pytest

from tests.integration.live.helpers import (
    COMMON_LOCALES,
    LiveConfig,
    is_sdk_not_found,
    soft_skip_if,
    soft_skip_on_sdk_not_found,
)
from translaas.client.client import TranslaasClient
from translaas.exceptions import TranslaasApiException

pytestmark = pytest.mark.live


@pytest.mark.asyncio
async def test_get_project_locales_existing(
    integration_client: TranslaasClient,
    live_config: LiveConfig,
) -> None:
    try:
        got = await integration_client.get_project_locales(live_config.default_project)
    except TranslaasApiException as exc:
        soft_skip_on_sdk_not_found(exc)
        raise

    soft_skip_if(not got.locales, "fixture data not available in API")
    assert got.locales


@pytest.mark.asyncio
async def test_get_project_locales_common(
    integration_client: TranslaasClient,
    live_config: LiveConfig,
) -> None:
    try:
        got = await integration_client.get_project_locales(live_config.default_project)
    except TranslaasApiException as exc:
        soft_skip_on_sdk_not_found(exc)
        raise

    soft_skip_if(not got.locales, "fixture data not available in API")
    found = any(locale in COMMON_LOCALES for locale in got.locales)
    soft_skip_if(not found, "expected at least one common locale in fixture API")
    assert found


@pytest.mark.asyncio
async def test_get_project_locales_not_found(integration_client: TranslaasClient) -> None:
    try:
        got = await integration_client.get_project_locales("nonexistent-project")
    except TranslaasApiException as exc:
        if is_sdk_not_found(exc):
            return
        raise
    else:
        assert not got.locales

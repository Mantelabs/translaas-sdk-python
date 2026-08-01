"""Pytest fixtures for live API integration tests."""

from __future__ import annotations

from typing import AsyncIterator

import pytest

from tests.integration.live.helpers import (
    LiveConfig,
    build_options,
    ensure_api_reachable,
    load_live_config,
)
from translaas.client.client import TranslaasClient
from translaas.models.options import TranslaasOptions

pytestmark = pytest.mark.live


@pytest.fixture(scope="session")
def live_config() -> LiveConfig:
    """Session fixture providing live test configuration or skipping when unset."""
    cfg = load_live_config()
    if cfg is None:
        pytest.skip("TRANSLAAS_API_KEY not set — live tests disabled")
    return cfg


@pytest.fixture
async def require_reachable_api(live_config: LiveConfig) -> LiveConfig:
    """Provide live config when the API origin responds; skip otherwise."""
    if not await ensure_api_reachable(live_config):
        pytest.skip(
            f"integration API not reachable at {live_config.base_url} — "
            "start local Docker (profile `core`) or set TRANSLAAS_BASE_URL"
        )
    return live_config


@pytest.fixture
async def integration_client(require_reachable_api: LiveConfig) -> AsyncIterator[TranslaasClient]:
    """Yield a connected client when the API is reachable."""
    options = build_options(require_reachable_api)
    async with TranslaasClient(options) as client:
        yield client


@pytest.fixture
def integration_options(live_config: LiveConfig) -> TranslaasOptions:
    """SDK options for live tests (does not require API reachability)."""
    return build_options(live_config)

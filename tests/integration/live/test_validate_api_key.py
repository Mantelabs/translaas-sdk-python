"""Live validate_api_key integration tests."""

from __future__ import annotations

import pytest

from tests.integration.live.helpers import (
    FIXTURE_ENTRY_SAVE,
    FIXTURE_GROUP,
    FIXTURE_LANG,
    LiveConfig,
    build_options,
    soft_skip_if,
    soft_skip_on_sdk_not_found,
)
from translaas.client.client import TranslaasClient
from translaas.exceptions import TranslaasApiException
from translaas.models.sdk_payloads import resolve_default_project_id

pytestmark = pytest.mark.live


@pytest.mark.asyncio
async def test_validate_api_key_valid(integration_client: TranslaasClient) -> None:
    got = await integration_client.validate_api_key()
    assert got.is_valid


@pytest.mark.asyncio
async def test_build_with_resolved_project_single_project_key(require_reachable_api: LiveConfig) -> None:
    options = build_options(require_reachable_api)
    async with TranslaasClient(options) as client:
        validate = await client.validate_api_key()

    if validate.project_id is None or len(validate.project_ids) != 1:
        pytest.skip("API key is not single-project scoped")

    resolved_project = resolve_default_project_id(options.default_project, validate)
    resolved_options = build_options(require_reachable_api, default_project=resolved_project)

    async with TranslaasClient(resolved_options) as client:
        try:
            got = await client.get_entry(FIXTURE_GROUP, FIXTURE_ENTRY_SAVE, FIXTURE_LANG)
        except TranslaasApiException as exc:
            soft_skip_on_sdk_not_found(exc)
            raise

    soft_skip_if(got == FIXTURE_ENTRY_SAVE, "fixture data not available in API")
    assert got

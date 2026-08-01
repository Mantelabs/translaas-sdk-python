"""Live TranslaasService.t() integration tests."""

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
from translaas.exceptions import TranslaasApiException
from translaas.language.providers import DefaultLanguageProvider
from translaas.language.resolver import LanguageResolver
from translaas.service import TranslaasService

pytestmark = pytest.mark.live


@pytest.mark.asyncio
async def test_service_t_explicit_language(require_reachable_api: LiveConfig) -> None:
    options = build_options(require_reachable_api)
    resolver = LanguageResolver([DefaultLanguageProvider(FIXTURE_LANG)])
    async with TranslaasService(options, language_resolver=resolver) as service:
        try:
            got = await service.t(FIXTURE_GROUP, FIXTURE_ENTRY_SAVE, FIXTURE_LANG)
        except TranslaasApiException as exc:
            soft_skip_on_sdk_not_found(exc)
            raise

    soft_skip_if(got == FIXTURE_ENTRY_SAVE, "fixture data not available in API")
    assert got

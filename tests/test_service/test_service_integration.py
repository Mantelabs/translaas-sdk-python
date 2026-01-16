"""Integration tests for TranslaasService."""

from unittest.mock import AsyncMock, patch

import pytest

# Import shared fixtures from conftest
from tests.conftest import MockCacheProvider  # noqa: F401
from translaas.exceptions import TranslaasLanguageResolutionException
from translaas.language.providers import DefaultLanguageProvider
from translaas.language.resolver import LanguageResolver
from translaas.models.options import TranslaasOptions
from translaas.service import TranslaasService


@pytest.fixture
def options() -> TranslaasOptions:
    """Create test options."""
    return TranslaasOptions(
        api_key="test-api-key",
        base_url="https://api.test.com",
        default_language="en",
    )


@pytest.fixture
def language_resolver() -> LanguageResolver:
    """Create language resolver with default provider."""
    return LanguageResolver([DefaultLanguageProvider("fr")])


class TestTranslaasServiceIntegration:
    """Integration tests for TranslaasService."""

    @pytest.mark.asyncio
    async def test_full_workflow_with_language_resolver(
        self, options: TranslaasOptions, language_resolver: LanguageResolver
    ) -> None:
        """Test full workflow with language resolver."""
        service = TranslaasService(options, language_resolver=language_resolver)
        async with service:
            with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = "Bonjour {name}!"
                result = await service.t("common", "greeting", {"name": "John"})
                assert result == "Bonjour John!"
                mock_get.assert_called_once_with(
                    group="common",
                    entry="greeting",
                    lang="fr",
                    number=None,
                    parameters=None,
                )

    @pytest.mark.asyncio
    async def test_full_workflow_with_default_language(self, options: TranslaasOptions) -> None:
        """Test full workflow with default language from options."""
        service = TranslaasService(options)
        async with service:
            with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = "Hello {name}!"
                result = await service.t("common", "greeting", {"name": "John"})
                assert result == "Hello John!"
                mock_get.assert_called_once_with(
                    group="common",
                    entry="greeting",
                    lang="en",
                    number=None,
                    parameters=None,
                )

    @pytest.mark.asyncio
    async def test_full_workflow_with_pluralization(
        self, options: TranslaasOptions, language_resolver: LanguageResolver
    ) -> None:
        """Test full workflow with pluralization."""
        service = TranslaasService(options, language_resolver=language_resolver)
        async with service:
            with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = "Vous avez 5 messages"
                # Test pluralization with automatic language resolution
                result = await service.t("messages", "count", 5.0)
                assert result == "Vous avez 5 messages"
                mock_get.assert_called_once_with(
                    group="messages",
                    entry="count",
                    lang="fr",
                    number=5.0,
                    parameters=None,
                )

    @pytest.mark.asyncio
    async def test_parameter_replacement_with_double_braces(
        self, options: TranslaasOptions
    ) -> None:
        """Test parameter replacement with double braces format."""
        service = TranslaasService(options)
        async with service:
            with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = "Hello {{name}}, welcome to {{app}}!"
                result = await service.t(
                    "common", "welcome", "en", {"name": "John", "app": "Translaas"}
                )
                assert result == "Hello John, welcome to Translaas!"

    @pytest.mark.asyncio
    async def test_parameter_replacement_with_single_braces(
        self, options: TranslaasOptions
    ) -> None:
        """Test parameter replacement with single braces format."""
        service = TranslaasService(options)
        async with service:
            with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = "Hello {name}, welcome to {app}!"
                result = await service.t(
                    "common", "welcome", "en", {"name": "John", "app": "Translaas"}
                )
                assert result == "Hello John, welcome to Translaas!"

    @pytest.mark.asyncio
    async def test_all_overloads_work_correctly(
        self, options: TranslaasOptions, language_resolver: LanguageResolver
    ) -> None:
        """Test that all t() method overloads work correctly."""
        service = TranslaasService(options, language_resolver=language_resolver)
        async with service:
            with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = "Translation"

                # Test: t(group, entry)
                result1 = await service.t("group", "entry")
                assert result1 == "Translation"

                # Test: t(group, entry, number)
                result2 = await service.t("group", "entry", 5.0)
                assert result2 == "Translation"

                # Test: t(group, entry, parameters)
                result3 = await service.t("group", "entry", {"key": "value"})
                assert result3 == "Translation"

                # Test: t(group, entry, lang)
                result4 = await service.t("group", "entry", "es")
                assert result4 == "Translation"

                # Test: t(group, entry, lang, number)
                result5 = await service.t("group", "entry", "es", 5.0)
                assert result5 == "Translation"

                # Test: t(group, entry, lang, parameters)
                result6 = await service.t("group", "entry", "es", {"key": "value"})
                assert result6 == "Translation"

                # Verify all calls were made
                assert mock_get.call_count == 6

    @pytest.mark.asyncio
    async def test_language_resolution_priority(
        self, options: TranslaasOptions, language_resolver: LanguageResolver
    ) -> None:
        """Test that explicit language takes priority over resolver."""
        service = TranslaasService(options, language_resolver=language_resolver)
        async with service:
            with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = "Translation"
                # Explicit language should override resolver
                await service.t("group", "entry", "de")
                mock_get.assert_called_once_with(
                    group="group", entry="entry", lang="de", number=None, parameters=None
                )

    @pytest.mark.asyncio
    async def test_error_handling_api_exception(self, options: TranslaasOptions) -> None:
        """Test error handling when API raises exception."""
        from translaas.exceptions import TranslaasApiException

        service = TranslaasService(options)
        async with service:
            with patch.object(service._client, "get_entry", new_callable=AsyncMock) as mock_get:
                mock_get.side_effect = TranslaasApiException("API error", status_code=500)
                with pytest.raises(TranslaasApiException):
                    await service.t("group", "entry", "en")

    @pytest.mark.asyncio
    async def test_error_handling_language_resolution_failure(
        self, options: TranslaasOptions
    ) -> None:
        """Test error handling when language resolution fails."""
        # Remove default_language to force failure
        options.default_language = None
        service = TranslaasService(options)
        async with service:
            with pytest.raises(TranslaasLanguageResolutionException):
                await service.t("group", "entry")

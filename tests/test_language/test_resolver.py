"""Tests for language resolver."""

from typing import Optional
from unittest.mock import AsyncMock, Mock

import pytest

from translaas.exceptions import TranslaasLanguageResolutionException
from translaas.language.providers import (
    DefaultLanguageProvider,
    RequestLanguageProvider,
)
from translaas.language.resolver import LanguageResolver


class TestLanguageResolver:
    """Tests for LanguageResolver."""

    @pytest.mark.asyncio
    async def test_resolve_from_first_provider(self) -> None:
        """Test resolving language from first provider."""
        provider1 = Mock()
        provider1.get_language = AsyncMock(return_value="en")

        provider2 = Mock()
        provider2.get_language = AsyncMock(return_value="fr")

        resolver = LanguageResolver([provider1, provider2])
        result = await resolver.resolve()

        assert result == "en"
        provider1.get_language.assert_called_once()
        provider2.get_language.assert_not_called()

    @pytest.mark.asyncio
    async def test_resolve_from_second_provider(self) -> None:
        """Test resolving language from second provider when first returns None."""
        provider1 = Mock()
        provider1.get_language = AsyncMock(return_value=None)

        provider2 = Mock()
        provider2.get_language = AsyncMock(return_value="fr")

        resolver = LanguageResolver([provider1, provider2])
        result = await resolver.resolve()

        assert result == "fr"
        provider1.get_language.assert_called_once()
        provider2.get_language.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_all_providers_return_none(self) -> None:
        """Test that exception is raised when all providers return None."""
        provider1 = Mock()
        provider1.get_language = AsyncMock(return_value=None)

        provider2 = Mock()
        provider2.get_language = AsyncMock(return_value=None)

        resolver = LanguageResolver([provider1, provider2])

        with pytest.raises(TranslaasLanguageResolutionException) as exc_info:
            await resolver.resolve()

        assert "Could not resolve language" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_resolve_or_none_returns_none(self) -> None:
        """Test that resolve_or_none returns None when no language found."""
        provider1 = Mock()
        provider1.get_language = AsyncMock(return_value=None)

        provider2 = Mock()
        provider2.get_language = AsyncMock(return_value=None)

        resolver = LanguageResolver([provider1, provider2])
        result = await resolver.resolve_or_none()

        assert result is None

    @pytest.mark.asyncio
    async def test_resolve_or_none_returns_language(self) -> None:
        """Test that resolve_or_none returns language when found."""
        provider1 = Mock()
        provider1.get_language = AsyncMock(return_value="en")

        resolver = LanguageResolver([provider1])
        result = await resolver.resolve_or_none()

        assert result == "en"

    @pytest.mark.asyncio
    async def test_provider_exception_continues_to_next(self) -> None:
        """Test that provider exceptions are handled and next provider is tried."""
        provider1 = Mock()
        provider1.get_language = AsyncMock(side_effect=Exception("Provider error"))

        provider2 = Mock()
        provider2.get_language = AsyncMock(return_value="fr")

        resolver = LanguageResolver([provider1, provider2])
        result = await resolver.resolve()

        assert result == "fr"

    def test_empty_providers_list_raises_exception(self) -> None:
        """Test that empty providers list raises exception."""
        with pytest.raises(TranslaasLanguageResolutionException) as exc_info:
            LanguageResolver([])

        assert "At least one language provider is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_real_providers_integration(self) -> None:
        """Test resolver with real provider implementations."""
        request = Mock()
        request.headers = {}
        request.cookies = {}
        request.args = {}

        provider1 = RequestLanguageProvider(request)
        provider2 = DefaultLanguageProvider("en")

        resolver = LanguageResolver([provider1, provider2])
        result = await resolver.resolve()

        assert result == "en"

    @pytest.mark.asyncio
    async def test_multiple_providers_order(self) -> None:
        """Test that providers are evaluated in order."""
        call_order = []

        async def make_provider(name: str, return_value: Optional[str]) -> Mock:
            async def get_language() -> Optional[str]:
                call_order.append(name)
                return return_value

            provider = Mock()
            provider.get_language = get_language
            return provider

        provider1 = await make_provider("provider1", None)
        provider2 = await make_provider("provider2", None)
        provider3 = await make_provider("provider3", "es")

        resolver = LanguageResolver([provider1, provider2, provider3])
        result = await resolver.resolve()

        assert result == "es"
        assert call_order == ["provider1", "provider2", "provider3"]

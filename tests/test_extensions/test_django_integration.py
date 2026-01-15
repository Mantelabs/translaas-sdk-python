"""Tests for Django integration."""

from unittest.mock import Mock, patch

import pytest
from django.test import override_settings

from translaas.extensions.django import DjangoRequestLanguageProvider, get_translaas_service, t


class TestDjangoRequestLanguageProvider:
    """Tests for DjangoRequestLanguageProvider."""

    @pytest.mark.asyncio
    async def test_get_language_from_language_code(self) -> None:
        """Test getting language from Django request LANGUAGE_CODE."""
        request = Mock()
        request.LANGUAGE_CODE = "en-us"
        request.headers = {}
        request.cookies = {}
        request.args = {}

        provider = DjangoRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "en"

    @pytest.mark.asyncio
    async def test_get_language_from_header(self) -> None:
        """Test getting language from Django request header."""
        request = Mock()
        request.LANGUAGE_CODE = None
        request.headers = {"Accept-Language": "fr-FR,fr;q=0.9"}
        request.cookies = {}
        request.args = {}

        provider = DjangoRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "fr"

    @pytest.mark.asyncio
    async def test_get_language_from_cookie(self) -> None:
        """Test getting language from Django request cookie."""
        request = Mock()
        request.LANGUAGE_CODE = None
        request.headers = {}
        request.cookies = {"language": "es"}
        request.args = {}

        provider = DjangoRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "es"

    @pytest.mark.asyncio
    async def test_get_language_from_query_param(self) -> None:
        """Test getting language from Django request query parameter."""
        request = Mock()
        request.LANGUAGE_CODE = None
        request.headers = {}
        request.cookies = {}
        request.args = {"lang": "de"}

        provider = DjangoRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "de"

    @pytest.mark.asyncio
    async def test_language_code_priority(self) -> None:
        """Test that LANGUAGE_CODE has priority over other sources."""
        request = Mock()
        request.LANGUAGE_CODE = "fr-fr"
        request.headers = {"Accept-Language": "en-US"}
        request.cookies = {"language": "es"}
        request.args = {"lang": "de"}

        provider = DjangoRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "fr"


class TestDjangoHelpers:
    """Tests for Django helper functions."""

    @patch("translaas.extensions.django.asyncio")
    @override_settings(
        TRANSLAAS_API_KEY="test-key",
        TRANSLAAS_BASE_URL="https://api.test.com",
        TRANSLAAS_CACHE_MODE=None,
        TRANSLAAS_TIMEOUT=None,
        TRANSLAAS_CACHE_ABSOLUTE_EXPIRATION=None,
        TRANSLAAS_CACHE_SLIDING_EXPIRATION=None,
        TRANSLAAS_DEFAULT_LANGUAGE=None,
    )
    def test_get_translaas_service(self, mock_asyncio: Mock) -> None:
        """Test get_translaas_service function."""
        request = Mock()
        request.LANGUAGE_CODE = "en"

        service = get_translaas_service(request)

        assert service is not None
        assert service.options.api_key == "test-key"
        assert service.options.base_url == "https://api.test.com"

    @patch("translaas.extensions.django.asyncio")
    @override_settings(
        TRANSLAAS_API_KEY="test-key",
        TRANSLAAS_BASE_URL="https://api.test.com",
        TRANSLAAS_CACHE_MODE=None,
        TRANSLAAS_TIMEOUT=None,
        TRANSLAAS_CACHE_ABSOLUTE_EXPIRATION=None,
        TRANSLAAS_CACHE_SLIDING_EXPIRATION=None,
        TRANSLAAS_DEFAULT_LANGUAGE=None,
    )
    def test_t_function(self, mock_asyncio: Mock) -> None:
        """Test t() helper function."""
        request = Mock()
        request.LANGUAGE_CODE = "en"

        # Mock async execution
        mock_loop = Mock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete.return_value = "translated"
        mock_asyncio.get_event_loop.return_value = mock_loop

        result = t("group", "entry", request=request)

        assert result == "translated"
        mock_loop.run_until_complete.assert_called_once()

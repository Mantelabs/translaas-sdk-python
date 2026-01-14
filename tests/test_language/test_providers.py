"""Tests for language providers."""

from unittest.mock import Mock, patch

import pytest

from translaas.exceptions import TranslaasLanguageResolutionException
from translaas.language.providers import (
    CultureLanguageProvider,
    DefaultLanguageProvider,
    RequestLanguageProvider,
)


class TestRequestLanguageProvider:
    """Tests for RequestLanguageProvider."""

    @pytest.mark.asyncio
    async def test_get_language_from_header(self) -> None:
        """Test getting language from Accept-Language header."""
        request = Mock()
        request.headers = {"Accept-Language": "en-US,en;q=0.9"}
        request.cookies = {}
        request.args = {}

        provider = RequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "en"

    @pytest.mark.asyncio
    async def test_get_language_from_header_multiple(self) -> None:
        """Test getting language from Accept-Language header with multiple languages."""
        request = Mock()
        request.headers = {"Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"}
        request.cookies = {}
        request.args = {}

        provider = RequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "fr"

    @pytest.mark.asyncio
    async def test_get_language_from_cookie(self) -> None:
        """Test getting language from cookie."""
        request = Mock()
        request.headers = {}
        request.cookies = {"language": "es"}
        request.args = {}

        provider = RequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "es"

    @pytest.mark.asyncio
    async def test_get_language_from_query_param(self) -> None:
        """Test getting language from query parameter."""
        request = Mock()
        request.headers = {}
        request.cookies = {}
        request.args = {"lang": "de"}

        provider = RequestLanguageProvider(request, param_name="lang")
        result = await provider.get_language()

        assert result == "de"

    @pytest.mark.asyncio
    async def test_priority_order(self) -> None:
        """Test that query param has priority over cookie and header."""
        request = Mock()
        request.headers = {"Accept-Language": "fr-FR"}
        request.cookies = {"language": "es"}
        request.args = {"lang": "de"}

        provider = RequestLanguageProvider(request, param_name="lang")
        result = await provider.get_language()

        assert result == "de"

    @pytest.mark.asyncio
    async def test_normalize_language_code(self) -> None:
        """Test that language codes are normalized correctly."""
        request = Mock()
        request.headers = {"Accept-Language": "en-US"}
        request.cookies = {}
        request.args = {}

        provider = RequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "en"

    @pytest.mark.asyncio
    async def test_no_language_found(self) -> None:
        """Test that None is returned when no language is found."""
        request = Mock()
        request.headers = {}
        request.cookies = {}
        request.args = {}

        provider = RequestLanguageProvider(request)
        result = await provider.get_language()

        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_language_code(self) -> None:
        """Test that invalid language codes return None."""
        request = Mock()
        request.headers = {"Accept-Language": "invalid"}
        request.cookies = {}
        request.args = {}

        provider = RequestLanguageProvider(request)
        result = await provider.get_language()

        assert result is None

    @pytest.mark.asyncio
    async def test_missing_request_attributes(self) -> None:
        """Test graceful handling of missing request attributes."""
        request = object()  # No attributes

        provider = RequestLanguageProvider(request)
        result = await provider.get_language()

        assert result is None

    @pytest.mark.asyncio
    async def test_custom_header_name(self) -> None:
        """Test using custom header name."""
        request = Mock()
        request.headers = {"X-Language": "pt"}
        request.cookies = {}
        request.args = {}

        provider = RequestLanguageProvider(request, header_name="X-Language")
        result = await provider.get_language()

        assert result == "pt"

    @pytest.mark.asyncio
    async def test_custom_cookie_name(self) -> None:
        """Test using custom cookie name."""
        request = Mock()
        request.headers = {}
        request.cookies = {"locale": "it"}
        request.args = {}

        provider = RequestLanguageProvider(request, cookie_name="locale")
        result = await provider.get_language()

        assert result == "it"


class TestCultureLanguageProvider:
    """Tests for CultureLanguageProvider."""

    @pytest.mark.asyncio
    async def test_get_language_from_locale(self) -> None:
        """Test getting language from system locale."""
        with patch("locale.getdefaultlocale", return_value=("en_US", "UTF-8")):
            provider = CultureLanguageProvider()
            result = await provider.get_language()

            assert result == "en"

    @pytest.mark.asyncio
    async def test_get_language_fallback_to_getlocale(self) -> None:
        """Test fallback to getlocale when getdefaultlocale fails."""
        with patch("locale.getdefaultlocale", return_value=(None, None)):
            with patch("locale.getlocale", return_value=("fr_FR", "UTF-8")):
                provider = CultureLanguageProvider()
                result = await provider.get_language()

                assert result == "fr"

    @pytest.mark.asyncio
    async def test_no_locale_available(self) -> None:
        """Test that None is returned when no locale is available."""
        with patch("locale.getdefaultlocale", return_value=(None, None)):
            with patch("locale.getlocale", return_value=(None, None)):
                provider = CultureLanguageProvider()
                result = await provider.get_language()

                assert result is None

    @pytest.mark.asyncio
    async def test_invalid_locale_format(self) -> None:
        """Test handling of invalid locale format."""
        with patch("locale.getdefaultlocale", return_value=("invalid", None)):
            with patch("locale.getlocale", return_value=(None, None)):
                provider = CultureLanguageProvider()
                result = await provider.get_language()

                # Should return None for invalid format
                assert result is None

    @pytest.mark.asyncio
    async def test_locale_exception_handling(self) -> None:
        """Test graceful handling of locale exceptions."""
        with patch("locale.getdefaultlocale", side_effect=ValueError("Invalid locale")):
            with patch("locale.getlocale", return_value=(None, None)):
                provider = CultureLanguageProvider()
                result = await provider.get_language()

                assert result is None


class TestDefaultLanguageProvider:
    """Tests for DefaultLanguageProvider."""

    @pytest.mark.asyncio
    async def test_get_default_language(self) -> None:
        """Test getting default language."""
        provider = DefaultLanguageProvider("en")
        result = await provider.get_language()

        assert result == "en"

    @pytest.mark.asyncio
    async def test_language_normalized_to_lowercase(self) -> None:
        """Test that language is normalized to lowercase."""
        provider = DefaultLanguageProvider("EN")
        result = await provider.get_language()

        assert result == "en"

    def test_invalid_language_code_raises_exception(self) -> None:
        """Test that invalid language code raises exception."""
        with pytest.raises(TranslaasLanguageResolutionException) as exc_info:
            DefaultLanguageProvider("invalid")

        assert "Invalid default language code" in str(exc_info.value)
        assert exc_info.value.language_code == "invalid"

    def test_empty_language_code_raises_exception(self) -> None:
        """Test that empty language code raises exception."""
        with pytest.raises(TranslaasLanguageResolutionException):
            DefaultLanguageProvider("")

    def test_too_long_language_code_raises_exception(self) -> None:
        """Test that too long language code raises exception."""
        with pytest.raises(TranslaasLanguageResolutionException):
            DefaultLanguageProvider("eng")

    @pytest.mark.asyncio
    async def test_different_languages(self) -> None:
        """Test different language codes."""
        languages = ["en", "fr", "es", "de", "it", "pt", "ru", "ja", "zh", "ko"]

        for lang in languages:
            provider = DefaultLanguageProvider(lang)
            result = await provider.get_language()
            assert result == lang.lower()

"""Tests for framework-specific language providers."""

from unittest.mock import Mock

import pytest

from translaas.extensions.django import DjangoRequestLanguageProvider
from translaas.extensions.fastapi import FastAPIRequestLanguageProvider
from translaas.extensions.flask import FlaskRequestLanguageProvider


class TestFlaskRequestLanguageProvider:
    """Tests for FlaskRequestLanguageProvider."""

    @pytest.mark.asyncio
    async def test_get_language_from_header(self) -> None:
        """Test getting language from Flask request header."""
        request = Mock()
        request.headers = {"Accept-Language": "en-US,en;q=0.9"}
        request.cookies = {}
        request.args = {}

        provider = FlaskRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "en"

    @pytest.mark.asyncio
    async def test_get_language_from_cookie(self) -> None:
        """Test getting language from Flask request cookie."""
        request = Mock()
        request.headers = {}
        request.cookies = {"language": "fr"}
        request.args = {}

        provider = FlaskRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "fr"

    @pytest.mark.asyncio
    async def test_get_language_from_query_param(self) -> None:
        """Test getting language from Flask request query parameter."""
        request = Mock()
        request.headers = {}
        request.cookies = {}
        request.args = {"lang": "es"}

        provider = FlaskRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "es"

    @pytest.mark.asyncio
    async def test_custom_names(self) -> None:
        """Test using custom header, cookie, and param names."""
        request = Mock()
        request.headers = {"X-Language": "de"}
        request.cookies = {"locale": "it"}
        request.args = {"l": "pt"}

        provider = FlaskRequestLanguageProvider(
            request, header_name="X-Language", cookie_name="locale", param_name="l"
        )
        result = await provider.get_language()

        # Query param should have priority
        assert result == "pt"


class TestFastAPIRequestLanguageProvider:
    """Tests for FastAPIRequestLanguageProvider."""

    @pytest.mark.asyncio
    async def test_get_language_from_header(self) -> None:
        """Test getting language from FastAPI request header."""
        request = Mock()
        request.headers = {"Accept-Language": "en-US,en;q=0.9"}
        request.cookies = {}
        request.args = {}

        provider = FastAPIRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "en"

    @pytest.mark.asyncio
    async def test_get_language_from_cookie(self) -> None:
        """Test getting language from FastAPI request cookie."""
        request = Mock()
        request.headers = {}
        request.cookies = {"language": "fr"}
        request.args = {}

        provider = FastAPIRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "fr"

    @pytest.mark.asyncio
    async def test_get_language_from_query_param(self) -> None:
        """Test getting language from FastAPI request query parameter."""
        request = Mock()
        request.headers = {}
        request.cookies = {}
        request.args = {"lang": "es"}

        provider = FastAPIRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "es"

    @pytest.mark.asyncio
    async def test_custom_names(self) -> None:
        """Test using custom header, cookie, and param names."""
        request = Mock()
        request.headers = {"X-Language": "de"}
        request.cookies = {"locale": "it"}
        request.args = {"l": "pt"}

        provider = FastAPIRequestLanguageProvider(
            request, header_name="X-Language", cookie_name="locale", param_name="l"
        )
        result = await provider.get_language()

        # Query param should have priority
        assert result == "pt"


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

    @pytest.mark.asyncio
    async def test_normalize_django_language_code(self) -> None:
        """Test normalization of Django language codes."""
        request = Mock()
        request.LANGUAGE_CODE = "zh-cn"
        request.headers = {}
        request.cookies = {}
        request.args = {}

        provider = DjangoRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "zh"

    @pytest.mark.asyncio
    async def test_missing_language_code_attribute(self) -> None:
        """Test graceful handling of missing LANGUAGE_CODE attribute."""
        request = Mock()
        del request.LANGUAGE_CODE
        request.headers = {"Accept-Language": "en-US"}
        request.cookies = {}
        request.args = {}

        provider = DjangoRequestLanguageProvider(request)
        result = await provider.get_language()

        assert result == "en"

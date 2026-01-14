"""Tests for language provider builder."""

from unittest.mock import Mock

import pytest

from translaas.exceptions import TranslaasLanguageResolutionException
from translaas.language.builder import LanguageProviderBuilder
from translaas.language.providers import (
    CultureLanguageProvider,
    DefaultLanguageProvider,
    RequestLanguageProvider,
)


class TestLanguageProviderBuilder:
    """Tests for LanguageProviderBuilder."""

    def test_add_request_provider(self) -> None:
        """Test adding request provider."""
        request = Mock()
        request.headers = {}
        request.cookies = {}
        request.args = {}

        builder = LanguageProviderBuilder()
        builder.add_request_provider(request)

        assert len(builder._providers) == 1
        assert isinstance(builder._providers[0], RequestLanguageProvider)

    def test_add_culture_provider(self) -> None:
        """Test adding culture provider."""
        builder = LanguageProviderBuilder()
        builder.add_culture_provider()

        assert len(builder._providers) == 1
        assert isinstance(builder._providers[0], CultureLanguageProvider)

    def test_add_default_provider(self) -> None:
        """Test adding default provider."""
        builder = LanguageProviderBuilder()
        builder.add_default_provider("en")

        assert len(builder._providers) == 1
        assert isinstance(builder._providers[0], DefaultLanguageProvider)

    def test_add_default_provider_invalid_language(self) -> None:
        """Test that invalid language code raises exception."""
        builder = LanguageProviderBuilder()

        with pytest.raises(TranslaasLanguageResolutionException):
            builder.add_default_provider("invalid")

    def test_add_custom_provider(self) -> None:
        """Test adding custom provider."""
        custom_provider = Mock()

        builder = LanguageProviderBuilder()
        builder.add_provider(custom_provider)

        assert len(builder._providers) == 1
        assert builder._providers[0] == custom_provider

    def test_fluent_interface(self) -> None:
        """Test fluent interface for chaining methods."""
        request = Mock()
        request.headers = {}
        request.cookies = {}
        request.args = {}

        builder = (
            LanguageProviderBuilder()
            .add_request_provider(request)
            .add_culture_provider()
            .add_default_provider("en")
        )

        assert len(builder._providers) == 3
        assert isinstance(builder._providers[0], RequestLanguageProvider)
        assert isinstance(builder._providers[1], CultureLanguageProvider)
        assert isinstance(builder._providers[2], DefaultLanguageProvider)

    def test_build_resolver(self) -> None:
        """Test building resolver from builder."""
        builder = LanguageProviderBuilder()
        builder.add_default_provider("en")

        resolver = builder.build()

        assert resolver is not None
        assert len(resolver.providers) == 1

    def test_build_empty_providers_raises_exception(self) -> None:
        """Test that building with no providers raises exception."""
        builder = LanguageProviderBuilder()

        with pytest.raises(TranslaasLanguageResolutionException) as exc_info:
            builder.build()

        assert "At least one language provider must be added" in str(exc_info.value)

    def test_custom_header_name(self) -> None:
        """Test using custom header name in request provider."""
        request = Mock()
        request.headers = {"X-Language": "fr"}
        request.cookies = {}
        request.args = {}

        builder = LanguageProviderBuilder()
        builder.add_request_provider(request, header_name="X-Language")

        resolver = builder.build()
        assert len(resolver.providers) == 1

    def test_custom_cookie_name(self) -> None:
        """Test using custom cookie name in request provider."""
        request = Mock()
        request.headers = {}
        request.cookies = {"locale": "es"}
        request.args = {}

        builder = LanguageProviderBuilder()
        builder.add_request_provider(request, cookie_name="locale")

        resolver = builder.build()
        assert len(resolver.providers) == 1

    def test_custom_param_name(self) -> None:
        """Test using custom param name in request provider."""
        request = Mock()
        request.headers = {}
        request.cookies = {}
        request.args = {"lang": "de"}

        builder = LanguageProviderBuilder()
        builder.add_request_provider(request, param_name="lang")

        resolver = builder.build()
        assert len(resolver.providers) == 1

    @pytest.mark.asyncio
    async def test_built_resolver_works(self) -> None:
        """Test that built resolver actually works."""
        request = Mock()
        request.headers = {}
        request.cookies = {}
        request.args = {}

        builder = LanguageProviderBuilder().add_request_provider(request).add_default_provider("en")

        resolver = builder.build()
        result = await resolver.resolve()

        assert result == "en"

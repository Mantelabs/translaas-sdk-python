"""Tests for FastAPI integration."""

from unittest.mock import Mock

import pytest

from translaas import TranslaasOptions
from translaas.extensions.fastapi import (
    FastAPIRequestLanguageProvider,
    FastAPITranslaas,
    get_translaas_service,
)


class TestFastAPITranslaas:
    """Tests for FastAPITranslaas extension."""

    def test_init_with_app(self) -> None:
        """Test initializing Translaas with FastAPI app."""
        from fastapi import FastAPI

        app = FastAPI()
        options = TranslaasOptions(
            api_key="test-key",
            base_url="https://api.test.com",
        )

        translaas = FastAPITranslaas(app)
        translaas.init_app(app, options)

        assert translaas.app == app
        assert translaas._options == options
        assert hasattr(app.state, "get_translaas_service")

    def test_init_without_app(self) -> None:
        """Test initializing Translaas without FastAPI app."""
        translaas = FastAPITranslaas()
        assert translaas.app is None

    def test_init_app_stores_options_in_state(self) -> None:
        """Test that init_app stores options in app state."""
        from fastapi import FastAPI

        app = FastAPI()
        options = TranslaasOptions(
            api_key="test-key",
            base_url="https://api.test.com",
        )

        translaas = FastAPITranslaas()
        translaas.init_app(app, options)

        assert app.state.translaas_options == options

    def test_get_translaas_service_dependency(self) -> None:
        """Test get_translaas_service dependency function."""
        from fastapi import FastAPI, Request

        app = FastAPI()
        options = TranslaasOptions(
            api_key="test-key",
            base_url="https://api.test.com",
        )

        translaas = FastAPITranslaas()
        translaas.init_app(app, options)

        # Create a mock request
        request = Mock(spec=Request)
        request.app = app

        # Get service
        service = get_translaas_service(request)

        assert service is not None
        assert service.options == options

    def test_get_translaas_service_raises_if_not_initialized(self) -> None:
        """Test that get_translaas_service raises if extension not initialized."""
        from fastapi import Request

        request = Mock(spec=Request)
        request.app = Mock()
        request.app.state = Mock()
        delattr(request.app.state, "get_translaas_service")

        with pytest.raises(RuntimeError, match="not initialized"):
            get_translaas_service(request)


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

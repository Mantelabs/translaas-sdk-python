"""Tests for FastAPI integration."""

import os
from unittest.mock import Mock, patch

import pytest

from translaas import TranslaasOptions
from translaas.extensions.config import fastapi_config
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

    def test_init_app_reads_translaas_config_dict(self) -> None:
        """Test init_app builds options from app.state.translaas_config."""
        from fastapi import FastAPI

        app = FastAPI()
        app.state.translaas_config = {
            "api_key": "cfg-key",
            "base_url": "https://cfg.test.com",
            "default_project": "proj",
        }

        translaas = FastAPITranslaas()
        translaas.init_app(app)

        assert translaas._options is not None
        assert translaas._options.api_key == "cfg-key"
        assert translaas._options.default_project == "proj"

    def test_init_app_reads_state_mapped_keys(self) -> None:
        """Test init_app builds options from TRANSLAAS_* attributes on app.state."""
        from fastapi import FastAPI

        app = FastAPI()
        app.state.TRANSLAAS_API_KEY = "state-key"
        app.state.TRANSLAAS_BASE_URL = "https://state.test.com"

        translaas = FastAPITranslaas()
        translaas.init_app(app)

        assert translaas._options.api_key == "state-key"

    def test_init_app_reads_from_env_when_no_state_config(self) -> None:
        """Test init_app falls back to from_env when state has no config."""
        from fastapi import FastAPI

        app = FastAPI()
        env = {
            "TRANSLAAS_API_KEY": "env-key",
            "TRANSLAAS_BASE_URL": "https://env.test.com",
        }
        with patch.dict(os.environ, env, clear=False):
            translaas = FastAPITranslaas()
            translaas.init_app(app)
        assert translaas._options.api_key == "env-key"


class TestFastAPIConfig:
    """Tests for fastapi_config helper."""

    def test_fastapi_config_from_dict_on_state(self) -> None:
        from fastapi import FastAPI

        app = FastAPI()
        app.state.translaas_config = {
            "api_key": "k",
            "base_url": "https://api.test.com",
            "channel": "beta",
        }
        options = fastapi_config(app)
        assert options.api_key == "k"
        assert options.channel == "beta"

    async def test_get_translaas_service_dependency(self) -> None:
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

        # Get service (async generator, need to iterate)
        async_gen = get_translaas_service(request)
        service = await async_gen.__anext__()

        assert service is not None
        assert service.options == options

        # Clean up
        await async_gen.aclose()

    async def test_get_translaas_service_raises_if_not_initialized(self) -> None:
        """Test that get_translaas_service raises if extension not initialized."""
        from fastapi import Request

        request = Mock(spec=Request)
        request.app = Mock()
        request.app.state = Mock()
        delattr(request.app.state, "get_translaas_service")

        async_gen = get_translaas_service(request)
        with pytest.raises(RuntimeError, match="not initialized"):
            await async_gen.__anext__()


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

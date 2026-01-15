"""Tests for Flask integration."""

from unittest.mock import Mock, patch

import pytest

from translaas import TranslaasOptions
from translaas.extensions.flask import FlaskRequestLanguageProvider, FlaskTranslaas


class TestFlaskTranslaas:
    """Tests for FlaskTranslaas extension."""

    def test_init_with_app(self) -> None:
        """Test initializing Translaas with Flask app."""
        from flask import Flask

        app = Flask(__name__)
        app.config["TRANSLAAS_API_KEY"] = "test-key"
        app.config["TRANSLAAS_BASE_URL"] = "https://api.test.com"

        options = TranslaasOptions(
            api_key=app.config["TRANSLAAS_API_KEY"],
            base_url=app.config["TRANSLAAS_BASE_URL"],
        )

        translaas = FlaskTranslaas(app)
        translaas.init_app(app, options)

        assert translaas.app == app
        assert translaas._options == options

    def test_init_without_app(self) -> None:
        """Test initializing Translaas without Flask app."""
        translaas = FlaskTranslaas()
        assert translaas.app is None

    def test_init_app_registers_template_filter(self) -> None:
        """Test that init_app registers template filter."""
        from flask import Flask

        app = Flask(__name__)
        app.config["TRANSLAAS_API_KEY"] = "test-key"
        app.config["TRANSLAAS_BASE_URL"] = "https://api.test.com"

        options = TranslaasOptions(
            api_key=app.config["TRANSLAAS_API_KEY"],
            base_url=app.config["TRANSLAAS_BASE_URL"],
        )

        translaas = FlaskTranslaas()
        translaas.init_app(app, options)

        # Check that filter is registered
        assert "translaas" in app.jinja_env.filters
        assert "translaas" in app.jinja_env.globals

    def test_t_method_raises_if_not_initialized(self) -> None:
        """Test that t() raises error if extension not initialized."""
        translaas = FlaskTranslaas()

        with pytest.raises(RuntimeError, match="not initialized"):
            translaas.t("group", "entry")

    @patch("translaas.extensions.flask.asyncio")
    def test_t_method_calls_service(self, mock_asyncio: Mock) -> None:
        """Test that t() method calls service correctly."""
        from flask import Flask

        app = Flask(__name__)
        options = TranslaasOptions(
            api_key="test-key",
            base_url="https://api.test.com",
        )

        translaas = FlaskTranslaas()
        translaas.init_app(app, options)

        # Mock the async execution
        mock_loop = Mock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete.return_value = "translated"
        mock_asyncio.get_event_loop.return_value = mock_loop

        # Mock request context
        with app.test_request_context():
            result = translaas.t("group", "entry")

        assert result == "translated"
        mock_loop.run_until_complete.assert_called_once()


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

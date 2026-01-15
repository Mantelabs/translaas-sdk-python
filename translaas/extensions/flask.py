"""Flask framework integration for the Translaas SDK.

This module provides Flask-specific integrations including initialization,
template filters, and helper methods for using Translaas in Flask applications.
"""

import asyncio
from typing import TYPE_CHECKING, Dict, Optional

from translaas.language.providers import RequestLanguageProvider
from translaas.language.resolver import LanguageResolver
from translaas.models.options import TranslaasOptions
from translaas.models.protocols import ILanguageProvider
from translaas.service import TranslaasService

if TYPE_CHECKING:
    from flask import Flask


class FlaskRequestLanguageProvider(ILanguageProvider):
    """Flask-specific request language provider.

    Extracts language from Flask request objects, checking headers,
    cookies, and query parameters.

    Attributes:
        request: The Flask request object.

    Example:
        ```python
        from flask import Flask, request

        app = Flask(__name__)

        @app.route('/')
        def index():
            provider = FlaskRequestLanguageProvider(request)
            language = await provider.get_language()
            return f"Language: {language}"
        ```
    """

    def __init__(
        self,
        request: object,
        *,
        header_name: str = "Accept-Language",
        cookie_name: str = "language",
        param_name: Optional[str] = "lang",
    ) -> None:
        """Initialize a FlaskRequestLanguageProvider.

        Args:
            request: The Flask request object.
            header_name: The header name to check (default: 'Accept-Language').
            cookie_name: The cookie name to check (default: 'language').
            param_name: The query parameter name to check (default: 'lang').
        """
        self._provider = RequestLanguageProvider(
            request,
            header_name=header_name,
            cookie_name=cookie_name,
            param_name=param_name,
        )

    async def get_language(self) -> Optional[str]:
        """Get the language from Flask request.

        Returns:
            The language code (ISO 639-1) if found, or None if not available.
        """
        return await self._provider.get_language()


class Translaas:
    """Flask extension for Translaas SDK.

    This extension provides Flask integration for the Translaas SDK,
    including template filters and helper methods.

    Attributes:
        app: The Flask application instance.
        service: The TranslaasService instance.

    Example:
        ```python
        from flask import Flask
        from translaas.extensions.flask import Translaas
        from translaas import TranslaasOptions

        app = Flask(__name__)
        translaas = Translaas()

        options = TranslaasOptions(
            api_key="your-api-key",
            base_url="https://api.translaas.com",
        )
        translaas.init_app(app, options)

        @app.route('/')
        def index():
            return render_template('index.html')
        ```
    """

    def __init__(self, app: Optional["Flask"] = None) -> None:
        """Initialize the Translaas Flask extension.

        Args:
            app: Optional Flask application instance. If provided, init_app is called automatically.
        """
        self.app: Optional["Flask"] = None
        self._options: Optional[TranslaasOptions] = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app: "Flask", options: Optional[TranslaasOptions] = None) -> None:
        """Initialize the extension with a Flask application.

        Args:
            app: The Flask application instance.
            options: Optional TranslaasOptions instance. If not provided, will be read from app.config.
        """
        self.app = app

        # Get options from parameter or app config
        if options is None:
            from translaas.models.options import TranslaasOptions

            options = TranslaasOptions(
                api_key=app.config.get("TRANSLAAS_API_KEY", ""),
                base_url=app.config.get("TRANSLAAS_BASE_URL", ""),
                cache_mode=app.config.get("TRANSLAAS_CACHE_MODE"),
                timeout=app.config.get("TRANSLAAS_TIMEOUT"),
                cache_absolute_expiration=app.config.get("TRANSLAAS_CACHE_ABSOLUTE_EXPIRATION"),
                cache_sliding_expiration=app.config.get("TRANSLAAS_CACHE_SLIDING_EXPIRATION"),
                default_language=app.config.get("TRANSLAAS_DEFAULT_LANGUAGE"),
            )

        self._options = options

        # Service will be created per-request to access current request context
        self.service: Optional[TranslaasService] = None

        # Register template filter
        @app.template_filter("translaas")  # type: ignore[misc]
        def translaas_filter(group: str, entry: str, **kwargs: str) -> str:
            """Template filter for translations.

            Args:
                group: The translation group name.
                entry: The translation entry key.
                **kwargs: Optional parameters for translation (lang, number, parameters).

            Returns:
                The translated string.
            """
            lang = kwargs.pop("lang", None)
            number_str = kwargs.pop("number", None)
            number: Optional[float] = None
            if number_str is not None:
                try:
                    number = float(number_str)
                except (ValueError, TypeError):
                    number = None
            parameters = kwargs if kwargs else None
            return self.t(group, entry, lang=lang, number=number, parameters=parameters)

        # Make translaas available in templates
        app.jinja_env.globals["translaas"] = self

    def _get_service(self) -> TranslaasService:
        """Get or create a TranslaasService instance for the current request.

        Returns:
            A TranslaasService instance configured for the current request.
        """
        from flask import has_request_context, request

        if self._options is None:
            raise RuntimeError("Translaas extension not initialized. Call init_app() first.")

        # Create service with language resolver for current request
        language_resolver = None
        if has_request_context():
            language_resolver = LanguageResolver([FlaskRequestLanguageProvider(request)])

        return TranslaasService(self._options, language_resolver=language_resolver)

    def t(
        self,
        group: str,
        entry: str,
        lang: Optional[str] = None,
        number: Optional[float] = None,
        parameters: Optional[Dict[str, str]] = None,
    ) -> str:
        """Get a translation synchronously.

        This is a synchronous wrapper around the async TranslaasService.t() method.
        It should be used in Flask views and templates.

        Args:
            group: The translation group name.
            entry: The translation entry key.
            lang: Optional explicit language code.
            number: Optional number for plural form selection.
            parameters: Optional dictionary of parameters for string interpolation.

        Returns:
            The translated string.

        Raises:
            RuntimeError: If the extension is not initialized.
        """
        if self._options is None:
            raise RuntimeError("Translaas extension not initialized. Call init_app() first.")

        # Run async operation in sync context
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Flask runs in a sync context, so we can safely use run_until_complete
        # If there's already a running loop, create a new one
        if loop.is_running():
            # Create a new event loop for this operation
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(
                    self._get_translation(group, entry, lang, number, parameters)
                )
            finally:
                new_loop.close()
        else:
            return loop.run_until_complete(
                self._get_translation(group, entry, lang, number, parameters)
            )

    async def _get_translation(
        self,
        group: str,
        entry: str,
        lang: Optional[str],
        number: Optional[float],
        parameters: Optional[Dict[str, str]],
    ) -> str:
        """Internal async method to get translation.

        Args:
            group: The translation group name.
            entry: The translation entry key.
            lang: Optional explicit language code.
            number: Optional number for plural form selection.
            parameters: Optional dictionary of parameters.

        Returns:
            The translated string.
        """
        service = self._get_service()

        async with service:
            if number is not None:
                if lang:
                    return await service.t(group, entry, lang, number)
                else:
                    return await service.t(group, entry, number)
            elif parameters:
                if lang:
                    return await service.t(group, entry, lang, parameters)
                else:
                    return await service.t(group, entry, parameters)
            elif lang:
                return await service.t(group, entry, lang)
            else:
                return await service.t(group, entry)


# Alias for backward compatibility and easier imports
FlaskTranslaas = Translaas

__all__ = [
    "FlaskRequestLanguageProvider",
    "Translaas",
    "FlaskTranslaas",
]

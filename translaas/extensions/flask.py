"""Flask framework integration for language resolution.

This module provides Flask-specific language providers that integrate
with Flask request objects.
"""

from typing import Optional

from translaas.language.providers import RequestLanguageProvider
from translaas.models.protocols import ILanguageProvider


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

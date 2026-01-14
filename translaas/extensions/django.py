"""Django framework integration for language resolution.

This module provides Django-specific language providers that integrate
with Django request objects.
"""

import re
from typing import Optional

from translaas.language.providers import RequestLanguageProvider
from translaas.models.protocols import ILanguageProvider


class DjangoRequestLanguageProvider(ILanguageProvider):
    """Django-specific request language provider.

    Extracts language from Django request objects, checking headers,
    cookies, and query parameters. Also checks Django's LANGUAGE_CODE setting
    and request.LANGUAGE_CODE if available.

    Attributes:
        request: The Django request object.

    Example:
        ```python
        from django.http import HttpRequest
        from translaas.extensions.django import DjangoRequestLanguageProvider

        def my_view(request: HttpRequest):
            provider = DjangoRequestLanguageProvider(request)
            language = await provider.get_language()
            return HttpResponse(f"Language: {language}")
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
        """Initialize a DjangoRequestLanguageProvider.

        Args:
            request: The Django request object.
            header_name: The header name to check (default: 'Accept-Language').
            cookie_name: The cookie name to check (default: 'language').
            param_name: The query parameter name to check (default: 'lang').
        """
        self.request = request
        self._provider = RequestLanguageProvider(
            request,
            header_name=header_name,
            cookie_name=cookie_name,
            param_name=param_name,
        )

    async def get_language(self) -> Optional[str]:
        """Get the language from Django request.

        Checks Django-specific attributes first (LANGUAGE_CODE), then falls
        back to standard request-based detection.

        Returns:
            The language code (ISO 639-1) if found, or None if not available.
        """
        # Check Django's LANGUAGE_CODE attribute first
        try:
            if hasattr(self.request, "LANGUAGE_CODE") and self.request.LANGUAGE_CODE:
                lang = self.request.LANGUAGE_CODE
                # Normalize Django language code (e.g., 'en-us' -> 'en')
                normalized = self._normalize_language(lang)
                if normalized:
                    return normalized
        except (AttributeError, TypeError):
            pass

        # Fall back to standard request-based detection
        return await self._provider.get_language()

    def _normalize_language(self, lang: str) -> Optional[str]:
        """Normalize a language code to ISO 639-1 format.

        Converts language codes like 'en-us' to 'en', 'fr-fr' to 'fr', etc.

        Args:
            lang: The language code to normalize.

        Returns:
            The normalized language code (ISO 639-1), or None if invalid.
        """
        if not lang:
            return None

        lang = lang.strip().lower()

        # Extract ISO 639-1 code (first two characters before hyphen)
        # Examples: 'en-us' -> 'en', 'fr-fr' -> 'fr', 'zh-cn' -> 'zh'
        match = re.match(r"^([a-z]{2})(?:[-_][a-z]{2,})?", lang)
        if match:
            return match.group(1)

        # If already a 2-character code, return as-is
        if re.match(r"^[a-z]{2}$", lang):
            return lang

        return None

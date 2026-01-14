"""Language providers for automatic language detection.

This module provides various language providers that can detect the current
language from different sources (request headers, cookies, system locale, etc.).
"""

import locale
import re
from typing import Optional

from translaas.exceptions import TranslaasLanguageResolutionException
from translaas.models.protocols import ILanguageProvider


class RequestLanguageProvider(ILanguageProvider):
    """Generic request-based language provider.

    Extracts language from request headers (Accept-Language) or cookies.
    This is a generic implementation that works with any request-like object
    that has headers and cookies attributes.

    Attributes:
        request: The request object (must have headers and cookies attributes).
        header_name: The header name to check (default: 'Accept-Language').
        cookie_name: The cookie name to check (default: 'language').
        param_name: Optional query parameter name to check.

    Example:
        ```python
        # Mock request object
        class MockRequest:
            headers = {'Accept-Language': 'en-US,en;q=0.9'}
            cookies = {}
            args = {}

        provider = RequestLanguageProvider(MockRequest())
        language = await provider.get_language()  # Returns 'en'
        ```
    """

    def __init__(
        self,
        request: object,
        *,
        header_name: str = "Accept-Language",
        cookie_name: str = "language",
        param_name: Optional[str] = None,
    ) -> None:
        """Initialize a RequestLanguageProvider.

        Args:
            request: The request object with headers and cookies attributes.
            header_name: The header name to check for language (default: 'Accept-Language').
            cookie_name: The cookie name to check for language (default: 'language').
            param_name: Optional query parameter name to check for language.
        """
        self.request = request
        self.header_name = header_name
        self.cookie_name = cookie_name
        self.param_name = param_name

    async def get_language(self) -> Optional[str]:
        """Get the language from the request.

        Checks in order: query parameter, cookie, header.

        Returns:
            The language code (ISO 639-1) if found, or None if not available.
        """
        # Check query parameter first (highest priority)
        if self.param_name:
            try:
                if hasattr(self.request, "args") and self.param_name in self.request.args:
                    lang = self.request.args[self.param_name]
                    return self._normalize_language(lang)
            except (AttributeError, KeyError, TypeError):
                pass

        # Check cookie
        try:
            if hasattr(self.request, "cookies") and self.cookie_name in self.request.cookies:
                lang = self.request.cookies[self.cookie_name]
                return self._normalize_language(lang)
        except (AttributeError, KeyError, TypeError):
            pass

        # Check header (Accept-Language)
        try:
            if hasattr(self.request, "headers"):
                headers = self.request.headers
                # Handle both dict-like and case-insensitive headers
                if isinstance(headers, dict):
                    header_value = headers.get(self.header_name) or headers.get(
                        self.header_name.lower()
                    )
                elif hasattr(headers, "get"):
                    header_value = headers.get(self.header_name)
                else:
                    header_value = None

                if header_value:
                    return self._parse_accept_language(header_value)
        except (AttributeError, KeyError, TypeError):
            pass

        return None

    def _parse_accept_language(self, accept_language: str) -> Optional[str]:
        """Parse Accept-Language header value.

        Extracts the primary language from an Accept-Language header string.
        Handles formats like 'en-US,en;q=0.9,fr;q=0.8'.

        Args:
            accept_language: The Accept-Language header value.

        Returns:
            The primary language code (ISO 639-1) if found, or None.
        """
        if not accept_language:
            return None

        # Split by comma and get the first language
        languages = accept_language.split(",")
        if not languages:
            return None

        # Get the first language (highest priority)
        first_lang = languages[0].strip()
        # Remove quality value if present (e.g., 'en;q=0.9' -> 'en')
        first_lang = first_lang.split(";")[0].strip()

        return self._normalize_language(first_lang)

    def _normalize_language(self, lang: str) -> Optional[str]:
        """Normalize a language code to ISO 639-1 format.

        Converts language codes like 'en-US' to 'en', 'fr-FR' to 'fr', etc.

        Args:
            lang: The language code to normalize.

        Returns:
            The normalized language code (ISO 639-1), or None if invalid.
        """
        if not lang:
            return None

        lang = lang.strip().lower()

        # If exactly 2 lowercase letters, return as-is
        if re.match(r"^[a-z]{2}$", lang):
            return lang

        # Extract ISO 639-1 code (first two characters before hyphen/underscore)
        # Examples: 'en-US' -> 'en', 'fr-FR' -> 'fr', 'zh-CN' -> 'zh'
        # Must match: 2 letters, optionally followed by separator and more characters
        # This ensures we don't match "in" from "invalid"
        match = re.match(r"^([a-z]{2})(?:[-_][a-z]{2,})?$", lang)
        if match:
            code = match.group(1)
            # Validate that it's a valid 2-letter code
            if re.match(r"^[a-z]{2}$", code):
                return code

        return None


class CultureLanguageProvider(ILanguageProvider):
    """System locale-based language provider.

    Detects the language from the system's locale settings.
    Uses Python's locale module to get the default locale.

    Example:
        ```python
        provider = CultureLanguageProvider()
        language = await provider.get_language()  # Returns system locale language
        ```
    """

    async def get_language(self) -> Optional[str]:
        """Get the language from system locale.

        Returns:
            The language code (ISO 639-1) from system locale, or None if unavailable.
        """
        try:
            # Get the default locale
            system_locale, _ = locale.getdefaultlocale()
            if system_locale:
                # Extract language code (e.g., 'en_US' -> 'en')
                lang = system_locale.split("_")[0].lower()
                if self._is_valid_language_code(lang):
                    return lang
        except (ValueError, AttributeError, TypeError):
            pass

        try:
            # Fallback to locale.getlocale()
            lang_code, _ = locale.getlocale()
            if lang_code:
                lang = lang_code.split("_")[0].lower()
                if self._is_valid_language_code(lang):
                    return lang
        except (ValueError, AttributeError, TypeError):
            pass

        return None

    def _is_valid_language_code(self, lang: str) -> bool:
        """Check if a language code is valid (ISO 639-1 format).

        Args:
            lang: The language code to validate.

        Returns:
            True if the language code is valid, False otherwise.
        """
        if not lang:
            return False
        # ISO 639-1 codes are 2 lowercase letters
        return bool(re.match(r"^[a-z]{2}$", lang))


class DefaultLanguageProvider(ILanguageProvider):
    """Default/fallback language provider.

    Always returns a specified default language code.
    This should typically be the last provider in the chain.

    Attributes:
        default_language: The default language code to return.

    Example:
        ```python
        provider = DefaultLanguageProvider('en')
        language = await provider.get_language()  # Always returns 'en'
        ```
    """

    def __init__(self, default_language: str) -> None:
        """Initialize a DefaultLanguageProvider.

        Args:
            default_language: The default language code (ISO 639-1).

        Raises:
            TranslaasLanguageResolutionException: If the language code is invalid.
        """
        # Normalize to lowercase first
        normalized = default_language.lower().strip()
        if not self._is_valid_language_code(normalized):
            raise TranslaasLanguageResolutionException(
                f"Invalid default language code: {default_language}",
                language_code=default_language,
            )
        self.default_language = normalized

    async def get_language(self) -> Optional[str]:
        """Get the default language.

        Returns:
            The default language code.
        """
        return self.default_language

    def _is_valid_language_code(self, lang: str) -> bool:
        """Check if a language code is valid (ISO 639-1 format).

        Args:
            lang: The language code to validate.

        Returns:
            True if the language code is valid, False otherwise.
        """
        if not lang:
            return False
        # ISO 639-1 codes are 2 lowercase letters
        return bool(re.match(r"^[a-z]{2}$", lang))

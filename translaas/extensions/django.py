"""Django framework integration for the Translaas SDK.

This module provides Django-specific integrations including template tags,
helper methods, and request language providers for using Translaas in Django applications.
"""

import asyncio
import re
from typing import TYPE_CHECKING, Dict, Optional

from translaas.language.providers import RequestLanguageProvider
from translaas.language.resolver import LanguageResolver
from translaas.models.protocols import ILanguageProvider
from translaas.service import TranslaasService

if TYPE_CHECKING:
    from django.http import HttpRequest


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


def get_translaas_service(request: Optional["HttpRequest"] = None) -> TranslaasService:
    """Get a TranslaasService instance for the current request.

    This function creates a TranslaasService instance configured with
    language resolution from the Django request.

    Args:
        request: Optional Django HttpRequest object. If not provided, attempts to get from context.

    Returns:
        A TranslaasService instance configured for the current request.

    Raises:
        RuntimeError: If request is not available and cannot be obtained from context.
    """
    from django.conf import settings

    from translaas.models.options import TranslaasOptions

    # Get options from Django settings
    options = TranslaasOptions(
        api_key=getattr(settings, "TRANSLAAS_API_KEY", ""),
        base_url=getattr(settings, "TRANSLAAS_BASE_URL", ""),
        cache_mode=getattr(settings, "TRANSLAAS_CACHE_MODE", None),
        timeout=getattr(settings, "TRANSLAAS_TIMEOUT", None),
        cache_absolute_expiration=getattr(settings, "TRANSLAAS_CACHE_ABSOLUTE_EXPIRATION", None),
        cache_sliding_expiration=getattr(settings, "TRANSLAAS_CACHE_SLIDING_EXPIRATION", None),
        default_language=getattr(settings, "TRANSLAAS_DEFAULT_LANGUAGE", None),
    )

    # Create language resolver if request is available
    language_resolver = None
    if request is not None:
        language_resolver = LanguageResolver([DjangoRequestLanguageProvider(request)])

    return TranslaasService(options, language_resolver=language_resolver)


def t(
    group: str,
    entry: str,
    request: Optional["HttpRequest"] = None,
    lang: Optional[str] = None,
    number: Optional[float] = None,
    parameters: Optional[Dict[str, str]] = None,
) -> str:
    """Get a translation synchronously.

    This is a synchronous wrapper around the async TranslaasService.t() method.
    It should be used in Django views and templates.

    Args:
        group: The translation group name.
        entry: The translation entry key.
        request: Optional Django HttpRequest object. Used for language resolution.
        lang: Optional explicit language code.
        number: Optional number for plural form selection.
        parameters: Optional dictionary of parameters for string interpolation.

    Returns:
        The translated string.

    Raises:
        RuntimeError: If the service cannot be initialized.
    """
    service = get_translaas_service(request)

    # Run async operation in sync context
    loop = None
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Django runs in a sync context, so we can safely use run_until_complete
    # If there's already a running loop, create a new one
    if loop.is_running():
        # Create a new event loop for this operation
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(
                _get_translation(service, group, entry, lang, number, parameters)
            )
        finally:
            new_loop.close()
    else:
        return loop.run_until_complete(
            _get_translation(service, group, entry, lang, number, parameters)
        )


async def _get_translation(
    service: TranslaasService,
    group: str,
    entry: str,
    lang: Optional[str],
    number: Optional[float],
    parameters: Optional[Dict[str, str]],
) -> str:
    """Internal async method to get translation.

    Args:
        service: The TranslaasService instance.
        group: The translation group name.
        entry: The translation entry key.
        lang: Optional explicit language code.
        number: Optional number for plural form selection.
        parameters: Optional dictionary of parameters.

    Returns:
        The translated string.
    """
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

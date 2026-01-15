"""FastAPI framework integration for the Translaas SDK.

This module provides FastAPI-specific integrations including dependency injection,
helper methods, and request language providers for using Translaas in FastAPI applications.
"""

from typing import TYPE_CHECKING, Optional

from fastapi import Request

from translaas.language.providers import RequestLanguageProvider
from translaas.language.resolver import LanguageResolver
from translaas.models.protocols import ILanguageProvider
from translaas.service import TranslaasService

if TYPE_CHECKING:
    from fastapi import FastAPI


class FastAPIRequestLanguageProvider(ILanguageProvider):
    """FastAPI-specific request language provider.

    Extracts language from FastAPI request objects, checking headers,
    cookies, and query parameters.

    Attributes:
        request: The FastAPI request object.

    Example:
        ```python
        from fastapi import FastAPI, Request

        app = FastAPI()

        @app.get('/')
        async def index(request: Request):
            provider = FastAPIRequestLanguageProvider(request)
            language = await provider.get_language()
            return {"language": language}
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
        """Initialize a FastAPIRequestLanguageProvider.

        Args:
            request: The FastAPI request object.
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
        """Get the language from FastAPI request.

        Returns:
            The language code (ISO 639-1) if found, or None if not available.
        """
        return await self._provider.get_language()


class Translaas:
    """FastAPI extension for Translaas SDK.

    This extension provides FastAPI integration for the Translaas SDK,
    including dependency injection and helper methods.

    Attributes:
        app: The FastAPI application instance.
        options: The TranslaasOptions instance.

    Example:
        ```python
        from fastapi import FastAPI
        from translaas.extensions.fastapi import Translaas, get_translaas_service
        from translaas import TranslaasOptions

        app = FastAPI()
        translaas = Translaas()

        options = TranslaasOptions(
            api_key="your-api-key",
            base_url="https://api.translaas.com",
        )
        translaas.init_app(app, options)

        @app.get('/')
        async def index(service: TranslaasService = Depends(get_translaas_service)):
            translation = await service.t('common', 'welcome')
            return {"message": translation}
        ```
    """

    def __init__(self, app: Optional["FastAPI"] = None) -> None:
        """Initialize the Translaas FastAPI extension.

        Args:
            app: Optional FastAPI application instance. If provided, init_app is called automatically.
        """
        self.app: Optional["FastAPI"] = None
        self._options = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app: "FastAPI", options: Optional[object] = None) -> None:
        """Initialize the extension with a FastAPI application.

        Args:
            app: The FastAPI application instance.
            options: Optional TranslaasOptions instance. If not provided, will be read from app.state.
        """
        self.app = app

        # Get options from parameter or app state
        if options is None:
            if not hasattr(app.state, "translaas_options"):
                raise ValueError(
                    "TranslaasOptions must be provided either as parameter or set in app.state.translaas_options"
                )
            options = app.state.translaas_options

        self._options = options
        app.state.translaas_options = options

        # Create dependency function
        def _get_translaas_service(request: Request) -> TranslaasService:
            """Create a TranslaasService instance for the current request.

            Args:
                request: The FastAPI request object.

            Returns:
                A TranslaasService instance configured for the current request.
            """
            language_resolver = LanguageResolver([FastAPIRequestLanguageProvider(request)])
            return TranslaasService(self._options, language_resolver=language_resolver)

        # Store dependency function in app state for access
        app.state.get_translaas_service = _get_translaas_service


def get_translaas_service(request: Request) -> TranslaasService:
    """Dependency function to get TranslaasService instance.

    This function should be used as a FastAPI dependency to inject
    TranslaasService into route handlers.

    Args:
        request: The FastAPI request object (injected by FastAPI).

    Returns:
        A TranslaasService instance configured for the current request.

    Raises:
        RuntimeError: If the extension is not initialized.

    Example:
        ```python
        from fastapi import FastAPI, Depends
        from translaas.extensions.fastapi import get_translaas_service
        from translaas.service import TranslaasService

        app = FastAPI()

        @app.get('/')
        async def index(service: TranslaasService = Depends(get_translaas_service)):
            translation = await service.t('common', 'welcome')
            return {"message": translation}
        ```
    """
    if not hasattr(request.app.state, "get_translaas_service"):
        raise RuntimeError(
            "Translaas extension not initialized. Call translaas.init_app(app, options) first."
        )

    get_service_func = request.app.state.get_translaas_service
    return get_service_func(request)

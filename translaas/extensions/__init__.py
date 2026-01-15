"""Framework integrations and extensions for the Translaas SDK."""

from translaas.extensions.config import (
    django_config,
    flask_config,
    from_dict,
    from_env,
)

# Django imports (optional dependency)
try:
    from translaas.extensions.django import (
        DjangoRequestLanguageProvider,
        get_translaas_service,
        t,
    )
except ImportError:
    DjangoRequestLanguageProvider = None  # type: ignore[assignment]
    get_translaas_service = None  # type: ignore[assignment]
    t = None  # type: ignore[assignment]

# FastAPI imports (optional dependency)
try:
    from translaas.extensions.fastapi import (
        FastAPIRequestLanguageProvider,
        Translaas as FastAPITranslaas,
        get_translaas_service as get_fastapi_translaas_service,
    )
except ImportError:
    FastAPIRequestLanguageProvider = None  # type: ignore[assignment]
    FastAPITranslaas = None  # type: ignore[assignment]
    get_fastapi_translaas_service = None  # type: ignore[assignment]

# Flask imports (optional dependency)
try:
    from translaas.extensions.flask import (
        FlaskRequestLanguageProvider,
        Translaas as FlaskTranslaas,
    )
except ImportError:
    FlaskRequestLanguageProvider = None  # type: ignore[assignment]
    FlaskTranslaas = None  # type: ignore[assignment]

__all__ = [
    # Flask
    "FlaskRequestLanguageProvider",
    "FlaskTranslaas",
    # FastAPI
    "FastAPIRequestLanguageProvider",
    "FastAPITranslaas",
    "get_fastapi_translaas_service",
    # Django
    "DjangoRequestLanguageProvider",
    "get_translaas_service",
    "t",
    # Config helpers
    "from_dict",
    "from_env",
    "flask_config",
    "django_config",
]

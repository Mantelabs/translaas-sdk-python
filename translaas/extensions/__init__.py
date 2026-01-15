"""Framework integrations and extensions for the Translaas SDK."""

from typing import TYPE_CHECKING

from translaas.extensions.config import (
    django_config,
    flask_config,
    from_dict,
    from_env,
)

# Import all extensions - they handle their own optional dependencies
from translaas.extensions.django import (
    DjangoRequestLanguageProvider,
    get_translaas_service,
    t,
)
from translaas.extensions.fastapi import (
    FastAPIRequestLanguageProvider,
)
from translaas.extensions.fastapi import (
    Translaas as FastAPITranslaas,
)
from translaas.extensions.fastapi import (
    get_translaas_service as get_fastapi_translaas_service,
)
from translaas.extensions.flask import (
    FlaskRequestLanguageProvider,
)
from translaas.extensions.flask import (
    Translaas as FlaskTranslaas,
)

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

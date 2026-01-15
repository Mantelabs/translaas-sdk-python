"""Configuration helpers for framework integrations.

This module provides helper functions for configuring TranslaasOptions
from framework-specific configuration sources.
"""

from typing import Any, Dict

from translaas.models.enums import CacheMode
from translaas.models.options import TranslaasOptions


def from_dict(config: Dict[str, Any]) -> TranslaasOptions:
    """Create TranslaasOptions from a dictionary.

    This helper function creates a TranslaasOptions instance from a dictionary,
    which is useful when reading configuration from environment variables or
    configuration files.

    Args:
        config: Dictionary containing configuration values. Supported keys:
            - api_key (str, required): API key for Translaas
            - base_url (str, required): Base URL for Translaas API
            - cache_mode (str, optional): Cache mode ('NONE', 'ENTRY', 'GROUP', 'PROJECT')
            - timeout (float, optional): Timeout in seconds
            - cache_absolute_expiration (float, optional): Cache absolute expiration in seconds
            - cache_sliding_expiration (float, optional): Cache sliding expiration in seconds
            - default_language (str, optional): Default language code

    Returns:
        A TranslaasOptions instance.

    Raises:
        ValueError: If required keys are missing.

    Example:
        ```python
        config = {
            "api_key": "your-api-key",
            "base_url": "https://api.translaas.com",
            "cache_mode": "GROUP",
            "default_language": "en",
        }
        options = from_dict(config)
        ```
    """
    if "api_key" not in config or "base_url" not in config:
        raise ValueError("api_key and base_url are required in config dictionary")

    # Convert cache_mode string to enum if provided
    cache_mode = CacheMode.NONE
    if "cache_mode" in config:
        cache_mode_str = config["cache_mode"]
        if isinstance(cache_mode_str, str):
            cache_mode = CacheMode[cache_mode_str.upper()]
        elif isinstance(cache_mode_str, CacheMode):
            cache_mode = cache_mode_str

    # Convert timeout to timedelta if provided
    timeout = None
    if "timeout" in config and config["timeout"] is not None:
        from datetime import timedelta

        timeout_seconds = config["timeout"]
        if isinstance(timeout_seconds, (int, float)):
            timeout = timedelta(seconds=timeout_seconds)

    # Convert cache expiration to timedelta if provided
    cache_absolute_expiration = None
    if "cache_absolute_expiration" in config and config["cache_absolute_expiration"] is not None:
        from datetime import timedelta

        expiration_seconds = config["cache_absolute_expiration"]
        if isinstance(expiration_seconds, (int, float)):
            cache_absolute_expiration = timedelta(seconds=expiration_seconds)

    cache_sliding_expiration = None
    if "cache_sliding_expiration" in config and config["cache_sliding_expiration"] is not None:
        from datetime import timedelta

        expiration_seconds = config["cache_sliding_expiration"]
        if isinstance(expiration_seconds, (int, float)):
            cache_sliding_expiration = timedelta(seconds=expiration_seconds)

    return TranslaasOptions(
        api_key=config["api_key"],
        base_url=config["base_url"],
        cache_mode=cache_mode,
        timeout=timeout,
        cache_absolute_expiration=cache_absolute_expiration,
        cache_sliding_expiration=cache_sliding_expiration,
        default_language=config.get("default_language"),
    )


def from_env(prefix: str = "TRANSLAAS_") -> TranslaasOptions:
    """Create TranslaasOptions from environment variables.

    This helper function creates a TranslaasOptions instance from environment variables.
    Environment variable names are prefixed with the given prefix (default: 'TRANSLAAS_').

    Args:
        prefix: Prefix for environment variable names. Default: 'TRANSLAAS_'

    Returns:
        A TranslaasOptions instance.

    Raises:
        ValueError: If required environment variables are missing.

    Example:
        ```python
        # Reads from TRANSLAAS_API_KEY, TRANSLAAS_BASE_URL, etc.
        options = from_env()

        # Reads from CUSTOM_API_KEY, CUSTOM_BASE_URL, etc.
        options = from_env(prefix="CUSTOM_")
        ```
    """
    import os

    config: Dict[str, Any] = {}

    # Required variables
    api_key = os.getenv(f"{prefix}API_KEY")
    base_url = os.getenv(f"{prefix}BASE_URL")

    if not api_key or not base_url:
        raise ValueError(f"{prefix}API_KEY and {prefix}BASE_URL environment variables are required")

    config["api_key"] = api_key
    config["base_url"] = base_url

    # Optional variables
    cache_mode = os.getenv(f"{prefix}CACHE_MODE")
    if cache_mode:
        config["cache_mode"] = cache_mode

    timeout = os.getenv(f"{prefix}TIMEOUT")
    if timeout:
        try:
            config["timeout"] = float(timeout)
        except ValueError:
            pass

    cache_absolute_expiration = os.getenv(f"{prefix}CACHE_ABSOLUTE_EXPIRATION")
    if cache_absolute_expiration:
        try:
            config["cache_absolute_expiration"] = float(cache_absolute_expiration)
        except ValueError:
            pass

    cache_sliding_expiration = os.getenv(f"{prefix}CACHE_SLIDING_EXPIRATION")
    if cache_sliding_expiration:
        try:
            config["cache_sliding_expiration"] = float(cache_sliding_expiration)
        except ValueError:
            pass

    default_language = os.getenv(f"{prefix}DEFAULT_LANGUAGE")
    if default_language:
        config["default_language"] = default_language

    return from_dict(config)


def flask_config(app_config: Dict[str, Any]) -> TranslaasOptions:
    """Create TranslaasOptions from Flask app.config.

    This helper function creates a TranslaasOptions instance from Flask's app.config dictionary.

    Args:
        app_config: Flask app.config dictionary. Supported keys:
            - TRANSLAAS_API_KEY (str, required)
            - TRANSLAAS_BASE_URL (str, required)
            - TRANSLAAS_CACHE_MODE (str, optional)
            - TRANSLAAS_TIMEOUT (float, optional)
            - TRANSLAAS_CACHE_ABSOLUTE_EXPIRATION (float, optional)
            - TRANSLAAS_CACHE_SLIDING_EXPIRATION (float, optional)
            - TRANSLAAS_DEFAULT_LANGUAGE (str, optional)

    Returns:
        A TranslaasOptions instance.

    Raises:
        ValueError: If required config keys are missing.

    Example:
        ```python
        from flask import Flask
        from translaas.extensions.config import flask_config

        app = Flask(__name__)
        app.config["TRANSLAAS_API_KEY"] = "your-api-key"
        app.config["TRANSLAAS_BASE_URL"] = "https://api.translaas.com"

        options = flask_config(app.config)
        ```
    """
    config: Dict[str, Any] = {}

    # Map Flask config keys to our config dict
    key_mapping = {
        "TRANSLAAS_API_KEY": "api_key",
        "TRANSLAAS_BASE_URL": "base_url",
        "TRANSLAAS_CACHE_MODE": "cache_mode",
        "TRANSLAAS_TIMEOUT": "timeout",
        "TRANSLAAS_CACHE_ABSOLUTE_EXPIRATION": "cache_absolute_expiration",
        "TRANSLAAS_CACHE_SLIDING_EXPIRATION": "cache_sliding_expiration",
        "TRANSLAAS_DEFAULT_LANGUAGE": "default_language",
    }

    for flask_key, config_key in key_mapping.items():
        if flask_key in app_config:
            config[config_key] = app_config[flask_key]

    return from_dict(config)


def django_config(settings_module: Any) -> TranslaasOptions:
    """Create TranslaasOptions from Django settings.

    This helper function creates a TranslaasOptions instance from Django settings module.

    Args:
        settings_module: Django settings module (typically django.conf.settings).
            Supported settings:
            - TRANSLAAS_API_KEY (str, required)
            - TRANSLAAS_BASE_URL (str, required)
            - TRANSLAAS_CACHE_MODE (str, optional)
            - TRANSLAAS_TIMEOUT (float, optional)
            - TRANSLAAS_CACHE_ABSOLUTE_EXPIRATION (float, optional)
            - TRANSLAAS_CACHE_SLIDING_EXPIRATION (float, optional)
            - TRANSLAAS_DEFAULT_LANGUAGE (str, optional)

    Returns:
        A TranslaasOptions instance.

    Raises:
        ValueError: If required settings are missing.

    Example:
        ```python
        from django.conf import settings
        from translaas.extensions.config import django_config

        options = django_config(settings)
        ```
    """
    config: Dict[str, Any] = {}

    # Map Django settings to our config dict
    key_mapping = {
        "TRANSLAAS_API_KEY": "api_key",
        "TRANSLAAS_BASE_URL": "base_url",
        "TRANSLAAS_CACHE_MODE": "cache_mode",
        "TRANSLAAS_TIMEOUT": "timeout",
        "TRANSLAAS_CACHE_ABSOLUTE_EXPIRATION": "cache_absolute_expiration",
        "TRANSLAAS_CACHE_SLIDING_EXPIRATION": "cache_sliding_expiration",
        "TRANSLAAS_DEFAULT_LANGUAGE": "default_language",
    }

    for django_key, config_key in key_mapping.items():
        if hasattr(settings_module, django_key):
            value = getattr(settings_module, django_key)
            if value is not None:
                config[config_key] = value

    return from_dict(config)

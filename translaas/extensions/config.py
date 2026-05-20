"""Configuration helpers for framework integrations."""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Any, Dict, Optional

from translaas.models.enums import CacheMode, OfflineFallbackMode
from translaas.models.options import OfflineCacheOptions, TranslaasOptions


def _parse_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
    return None


def _parse_timedelta_seconds(value: Any) -> Optional[timedelta]:
    if value is None:
        return None
    if isinstance(value, timedelta):
        return value
    if isinstance(value, (int, float)):
        return timedelta(seconds=float(value))
    return None


def _parse_offline_fallback(value: Any) -> OfflineFallbackMode:
    if isinstance(value, OfflineFallbackMode):
        return value
    if isinstance(value, str):
        normalized = value.strip().upper().replace("-", "_")
        for mode in OfflineFallbackMode:
            if mode.name == normalized:
                return mode
    return OfflineFallbackMode.CACHE_FIRST


def build_translaas_options(config: Dict[str, Any]) -> TranslaasOptions:
    """Build ``TranslaasOptions`` from a normalized flat configuration dict."""
    if "api_key" not in config or "base_url" not in config:
        raise ValueError("api_key and base_url are required in config dictionary")

    cache_mode = CacheMode.NONE
    if "cache_mode" in config and config["cache_mode"] is not None:
        cache_mode_value = config["cache_mode"]
        if isinstance(cache_mode_value, CacheMode):
            cache_mode = cache_mode_value
        elif isinstance(cache_mode_value, str):
            cache_mode = CacheMode[cache_mode_value.upper()]

    offline_cache: Optional[OfflineCacheOptions] = None
    offline_enabled = _parse_bool(config.get("offline_cache_enabled"))
    if offline_enabled:
        offline_cache = OfflineCacheOptions(
            enabled=True,
            cache_directory=str(config.get("offline_cache_directory") or ".translaas-cache"),
            fallback_mode=_parse_offline_fallback(
                config.get("offline_fallback_mode", OfflineFallbackMode.CACHE_FIRST)
            ),
            default_project_id=config.get("offline_default_project_id")
            or config.get("default_project"),
            auto_sync=_parse_bool(config.get("offline_auto_sync")) is not False,
        )
        interval = _parse_timedelta_seconds(config.get("offline_auto_sync_interval_seconds"))
        if interval is not None:
            offline_cache.auto_sync_interval = interval

    return TranslaasOptions(
        api_key=str(config["api_key"]),
        base_url=str(config["base_url"]),
        cache_mode=cache_mode,
        timeout=_parse_timedelta_seconds(config.get("timeout")),
        cache_absolute_expiration=_parse_timedelta_seconds(
            config.get("cache_absolute_expiration")
        ),
        cache_sliding_expiration=_parse_timedelta_seconds(config.get("cache_sliding_expiration")),
        offline_cache=offline_cache,
        default_language=config.get("default_language"),
        verify=_parse_bool(config.get("verify")) is not False,
        default_project=config.get("default_project"),
        channel=config.get("channel"),
        snapshot_version=config.get("snapshot_version"),
        include_context=_parse_bool(config.get("include_context")),
        use_conditional_requests=_parse_bool(config.get("use_conditional_requests")) is True,
        api_key_header=str(config.get("api_key_header") or "X-Api-Key"),
        sdk_translations_path_prefix=config.get("sdk_translations_path_prefix"),
    )


def from_dict(config: Dict[str, Any]) -> TranslaasOptions:
    """Create ``TranslaasOptions`` from a dictionary."""
    return build_translaas_options(config)


def from_env(prefix: str = "TRANSLAAS_") -> TranslaasOptions:
    """Create ``TranslaasOptions`` from environment variables."""
    config: Dict[str, Any] = {}

    api_key = os.getenv(f"{prefix}API_KEY")
    base_url = os.getenv(f"{prefix}BASE_URL")
    if not api_key or not base_url:
        raise ValueError(f"{prefix}API_KEY and {prefix}BASE_URL environment variables are required")

    config["api_key"] = api_key
    config["base_url"] = base_url

    optional_string_keys = {
        f"{prefix}CACHE_MODE": "cache_mode",
        f"{prefix}DEFAULT_LANGUAGE": "default_language",
        f"{prefix}DEFAULT_PROJECT": "default_project",
        f"{prefix}CHANNEL": "channel",
        f"{prefix}SNAPSHOT_VERSION": "snapshot_version",
        f"{prefix}API_KEY_HEADER": "api_key_header",
        f"{prefix}SDK_TRANSLATIONS_PATH_PREFIX": "sdk_translations_path_prefix",
        f"{prefix}OFFLINE_CACHE_DIRECTORY": "offline_cache_directory",
        f"{prefix}OFFLINE_FALLBACK_MODE": "offline_fallback_mode",
        f"{prefix}OFFLINE_DEFAULT_PROJECT_ID": "offline_default_project_id",
    }
    for env_key, config_key in optional_string_keys.items():
        value = os.getenv(env_key)
        if value:
            config[config_key] = value

    optional_bool_keys = {
        f"{prefix}VERIFY": "verify",
        f"{prefix}INCLUDE_CONTEXT": "include_context",
        f"{prefix}USE_CONDITIONAL_REQUESTS": "use_conditional_requests",
        f"{prefix}OFFLINE_CACHE_ENABLED": "offline_cache_enabled",
        f"{prefix}OFFLINE_AUTO_SYNC": "offline_auto_sync",
    }
    for env_key, config_key in optional_bool_keys.items():
        value = os.getenv(env_key)
        if value is not None:
            config[config_key] = value

    for env_key, config_key in (
        (f"{prefix}TIMEOUT", "timeout"),
        (f"{prefix}CACHE_ABSOLUTE_EXPIRATION", "cache_absolute_expiration"),
        (f"{prefix}CACHE_SLIDING_EXPIRATION", "cache_sliding_expiration"),
        (f"{prefix}OFFLINE_AUTO_SYNC_INTERVAL_SECONDS", "offline_auto_sync_interval_seconds"),
    ):
        value = os.getenv(env_key)
        if value:
            try:
                config[config_key] = float(value)
            except ValueError:
                pass

    return build_translaas_options(config)


_COMMON_KEY_MAPPING = {
    "TRANSLAAS_API_KEY": "api_key",
    "TRANSLAAS_BASE_URL": "base_url",
    "TRANSLAAS_CACHE_MODE": "cache_mode",
    "TRANSLAAS_TIMEOUT": "timeout",
    "TRANSLAAS_CACHE_ABSOLUTE_EXPIRATION": "cache_absolute_expiration",
    "TRANSLAAS_CACHE_SLIDING_EXPIRATION": "cache_sliding_expiration",
    "TRANSLAAS_DEFAULT_LANGUAGE": "default_language",
    "TRANSLAAS_DEFAULT_PROJECT": "default_project",
    "TRANSLAAS_CHANNEL": "channel",
    "TRANSLAAS_SNAPSHOT_VERSION": "snapshot_version",
    "TRANSLAAS_INCLUDE_CONTEXT": "include_context",
    "TRANSLAAS_USE_CONDITIONAL_REQUESTS": "use_conditional_requests",
    "TRANSLAAS_VERIFY": "verify",
    "TRANSLAAS_API_KEY_HEADER": "api_key_header",
    "TRANSLAAS_SDK_TRANSLATIONS_PATH_PREFIX": "sdk_translations_path_prefix",
    "TRANSLAAS_OFFLINE_CACHE_ENABLED": "offline_cache_enabled",
    "TRANSLAAS_OFFLINE_CACHE_DIRECTORY": "offline_cache_directory",
    "TRANSLAAS_OFFLINE_FALLBACK_MODE": "offline_fallback_mode",
    "TRANSLAAS_OFFLINE_DEFAULT_PROJECT_ID": "offline_default_project_id",
    "TRANSLAAS_OFFLINE_AUTO_SYNC": "offline_auto_sync",
    "TRANSLAAS_OFFLINE_AUTO_SYNC_INTERVAL_SECONDS": "offline_auto_sync_interval_seconds",
}


def _config_from_mapped_source(source: Any, mapping: Dict[str, str]) -> Dict[str, Any]:
    config: Dict[str, Any] = {}
    for source_key, config_key in mapping.items():
        if hasattr(source, source_key):
            value = getattr(source, source_key)
        elif isinstance(source, dict) and source_key in source:
            value = source[source_key]
        else:
            continue
        if value is not None:
            config[config_key] = value
    return config


def flask_config(app_config: Dict[str, Any]) -> TranslaasOptions:
    """Create ``TranslaasOptions`` from Flask ``app.config``."""
    return build_translaas_options(_config_from_mapped_source(app_config, _COMMON_KEY_MAPPING))


def django_config(settings_module: Any) -> TranslaasOptions:
    """Create ``TranslaasOptions`` from Django settings."""
    return build_translaas_options(_config_from_mapped_source(settings_module, _COMMON_KEY_MAPPING))

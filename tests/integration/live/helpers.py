"""Shared helpers for live API integration tests."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

import pytest

from translaas.client.client import TranslaasClient
from translaas.exceptions import TranslaasApiException
from translaas.models.options import TranslaasOptions

# Fixture ids aligned with translaas-sdk-examples (translaas_sdk_samples_strings.csv).
DEFAULT_BASE_URL = "https://api.translaas.local"
DEFAULT_PROJECT = "translaas-sdk-samples"
FIXTURE_GROUP = "common"
FIXTURE_GROUP_MESSAGES = "messages"
FIXTURE_ENTRY_SAVE = "welcome.message"
FIXTURE_ENTRY_PLURAL = "item"
FIXTURE_LANG = "en"
COMMON_LOCALES = ("en", "fr", "es", "de")

_reachability: Optional[bool] = None
_reachability_lock = asyncio.Lock()


@dataclass(frozen=True)
class LiveConfig:
    """Environment configuration for live API integration tests."""

    api_key: str
    base_url: str
    default_project: str


def load_live_config() -> Optional[LiveConfig]:
    """Load live test configuration from environment variables."""
    api_key = os.getenv("TRANSLAAS_API_KEY", "").strip()
    if not api_key:
        return None
    base_url = os.getenv("TRANSLAAS_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL
    default_project = (
        os.getenv("TRANSLAAS_DEFAULT_PROJECT", DEFAULT_PROJECT).strip() or DEFAULT_PROJECT
    )
    return LiveConfig(api_key=api_key, base_url=base_url, default_project=default_project)


def build_options(
    cfg: LiveConfig,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    default_project: Optional[str] = None,
    timeout: Optional[timedelta] = None,
) -> TranslaasOptions:
    """Build SDK options for integration tests (self-signed TLS allowed for local Docker)."""
    return TranslaasOptions(
        api_key=api_key if api_key is not None else cfg.api_key,
        base_url=base_url if base_url is not None else cfg.base_url,
        default_project=default_project if default_project is not None else cfg.default_project,
        timeout=timeout,
        verify=False,
    )


def is_sdk_not_found(exc: TranslaasApiException) -> bool:
    """True when the delivery API reports a missing SDK resource (Mantelabs uses HTTP 404)."""
    return exc.status_code == 404


def soft_skip_if(condition: bool, message: str) -> None:
    """Skip the current test when fixture data is unavailable."""
    if condition:
        pytest.skip(message)


def soft_skip_on_sdk_not_found(exc: TranslaasApiException) -> None:
    """Skip when the configured project or resource is missing on the API."""
    if is_sdk_not_found(exc):
        pytest.skip(
            "SDK resource not found (HTTP 404) — set TRANSLAAS_DEFAULT_PROJECT to an "
            f"existing project id (default: {DEFAULT_PROJECT})"
        )


def _is_transport_failure(exc: TranslaasApiException) -> bool:
    message = exc.message.lower()
    return any(
        token in message
        for token in (
            "failed to connect",
            "connection refused",
            "no such host",
            "network error",
            "error sending request",
        )
    )


async def _probe_api(cfg: LiveConfig) -> bool:
    options = build_options(cfg, timeout=timedelta(seconds=5))
    try:
        async with TranslaasClient(options) as client:
            await client.validate_api_key()
        return True
    except TranslaasApiException as exc:
        if exc.status_code in (401, 403):
            return True
        if _is_transport_failure(exc):
            return False
        return True
    except Exception:
        return False


async def ensure_api_reachable(cfg: LiveConfig) -> bool:
    """Return True when the configured API origin responds to validate_api_key."""
    global _reachability
    async with _reachability_lock:
        if _reachability is None:
            _reachability = await _probe_api(cfg)
        return _reachability

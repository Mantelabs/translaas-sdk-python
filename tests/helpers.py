"""Test utilities and helper functions for the Translaas SDK test suite.

This module provides utility functions and helpers for writing tests.
"""

import json
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

import httpx

from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject


def create_mock_response(
    status_code: int = 200,
    text: Optional[str] = None,
    json_data: Optional[Dict[str, Any]] = None,
    url: str = "https://api.test.com/api/translations/text",
) -> httpx.Response:
    """Create a mock HTTP response.

    Args:
        status_code: HTTP status code. Defaults to 200.
        text: Response text content. Defaults to None.
        json_data: Response JSON data. Defaults to None.
        url: Request URL. Defaults to test URL.

    Returns:
        httpx.Response instance with the specified data.
    """
    if json_data:
        text = json.dumps(json_data)

    return httpx.Response(
        status_code,
        text=text or "",
        request=httpx.Request("GET", url),
    )


def create_mock_translation_group(entries: Optional[Dict[str, Any]] = None) -> TranslationGroup:
    """Create a mock TranslationGroup with test data.

    Args:
        entries: Optional dictionary of translation entries.
                Defaults to sample entries.

    Returns:
        TranslationGroup instance.
    """
    if entries is None:
        entries = {
            "entry1": "Hello, World!",
            "entry2": "Goodbye, World!",
        }
    return TranslationGroup(entries=entries)


def create_mock_translation_project(
    groups: Optional[Dict[str, TranslationGroup]] = None,
) -> TranslationProject:
    """Create a mock TranslationProject with test data.

    Args:
        groups: Optional dictionary of translation groups.
                Defaults to sample groups.

    Returns:
        TranslationProject instance.
    """
    if groups is None:
        groups = {
            "group1": create_mock_translation_group({"entry1": "Hello", "entry2": "World"}),
            "group2": create_mock_translation_group({"entry3": "Foo", "entry4": "Bar"}),
        }
    return TranslationProject(groups=groups)


def create_mock_project_locales(locales: Optional[list[str]] = None) -> ProjectLocales:
    """Create a mock ProjectLocales with test data.

    Args:
        locales: Optional list of locale codes. Defaults to common locales.

    Returns:
        ProjectLocales instance.
    """
    if locales is None:
        locales = ["en", "es", "fr", "de"]
    return ProjectLocales(locales=locales)


def create_mock_httpx_client(
    response: Optional[httpx.Response] = None,
    side_effect: Optional[Any] = None,
) -> MagicMock:
    """Create a mock httpx.AsyncClient.

    Args:
        response: Optional response to return. Defaults to None.
        side_effect: Optional side effect function. Defaults to None.

    Returns:
        MagicMock instance configured as httpx.AsyncClient.
    """
    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_get = AsyncMock(return_value=response) if response else AsyncMock(side_effect=side_effect)
    mock_client.get = mock_get
    mock_client.post = mock_get  # Reuse for simplicity
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


def assert_translation_group_equal(group1: TranslationGroup, group2: TranslationGroup) -> bool:
    """Assert that two TranslationGroup instances are equal.

    Args:
        group1: First TranslationGroup instance.
        group2: Second TranslationGroup instance.

    Returns:
        True if groups are equal, False otherwise.
    """
    return group1.entries == group2.entries


def assert_translation_project_equal(
    project1: TranslationProject, project2: TranslationProject
) -> bool:
    """Assert that two TranslationProject instances are equal.

    Args:
        project1: First TranslationProject instance.
        project2: Second TranslationProject instance.

    Returns:
        True if projects are equal, False otherwise.
    """
    if set(project1.groups.keys()) != set(project2.groups.keys()):
        return False

    for group_name in project1.groups:
        if not assert_translation_group_equal(
            project1.groups[group_name], project2.groups[group_name]
        ):
            return False

    return True

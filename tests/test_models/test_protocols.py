"""Tests for protocol definitions.

Protocols use structural typing, so we test compliance by creating
mock implementations that satisfy the protocol interface.
"""

from typing import Dict, Optional

import pytest

from translaas.models.protocols import (
    ILanguageProvider,
    ITranslaasCacheProvider,
    ITranslaasClient,
    ITranslaasService,
)
from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject


class MockTranslaasClient:
    """Mock implementation of ITranslaasClient for testing."""

    async def get_entry(
        self,
        group: str,
        entry: str,
        lang: str,
        number: Optional[float] = None,
        parameters: Optional[Dict[str, str]] = None,
    ) -> str:
        """Mock get_entry implementation."""
        return f"{group}.{entry}.{lang}"

    async def get_group(
        self,
        project: str,
        group: str,
        lang: str,
        format: Optional[str] = None,
    ) -> TranslationGroup:
        """Mock get_group implementation."""
        return TranslationGroup(entries={"test": "value"})

    async def get_project(
        self,
        project: str,
        lang: str,
        format: Optional[str] = None,
    ) -> TranslationProject:
        """Mock get_project implementation."""
        return TranslationProject(groups={"test": {}})

    async def get_project_locales(
        self,
        project: str,
    ) -> ProjectLocales:
        """Mock get_project_locales implementation."""
        return ProjectLocales(locales=["en", "fr"])


class MockTranslaasService:
    """Mock implementation of ITranslaasService for testing."""

    async def t(
        self,
        group: str,
        entry: str,
        lang: Optional[str] = None,
        number: Optional[float] = None,
        parameters: Optional[Dict[str, str]] = None,
    ) -> str:
        """Mock t implementation."""
        return f"{group}.{entry}"


class MockCacheProvider:
    """Mock implementation of ITranslaasCacheProvider for testing."""

    def __init__(self) -> None:
        """Initialize mock cache provider."""
        self._cache: Dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:
        """Mock get implementation."""
        return self._cache.get(key)

    def set(
        self,
        key: str,
        value: str,
        absolute_expiration_ms: Optional[int] = None,
        sliding_expiration_ms: Optional[int] = None,
    ) -> None:
        """Mock set implementation."""
        self._cache[key] = value

    def remove(self, key: str) -> None:
        """Mock remove implementation."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Mock clear implementation."""
        self._cache.clear()


class MockLanguageProvider:
    """Mock implementation of ILanguageProvider for testing."""

    def __init__(self, language: Optional[str] = None) -> None:
        """Initialize mock language provider."""
        self.language = language

    async def get_language(self) -> Optional[str]:
        """Mock get_language implementation."""
        return self.language


class TestProtocolCompliance:
    """Tests for protocol compliance using structural typing."""

    @pytest.mark.asyncio
    async def test_translaas_client_protocol(self) -> None:
        """Test that MockTranslaasClient satisfies ITranslaasClient protocol."""
        client: ITranslaasClient = MockTranslaasClient()

        result = await client.get_entry("group", "entry", "en")
        assert result == "group.entry.en"

        group = await client.get_group("project", "group", "en")
        assert isinstance(group, TranslationGroup)

        project = await client.get_project("project", "en")
        assert isinstance(project, TranslationProject)

        locales = await client.get_project_locales("project")
        assert isinstance(locales, ProjectLocales)

    @pytest.mark.asyncio
    async def test_translaas_service_protocol(self) -> None:
        """Test that MockTranslaasService satisfies ITranslaasService protocol."""
        service: ITranslaasService = MockTranslaasService()

        result = await service.t("group", "entry")
        assert result == "group.entry"

        result = await service.t("group", "entry", lang="en")
        assert result == "group.entry"

        result = await service.t("group", "entry", number=1.0)
        assert result == "group.entry"

    def test_cache_provider_protocol(self) -> None:
        """Test that MockCacheProvider satisfies ITranslaasCacheProvider protocol."""
        cache: ITranslaasCacheProvider = MockCacheProvider()

        assert cache.get("key1") is None

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.remove("key1")
        assert cache.get("key1") is None

        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_language_provider_protocol(self) -> None:
        """Test that MockLanguageProvider satisfies ILanguageProvider protocol."""
        provider: ILanguageProvider = MockLanguageProvider("en")

        language = await provider.get_language()
        assert language == "en"

        provider_none = MockLanguageProvider(None)
        language_none = await provider_none.get_language()
        assert language_none is None

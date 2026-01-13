"""Tests for enum definitions."""

import pytest

from translaas.models.enums import CacheMode, OfflineFallbackMode, PluralCategory


class TestCacheMode:
    """Tests for CacheMode enum."""

    def test_cache_mode_values(self) -> None:
        """Test that CacheMode has correct values."""
        assert CacheMode.NONE.value == 0
        assert CacheMode.ENTRY.value == 1
        assert CacheMode.GROUP.value == 2
        assert CacheMode.PROJECT.value == 3

    def test_cache_mode_members(self) -> None:
        """Test that all CacheMode members exist."""
        assert CacheMode.NONE in CacheMode
        assert CacheMode.ENTRY in CacheMode
        assert CacheMode.GROUP in CacheMode
        assert CacheMode.PROJECT in CacheMode

    def test_cache_mode_iteration(self) -> None:
        """Test that CacheMode can be iterated."""
        modes = list(CacheMode)
        assert len(modes) == 4
        assert CacheMode.NONE in modes
        assert CacheMode.ENTRY in modes
        assert CacheMode.GROUP in modes
        assert CacheMode.PROJECT in modes


class TestOfflineFallbackMode:
    """Tests for OfflineFallbackMode enum."""

    def test_offline_fallback_mode_values(self) -> None:
        """Test that OfflineFallbackMode has correct values."""
        assert OfflineFallbackMode.CACHE_FIRST.value == 0
        assert OfflineFallbackMode.API_FIRST.value == 1
        assert OfflineFallbackMode.CACHE_ONLY.value == 2
        assert OfflineFallbackMode.API_ONLY_WITH_BACKUP.value == 3

    def test_offline_fallback_mode_members(self) -> None:
        """Test that all OfflineFallbackMode members exist."""
        assert OfflineFallbackMode.CACHE_FIRST in OfflineFallbackMode
        assert OfflineFallbackMode.API_FIRST in OfflineFallbackMode
        assert OfflineFallbackMode.CACHE_ONLY in OfflineFallbackMode
        assert OfflineFallbackMode.API_ONLY_WITH_BACKUP in OfflineFallbackMode


class TestPluralCategory:
    """Tests for PluralCategory enum."""

    def test_plural_category_values(self) -> None:
        """Test that PluralCategory has correct string values."""
        assert PluralCategory.ZERO.value == "zero"
        assert PluralCategory.ONE.value == "one"
        assert PluralCategory.TWO.value == "two"
        assert PluralCategory.FEW.value == "few"
        assert PluralCategory.MANY.value == "many"
        assert PluralCategory.OTHER.value == "other"

    def test_plural_category_members(self) -> None:
        """Test that all PluralCategory members exist."""
        assert PluralCategory.ZERO in PluralCategory
        assert PluralCategory.ONE in PluralCategory
        assert PluralCategory.TWO in PluralCategory
        assert PluralCategory.FEW in PluralCategory
        assert PluralCategory.MANY in PluralCategory
        assert PluralCategory.OTHER in PluralCategory

    def test_plural_category_from_value(self) -> None:
        """Test creating PluralCategory from string value."""
        assert PluralCategory("zero") == PluralCategory.ZERO
        assert PluralCategory("one") == PluralCategory.ONE
        assert PluralCategory("other") == PluralCategory.OTHER

    def test_plural_category_invalid_value(self) -> None:
        """Test that invalid PluralCategory value raises ValueError."""
        with pytest.raises(ValueError):
            PluralCategory("invalid")

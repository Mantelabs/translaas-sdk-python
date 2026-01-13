"""Tests for configuration models."""

from datetime import timedelta

import pytest

from translaas.models.enums import CacheMode, OfflineFallbackMode
from translaas.models.options import (
    HybridCacheOptions,
    OfflineCacheOptions,
    TranslaasOptions,
)


class TestTranslaasOptions:
    """Tests for TranslaasOptions."""

    def test_create_with_required_fields(self) -> None:
        """Test creating TranslaasOptions with required fields."""
        options = TranslaasOptions(
            api_key="test-api-key",
            base_url="https://api.example.com",
        )
        assert options.api_key == "test-api-key"
        assert options.base_url == "https://api.example.com"
        assert options.cache_mode == CacheMode.NONE

    def test_create_with_all_fields(self) -> None:
        """Test creating TranslaasOptions with all fields."""
        timeout = timedelta(seconds=30)
        cache_expiration = timedelta(minutes=5)
        offline_cache = OfflineCacheOptions(enabled=True)

        options = TranslaasOptions(
            api_key="test-api-key",
            base_url="https://api.example.com",
            cache_mode=CacheMode.GROUP,
            timeout=timeout,
            cache_absolute_expiration=cache_expiration,
            cache_sliding_expiration=cache_expiration,
            offline_cache=offline_cache,
            default_language="en",
        )

        assert options.api_key == "test-api-key"
        assert options.base_url == "https://api.example.com"
        assert options.cache_mode == CacheMode.GROUP
        assert options.timeout == timeout
        assert options.cache_absolute_expiration == cache_expiration
        assert options.offline_cache == offline_cache
        assert options.default_language == "en"

    def test_validation_empty_api_key(self) -> None:
        """Test that empty api_key raises ValueError."""
        with pytest.raises(ValueError, match="api_key is required"):
            TranslaasOptions(api_key="", base_url="https://api.example.com")

    def test_validation_none_api_key(self) -> None:
        """Test that None api_key raises ValueError."""
        with pytest.raises(ValueError, match="api_key is required"):
            TranslaasOptions(api_key=None, base_url="https://api.example.com")  # type: ignore

    def test_validation_empty_base_url(self) -> None:
        """Test that empty base_url raises ValueError."""
        with pytest.raises(ValueError, match="base_url is required"):
            TranslaasOptions(api_key="test-key", base_url="")

    def test_validation_none_base_url(self) -> None:
        """Test that None base_url raises ValueError."""
        with pytest.raises(ValueError, match="base_url is required"):
            TranslaasOptions(api_key="test-key", base_url=None)  # type: ignore

    def test_validation_whitespace_api_key(self) -> None:
        """Test that whitespace-only api_key raises ValueError."""
        with pytest.raises(ValueError, match="api_key is required"):
            TranslaasOptions(api_key="   ", base_url="https://api.example.com")


class TestOfflineCacheOptions:
    """Tests for OfflineCacheOptions."""

    def test_create_with_defaults(self) -> None:
        """Test creating OfflineCacheOptions with defaults."""
        options = OfflineCacheOptions()
        assert options.enabled is False
        assert options.cache_directory == ".translaas-cache"
        assert options.fallback_mode == OfflineFallbackMode.CACHE_FIRST
        assert options.auto_sync is True
        assert options.projects == []
        assert options.languages == []

    def test_create_with_custom_values(self) -> None:
        """Test creating OfflineCacheOptions with custom values."""
        sync_interval = timedelta(hours=1)
        hybrid_cache = HybridCacheOptions(enabled=True)

        options = OfflineCacheOptions(
            enabled=True,
            cache_directory="/custom/cache",
            fallback_mode=OfflineFallbackMode.API_FIRST,
            auto_sync=False,
            auto_sync_interval=sync_interval,
            projects=["project1", "project2"],
            languages=["en", "fr"],
            default_project_id="default-project",
            hybrid_cache=hybrid_cache,
        )

        assert options.enabled is True
        assert options.cache_directory == "/custom/cache"
        assert options.fallback_mode == OfflineFallbackMode.API_FIRST
        assert options.auto_sync is False
        assert options.auto_sync_interval == sync_interval
        assert options.projects == ["project1", "project2"]
        assert options.languages == ["en", "fr"]
        assert options.default_project_id == "default-project"
        assert options.hybrid_cache == hybrid_cache


class TestHybridCacheOptions:
    """Tests for HybridCacheOptions."""

    def test_create_with_defaults(self) -> None:
        """Test creating HybridCacheOptions with defaults."""
        options = HybridCacheOptions()
        assert options.enabled is True
        assert options.memory_cache_expiration is None
        assert options.max_memory_cache_entries == 1000
        assert options.warmup_on_startup is False

    def test_create_with_custom_values(self) -> None:
        """Test creating HybridCacheOptions with custom values."""
        expiration = timedelta(minutes=10)

        options = HybridCacheOptions(
            enabled=False,
            memory_cache_expiration=expiration,
            max_memory_cache_entries=500,
            warmup_on_startup=True,
        )

        assert options.enabled is False
        assert options.memory_cache_expiration == expiration
        assert options.max_memory_cache_entries == 500
        assert options.warmup_on_startup is True

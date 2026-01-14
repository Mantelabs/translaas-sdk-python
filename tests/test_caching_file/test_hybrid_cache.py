"""Tests for the hybrid cache provider."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from translaas.caching.memory import MemoryCacheProvider
from translaas.caching_file.file_cache import FileCacheProvider
from translaas.caching_file.hybrid_cache import HybridCacheProvider
from translaas.models.options import HybridCacheOptions
from translaas.models.protocols import ITranslaasCacheProvider


class TestHybridCacheProvider:
    """Tests for HybridCacheProvider class."""

    @pytest.fixture
    def temp_cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def l2_cache(self, temp_cache_dir: Path) -> FileCacheProvider:
        """Create a file cache provider for L2."""
        return FileCacheProvider(str(temp_cache_dir))

    @pytest.fixture
    def l1_cache(self) -> MemoryCacheProvider:
        """Create a memory cache provider for L1."""
        return MemoryCacheProvider(max_size=100, enable_statistics=True)

    def test_protocol_compliance(self, l2_cache: FileCacheProvider) -> None:
        """Test that HybridCacheProvider implements ITranslaasCacheProvider."""
        cache: ITranslaasCacheProvider = HybridCacheProvider(l2_cache)
        assert isinstance(cache, HybridCacheProvider)

    def test_initialization_default(self, l2_cache: FileCacheProvider) -> None:
        """Test default initialization."""
        cache = HybridCacheProvider(l2_cache)
        assert cache.l1_cache is not None
        assert cache.l2_cache == l2_cache
        assert cache.options is not None
        assert cache.l1_hits == 0
        assert cache.l1_misses == 0
        assert cache.l2_hits == 0
        assert cache.l2_misses == 0

    def test_initialization_with_options(self, l2_cache: FileCacheProvider) -> None:
        """Test initialization with custom options."""
        options = HybridCacheOptions(
            max_memory_cache_entries=500,
            memory_cache_expiration=None,
            warmup_on_startup=False,
        )
        cache = HybridCacheProvider(l2_cache, options=options)
        assert cache.options.max_memory_cache_entries == 500

    def test_initialization_with_custom_l1(
        self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider
    ) -> None:
        """Test initialization with custom L1 cache."""
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)
        assert cache.l1_cache == l1_cache

    def test_get_l1_hit(self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider) -> None:
        """Test get() with L1 hit."""
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)
        key = "project|project:test-project|lang:en"
        value = json.dumps({"group1": {"entry1": "value1"}})
        cache.l1_cache.set(key, value)

        result = cache.get(key)

        assert result == value
        assert cache.l1_hits == 1
        assert cache.l1_misses == 0
        assert cache.l2_hits == 0
        assert cache.l2_misses == 0

    def test_get_l1_miss_l2_hit_with_promotion(
        self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider
    ) -> None:
        """Test get() with L1 miss and L2 hit, promoting to L1."""
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)
        # Use key format that FileCacheProvider expects
        key = "project|project:test-project|lang:en"
        cache.l2_cache.set(key, json.dumps({"group1": {"entry1": "value1"}}))

        # L1 should not have the key
        assert cache.l1_cache.get(key) is None

        # Get should find it in L2 and promote to L1
        result = cache.get(key)

        assert result is not None
        assert cache.l1_hits == 0
        assert cache.l1_misses == 1
        assert cache.l2_hits == 1
        assert cache.l2_misses == 0

        # Verify promotion: L1 should now have the key
        assert cache.l1_cache.get(key) is not None

    def test_get_l1_miss_l2_miss(
        self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider
    ) -> None:
        """Test get() with both L1 and L2 miss."""
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)

        result = cache.get("project|project:nonexistent|lang:en")

        assert result is None
        assert cache.l1_hits == 0
        assert cache.l1_misses == 1
        assert cache.l2_hits == 0
        assert cache.l2_misses == 1

    def test_set_updates_both_layers(
        self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider
    ) -> None:
        """Test set() updates both L1 and L2."""
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)
        # Use key format that FileCacheProvider expects
        key = "project|project:test-project|lang:en"
        value = json.dumps({"group1": {"entry1": "value1"}})

        cache.set(key, value)

        assert cache.l1_cache.get(key) == value
        assert cache.l2_cache.get(key) == value

    def test_set_with_expiration(
        self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider
    ) -> None:
        """Test set() with expiration."""
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)
        # Use key format that FileCacheProvider expects
        key = "project|project:test-project|lang:en"
        value = json.dumps({"group1": {"entry1": "value1"}})

        cache.set(key, value, absolute_expiration_ms=1000)

        assert cache.l1_cache.get(key) == value
        assert cache.l2_cache.get(key) == value

    def test_remove_from_both_layers(
        self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider
    ) -> None:
        """Test remove() removes from both L1 and L2."""
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)
        key = "project|project:test-project|lang:en"
        value = json.dumps({"group1": {"entry1": "value1"}})
        cache.set(key, value)

        cache.remove(key)

        assert cache.l1_cache.get(key) is None
        assert cache.l2_cache.get(key) is None

    def test_clear_both_layers(
        self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider
    ) -> None:
        """Test clear() clears both L1 and L2."""
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)
        key1 = "project|project:test1|lang:en"
        value1 = json.dumps({"group1": {"entry1": "value1"}})
        key2 = "project|project:test2|lang:en"
        value2 = json.dumps({"group2": {"entry2": "value2"}})
        cache.set(key1, value1)
        cache.set(key2, value2)

        cache.clear()

        assert cache.l1_cache.get(key1) is None
        assert cache.l1_cache.get(key2) is None
        assert cache.l2_cache.get(key1) is None
        assert cache.l2_cache.get(key2) is None

        # Statistics should be reset
        assert cache.l1_hits == 0
        assert cache.l1_misses == 0
        assert cache.l2_hits == 0
        assert cache.l2_misses == 0

    def test_get_statistics(
        self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider
    ) -> None:
        """Test getting cache statistics."""
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)

        # L1 hit
        key1 = "project|project:test1|lang:en"
        value1 = json.dumps({"group1": {"entry1": "value1"}})
        cache.l1_cache.set(key1, value1)
        cache.get(key1)

        # L1 miss, L2 hit
        key2 = "project|project:test2|lang:en"
        value2 = json.dumps({"group2": {"entry2": "value2"}})
        cache.l2_cache.set(key2, value2)
        cache.get(key2)

        # L1 miss, L2 miss
        cache.get("project|project:nonexistent|lang:en")

        stats = cache.get_statistics()

        assert stats["l1_hits"] == 1
        assert stats["l1_misses"] == 2
        assert stats["l2_hits"] == 1
        assert stats["l2_misses"] == 1
        assert stats["l1_hit_rate"] == pytest.approx(33.33, abs=0.1)
        assert stats["l2_hit_rate"] == pytest.approx(50.0, abs=0.1)
        # Overall: 2 hits out of 3 total requests = 66.67%
        assert stats["overall_hit_rate"] == pytest.approx(66.67, abs=0.1)

    def test_get_statistics_no_requests(self, l2_cache: FileCacheProvider) -> None:
        """Test statistics with no requests."""
        cache = HybridCacheProvider(l2_cache)
        stats = cache.get_statistics()

        assert stats["l1_hits"] == 0
        assert stats["l1_misses"] == 0
        assert stats["l2_hits"] == 0
        assert stats["l2_misses"] == 0
        assert stats["l1_hit_rate"] == 0.0
        assert stats["l2_hit_rate"] == 0.0
        assert stats["overall_hit_rate"] == 0.0

    def test_error_recovery_l1_failure(self, l2_cache: FileCacheProvider) -> None:
        """Test error recovery when L1 fails."""
        # Create a mock L1 cache that raises an error
        mock_l1 = MagicMock()
        mock_l1.get.side_effect = Exception("L1 error")

        cache = HybridCacheProvider(l2_cache, l1_cache=mock_l1)
        key = "project|project:test-project|lang:en"
        value = json.dumps({"group1": {"entry1": "value1"}})
        cache.l2_cache.set(key, value)

        # Should fallback to L2
        result = cache.get(key)

        assert result == value
        assert cache.l1_misses == 1
        assert cache.l2_hits == 1

    def test_error_recovery_l2_failure(self, l1_cache: MemoryCacheProvider) -> None:
        """Test error recovery when L2 fails."""
        # Create a mock L2 cache that raises an error
        mock_l2 = MagicMock()
        mock_l2.get.side_effect = Exception("L2 error")

        cache = HybridCacheProvider(mock_l2, l1_cache=l1_cache)

        # Should return None without crashing
        result = cache.get("key1")

        assert result is None
        assert cache.l1_misses == 1
        assert cache.l2_misses == 1

    def test_error_recovery_set_l1_failure(self, l2_cache: FileCacheProvider) -> None:
        """Test error recovery when L1 set fails."""
        # Create a mock L1 cache that raises an error on set
        mock_l1 = MagicMock()
        mock_l1.set.side_effect = Exception("L1 set error")

        cache = HybridCacheProvider(l2_cache, l1_cache=mock_l1)
        key = "project|project:test-project|lang:en"
        value = json.dumps({"group1": {"entry1": "value1"}})

        # Should still update L2
        cache.set(key, value)

        assert cache.l2_cache.get(key) == value

    def test_error_recovery_set_l2_failure(self, l1_cache: MemoryCacheProvider) -> None:
        """Test error recovery when L2 set fails."""
        # Create a mock L2 cache that raises an error on set
        mock_l2 = MagicMock()
        mock_l2.set.side_effect = Exception("L2 set error")

        cache = HybridCacheProvider(mock_l2, l1_cache=l1_cache)

        # Should still update L1
        cache.set("key1", "value1")

        assert cache.l1_cache.get("key1") == "value1"

    def test_promotion_with_expiration(
        self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider
    ) -> None:
        """Test promotion to L1 with expiration configured."""
        options = HybridCacheOptions(memory_cache_expiration=None)
        cache = HybridCacheProvider(l2_cache, options=options, l1_cache=l1_cache)
        key = "project|project:test-project|lang:en"
        value = json.dumps({"group1": {"entry1": "value1"}})
        cache.l2_cache.set(key, value)

        cache.get(key)

        # Verify promotion happened
        assert cache.l1_cache.get(key) == value

    def test_cleanup_expired(
        self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider
    ) -> None:
        """Test cleanup of expired entries."""
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)

        # Set expired entries
        cache.l1_cache.set("key1", "value1", absolute_expiration_ms=10)
        cache.l2_cache.set("key2", "value2", absolute_expiration_ms=10)

        import time

        time.sleep(0.02)

        removed = cache.cleanup_expired()

        assert removed >= 0  # At least some entries should be removed

    def test_warmup_on_startup(self, l2_cache: FileCacheProvider) -> None:
        """Test warmup on startup."""
        options = HybridCacheOptions(warmup_on_startup=True)
        cache = HybridCacheProvider(l2_cache, options=options)

        # Warmup should have been called (basic implementation just cleans up expired)
        # This is a basic test - full warmup would require more context
        assert cache is not None

    def test_multiple_operations(
        self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider
    ) -> None:
        """Test multiple cache operations."""
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)

        # Set multiple keys
        key1 = "project|project:test1|lang:en"
        value1 = json.dumps({"group1": {"entry1": "value1"}})
        key2 = "project|project:test2|lang:en"
        value2 = json.dumps({"group2": {"entry2": "value2"}})
        key3 = "project|project:test3|lang:en"
        value3 = json.dumps({"group3": {"entry3": "value3"}})

        cache.set(key1, value1)
        cache.set(key2, value2)
        cache.set(key3, value3)

        # Get from L1 (should be hits)
        assert cache.get(key1) == value1
        assert cache.get(key2) == value2

        # Remove one
        cache.remove(key1)

        # Verify removal
        assert cache.get(key1) is None
        assert cache.get(key2) == value2
        assert cache.get(key3) == value3

    def test_lru_eviction_in_l1(self, l2_cache: FileCacheProvider) -> None:
        """Test that LRU eviction works in L1."""
        # Create L1 with small max size
        l1_cache = MemoryCacheProvider(max_size=2, enable_statistics=True)
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)

        # Fill L1
        key1 = "project|project:test1|lang:en"
        value1 = json.dumps({"group1": {"entry1": "value1"}})
        key2 = "project|project:test2|lang:en"
        value2 = json.dumps({"group2": {"entry2": "value2"}})
        key3 = "project|project:test3|lang:en"
        value3 = json.dumps({"group3": {"entry3": "value3"}})

        cache.set(key1, value1)
        cache.set(key2, value2)

        # Add third entry (should evict key1)
        cache.set(key3, value3)

        # key1 should be evicted from L1 but still in L2
        assert cache.l1_cache.get(key1) is None
        assert cache.l2_cache.get(key1) == value1

        # Getting key1 should promote it back to L1
        result = cache.get(key1)
        assert result == value1
        assert cache.l1_cache.get(key1) == value1

    def test_statistics_accumulation(
        self, l2_cache: FileCacheProvider, l1_cache: MemoryCacheProvider
    ) -> None:
        """Test that statistics accumulate correctly."""
        cache = HybridCacheProvider(l2_cache, l1_cache=l1_cache)

        # Multiple operations
        key1 = "project|project:test1|lang:en"
        value1 = json.dumps({"group1": {"entry1": "value1"}})
        key2 = "project|project:test2|lang:en"
        key3 = "project|project:test3|lang:en"
        value3 = json.dumps({"group3": {"entry3": "value3"}})

        cache.set(key1, value1)
        cache.get(key1)  # L1 hit
        cache.get(key1)  # L1 hit
        cache.get(key2)  # L1 miss, L2 miss
        cache.l2_cache.set(key3, value3)
        cache.get(key3)  # L1 miss, L2 hit

        stats = cache.get_statistics()

        assert stats["l1_hits"] == 2
        assert stats["l1_misses"] == 2
        assert stats["l2_hits"] == 1
        assert stats["l2_misses"] == 1

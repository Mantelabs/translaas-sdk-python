"""Tests for the memory cache provider."""

import time
from datetime import datetime, timedelta, timezone

from translaas.caching.memory import CacheEntry, MemoryCacheProvider
from translaas.models.protocols import ITranslaasCacheProvider


class TestCacheEntry:
    """Tests for CacheEntry class."""

    def test_cache_entry_creation(self) -> None:
        """Test cache entry creation."""
        entry = CacheEntry("test_value")
        assert entry.value == "test_value"
        assert entry.absolute_expiration is None
        assert entry.sliding_expiration_ms is None
        assert isinstance(entry.last_access, datetime)

    def test_cache_entry_with_absolute_expiration(self) -> None:
        """Test cache entry with absolute expiration."""
        expiration = datetime.now(timezone.utc) + timedelta(seconds=60)
        entry = CacheEntry("test_value", absolute_expiration=expiration)
        assert entry.absolute_expiration == expiration
        assert not entry.is_expired()

    def test_cache_entry_with_sliding_expiration(self) -> None:
        """Test cache entry with sliding expiration."""
        entry = CacheEntry("test_value", sliding_expiration_ms=1000)
        assert entry.sliding_expiration_ms == 1000
        assert not entry.is_expired()

    def test_cache_entry_expired_absolute(self) -> None:
        """Test cache entry expired by absolute expiration."""
        expiration = datetime.now(timezone.utc) - timedelta(seconds=1)
        entry = CacheEntry("test_value", absolute_expiration=expiration)
        assert entry.is_expired()

    def test_cache_entry_expired_sliding(self) -> None:
        """Test cache entry expired by sliding expiration."""
        entry = CacheEntry("test_value", sliding_expiration_ms=100)
        # Wait for expiration
        time.sleep(0.15)
        assert entry.is_expired()

    def test_cache_entry_not_expired_sliding(self) -> None:
        """Test cache entry not expired with sliding expiration."""
        entry = CacheEntry("test_value", sliding_expiration_ms=1000)
        assert not entry.is_expired()
        # Update access time
        entry.update_access_time()
        assert not entry.is_expired()

    def test_update_access_time(self) -> None:
        """Test updating access time."""
        entry = CacheEntry("test_value", sliding_expiration_ms=1000)
        old_access = entry.last_access
        time.sleep(0.01)
        entry.update_access_time()
        assert entry.last_access > old_access


class TestMemoryCacheProvider:
    """Tests for MemoryCacheProvider class."""

    def test_protocol_compliance(self) -> None:
        """Test that MemoryCacheProvider implements ITranslaasCacheProvider."""
        cache: ITranslaasCacheProvider = MemoryCacheProvider()
        assert isinstance(cache, MemoryCacheProvider)

    def test_initialization_default(self) -> None:
        """Test default initialization."""
        cache = MemoryCacheProvider()
        assert cache.max_size is None
        assert cache.enable_statistics is False
        assert cache.hits == 0
        assert cache.misses == 0

    def test_initialization_with_max_size(self) -> None:
        """Test initialization with max size."""
        cache = MemoryCacheProvider(max_size=100)
        assert cache.max_size == 100

    def test_initialization_with_statistics(self) -> None:
        """Test initialization with statistics enabled."""
        cache = MemoryCacheProvider(enable_statistics=True)
        assert cache.enable_statistics is True

    def test_set_and_get(self) -> None:
        """Test basic set and get operations."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self) -> None:
        """Test getting a nonexistent key."""
        cache = MemoryCacheProvider()
        assert cache.get("nonexistent") is None

    def test_set_overwrite(self) -> None:
        """Test overwriting an existing key."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        assert cache.get("key1") == "value2"

    def test_remove(self) -> None:
        """Test removing a key."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1")
        cache.remove("key1")
        assert cache.get("key1") is None

    def test_remove_nonexistent_key(self) -> None:
        """Test removing a nonexistent key."""
        cache = MemoryCacheProvider()
        # Should not raise an error
        cache.remove("nonexistent")

    def test_clear(self) -> None:
        """Test clearing all cache entries."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_absolute_expiration(self) -> None:
        """Test absolute expiration."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1", absolute_expiration_ms=100)
        assert cache.get("key1") == "value1"
        # Wait for expiration
        time.sleep(0.15)
        assert cache.get("key1") is None

    def test_sliding_expiration(self) -> None:
        """Test sliding expiration."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1", sliding_expiration_ms=200)
        assert cache.get("key1") == "value1"
        # Access before expiration extends the expiration
        time.sleep(0.1)
        assert cache.get("key1") == "value1"
        # Wait for expiration after last access (200ms = 0.2s)
        time.sleep(0.25)
        assert cache.get("key1") is None

    def test_sliding_expiration_no_access(self) -> None:
        """Test sliding expiration without access."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1", sliding_expiration_ms=100)
        # Don't access, wait for expiration
        time.sleep(0.15)
        assert cache.get("key1") is None

    def test_both_expiration_types(self) -> None:
        """Test both absolute and sliding expiration."""
        cache = MemoryCacheProvider()
        # Set with both expiration types - absolute should take precedence
        cache.set("key1", "value1", absolute_expiration_ms=100, sliding_expiration_ms=1000)
        assert cache.get("key1") == "value1"
        # Wait for absolute expiration
        time.sleep(0.15)
        assert cache.get("key1") is None

    def test_statistics_enabled(self) -> None:
        """Test cache statistics when enabled."""
        cache = MemoryCacheProvider(enable_statistics=True)
        cache.set("key1", "value1")
        assert cache.hits == 0
        assert cache.misses == 0

        # Hit
        cache.get("key1")
        assert cache.hits == 1
        assert cache.misses == 0

        # Miss
        cache.get("nonexistent")
        assert cache.hits == 1
        assert cache.misses == 1

    def test_statistics_disabled(self) -> None:
        """Test cache statistics when disabled."""
        cache = MemoryCacheProvider(enable_statistics=False)
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("nonexistent")
        # Statistics should not be tracked
        assert cache.hits == 0
        assert cache.misses == 0

    def test_statistics_expired_entry(self) -> None:
        """Test statistics with expired entries."""
        cache = MemoryCacheProvider(enable_statistics=True)
        cache.set("key1", "value1", absolute_expiration_ms=10)
        cache.get("key1")  # Hit
        assert cache.hits == 1
        assert cache.misses == 0

        # Wait for expiration
        time.sleep(0.02)
        cache.get("key1")  # Miss (expired)
        assert cache.hits == 1
        assert cache.misses == 1

    def test_get_statistics(self) -> None:
        """Test getting cache statistics."""
        cache = MemoryCacheProvider(enable_statistics=True, max_size=100)
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_statistics()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["max_size"] == 100
        assert stats["hit_rate"] == 50.0

    def test_get_statistics_no_requests(self) -> None:
        """Test statistics with no requests."""
        cache = MemoryCacheProvider(enable_statistics=True)
        stats = cache.get_statistics()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    def test_lru_eviction(self) -> None:
        """Test LRU eviction when max size is reached."""
        cache = MemoryCacheProvider(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

        # Adding third entry should evict least recently used (key1)
        cache.set("key3", "value3")
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_lru_eviction_access_order(self) -> None:
        """Test LRU eviction respects access order."""
        cache = MemoryCacheProvider(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        # Access key1 to make it more recently used
        cache.get("key1")
        # Adding third entry should evict key2 (least recently used)
        cache.set("key3", "value3")
        assert cache.get("key1") == "value1"  # Not evicted
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"

    def test_lru_eviction_update_existing(self) -> None:
        """Test LRU eviction when updating existing key."""
        cache = MemoryCacheProvider(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        # Update existing key should not evict
        cache.set("key1", "value1_updated")
        assert cache.get("key1") == "value1_updated"
        assert cache.get("key2") == "value2"

    def test_cleanup_expired(self) -> None:
        """Test cleanup of expired entries."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1", absolute_expiration_ms=10)
        cache.set("key2", "value2", absolute_expiration_ms=1000)
        cache.set("key3", "value3", absolute_expiration_ms=10)

        # Wait for some entries to expire
        time.sleep(0.02)

        removed = cache.cleanup_expired()
        assert removed == 2
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") is None

    def test_cleanup_expired_none(self) -> None:
        """Test cleanup when no entries are expired."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        removed = cache.cleanup_expired()
        assert removed == 0
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

    def test_clear_resets_statistics(self) -> None:
        """Test that clear resets statistics."""
        cache = MemoryCacheProvider(enable_statistics=True)
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("nonexistent")
        assert cache.hits == 1
        assert cache.misses == 1

        cache.clear()
        assert cache.hits == 0
        assert cache.misses == 0

    def test_multiple_keys(self) -> None:
        """Test caching multiple keys."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_expiration_removes_from_cache(self) -> None:
        """Test that expired entries are removed from cache."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1", absolute_expiration_ms=10)
        assert "key1" in cache._cache

        time.sleep(0.02)
        cache.get("key1")  # This should remove expired entry
        assert "key1" not in cache._cache

    def test_sliding_expiration_updates_on_access(self) -> None:
        """Test that sliding expiration updates on access."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1", sliding_expiration_ms=200)
        entry1 = cache._cache["key1"]
        first_access = entry1.last_access

        time.sleep(0.1)
        cache.get("key1")  # Access should update last_access
        entry2 = cache._cache["key1"]
        assert entry2.last_access > first_access

    def test_no_expiration(self) -> None:
        """Test entries without expiration."""
        cache = MemoryCacheProvider()
        cache.set("key1", "value1")
        # Entry should never expire
        assert cache.get("key1") == "value1"
        time.sleep(0.1)
        assert cache.get("key1") == "value1"

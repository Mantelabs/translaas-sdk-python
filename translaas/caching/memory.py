"""In-memory cache provider for the Translaas SDK.

This module provides a fast, in-process caching implementation with support
for absolute and sliding expiration, cache statistics, and optional LRU eviction.
"""

from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Dict, List, Optional, Union

from translaas.models.protocols import ITranslaasCacheProvider


class CacheEntry:
    """Represents a cache entry with expiration tracking.

    Attributes:
        value: The cached value.
        absolute_expiration: Optional absolute expiration timestamp.
        sliding_expiration_ms: Optional sliding expiration time in milliseconds.
        last_access: Timestamp of last access for sliding expiration.
    """

    def __init__(
        self,
        value: str,
        absolute_expiration: Optional[datetime] = None,
        sliding_expiration_ms: Optional[int] = None,
    ) -> None:
        """Initialize a cache entry.

        Args:
            value: The value to cache.
            absolute_expiration: Optional absolute expiration timestamp.
            sliding_expiration_ms: Optional sliding expiration time in milliseconds.
        """
        self.value = value
        self.absolute_expiration = absolute_expiration
        self.sliding_expiration_ms = sliding_expiration_ms
        self.last_access = datetime.now(timezone.utc)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """Check if the cache entry is expired.

        Args:
            now: Optional current timestamp. Defaults to UTC now.

        Returns:
            True if the entry is expired, False otherwise.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # Check absolute expiration
        if self.absolute_expiration is not None and now >= self.absolute_expiration:
            return True

        # Check sliding expiration
        if self.sliding_expiration_ms is not None:
            time_since_access = (now - self.last_access).total_seconds() * 1000
            if time_since_access >= self.sliding_expiration_ms:
                return True

        return False

    def update_access_time(self) -> None:
        """Update the last access time for sliding expiration."""
        self.last_access = datetime.now(timezone.utc)


class MemoryCacheProvider(ITranslaasCacheProvider):
    """In-memory cache provider implementing ITranslaasCacheProvider.

    Provides fast, in-process caching with support for:
    - Absolute expiration (time-based)
    - Sliding expiration (access-based)
    - Cache statistics (hit/miss counts)
    - Optional LRU eviction when cache size limit is reached
    - Thread-safe operations

    Attributes:
        max_size: Maximum number of entries in the cache. None for unlimited.
        enable_statistics: Whether to track cache statistics.
        hits: Number of cache hits (if statistics enabled).
        misses: Number of cache misses (if statistics enabled).
    """

    def __init__(
        self,
        max_size: Optional[int] = None,
        enable_statistics: bool = False,
    ) -> None:
        """Initialize the memory cache provider.

        Args:
            max_size: Maximum number of entries in the cache. None for unlimited.
            enable_statistics: Whether to track cache statistics.
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self.max_size = max_size
        self.enable_statistics = enable_statistics
        self.hits = 0
        self.misses = 0
        self._access_order: List[str] = []  # For LRU tracking

    def get(self, key: str) -> Optional[str]:
        """Get a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value if found and not expired, or None if not found or expired.
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                if self.enable_statistics:
                    self.misses += 1
                return None

            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                if self.enable_statistics:
                    self.misses += 1
                return None

            # Update access time for sliding expiration
            if entry.sliding_expiration_ms is not None:
                entry.update_access_time()

            # Update LRU access order
            if self.max_size is not None and key in self._access_order:
                self._access_order.remove(key)
                self._access_order.append(key)

            if self.enable_statistics:
                self.hits += 1

            return entry.value

    def set(
        self,
        key: str,
        value: str,
        absolute_expiration_ms: Optional[int] = None,
        sliding_expiration_ms: Optional[int] = None,
    ) -> None:
        """Set a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
            absolute_expiration_ms: Optional absolute expiration time in milliseconds.
            sliding_expiration_ms: Optional sliding expiration time in milliseconds.
        """
        with self._lock:
            # Calculate absolute expiration timestamp if provided
            absolute_expiration: Optional[datetime] = None
            if absolute_expiration_ms is not None:
                absolute_expiration = datetime.now(timezone.utc) + timedelta(
                    milliseconds=absolute_expiration_ms
                )

            # Check if we need to evict entries (LRU)
            if self.max_size is not None and key not in self._cache:
                if len(self._cache) >= self.max_size:
                    self._evict_lru()

            # Create or update cache entry
            entry = CacheEntry(
                value=value,
                absolute_expiration=absolute_expiration,
                sliding_expiration_ms=sliding_expiration_ms,
            )
            self._cache[key] = entry

            # Update LRU access order
            if self.max_size is not None:
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)

    def remove(self, key: str) -> None:
        """Remove a value from the cache.

        Args:
            key: The cache key to remove.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)

    def clear(self) -> None:
        """Clear all values from the cache."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            if self.enable_statistics:
                self.hits = 0
                self.misses = 0

    def _evict_lru(self) -> None:
        """Evict the least recently used entry from the cache."""
        if not self._access_order:
            return

        # Remove the oldest entry (first in access order)
        oldest_key = self._access_order.pop(0)
        if oldest_key in self._cache:
            del self._cache[oldest_key]

    def get_statistics(self) -> Dict[str, Union[int, float]]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics including hits, misses, and size.
        """
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0

            return {
                "hits": self.hits,
                "misses": self.misses,
                "size": len(self._cache),
                "max_size": self.max_size if self.max_size is not None else -1,
                "hit_rate": round(hit_rate, 2),
            }

    def cleanup_expired(self) -> int:
        """Remove all expired entries from the cache.

        Returns:
            Number of expired entries removed.
        """
        with self._lock:
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
            return len(expired_keys)
